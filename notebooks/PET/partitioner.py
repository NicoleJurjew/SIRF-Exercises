#
# SPDX-License-Identifier: Apache-2.0
#
# Functions for partitioning sirf.STIR.ACquisitionData in subsets
#
# Authors: Margaret Duff and Kris Thielemans
#
# Copyright 2024 Science Technology Facilities Council
# Copyright 2024 University College London

import numpy
import math 
import sys
import sirf.STIR as pet

sys.path.insert(0, 'functions')
sys.path.insert(0, 'tools')


#%%

def data_partition( prompts, background, multiplicative_factors, num_batches, initial_image, nonTOF_template = None , mode="sequential", seed=None): 
        '''Partition the data into ``num_batches`` batches using the specified ``mode``.
        

        The modes are
        
        1. ``sequential`` - The data will be partitioned into ``num_batches`` batches of sequential indices.
        
        2. ``staggered`` - The data will be partitioned into ``num_batches`` batches of sequential indices, with stride equal to ``num_batches``.
        
        3. ``random_permutation`` - The data will be partitioned into ``num_batches`` batches of random indices.

        Parameters
        ----------
        prompts: 
            Noisy data
        background:
            background factors
        multiplicative_factors:
            bin efficiency      
        num_batches : int
            The number of batches to partition the data into.
        initial_image: ImageData
            If passed, the returned objectives and acquisition models will be set-up. If not, you will have to do this yourself.
        nonTOF_template: optional
            If called with TOF prompts, non-TOF template must be passed to create a correct acquisition model L
        mode : str
            The mode to use for partitioning. Must be one of "sequential", "staggered" or "random_permutation".
        seed : int, optional
            The seed to use for the random permutation. If not specified, the random number
            generator will not be seeded.



        Returns
        -------
        List of data subsets 
        
        List of acquisition models B
        
        List of acquisition models L

        Example
        -------
        
        Partitioning a list of ints [0, 1, 2, 3, 4, 5, 6, 7, 8] into 4 batches will return:
    
        1. [[0, 1, 2], [3, 4], [5, 6], [7, 8]] with ``sequential``
        2. [[0, 4, 8], [1, 5], [2, 6], [3, 7]] with ``staggered``
        3. [[8, 2, 6], [7, 1], [0, 4], [3, 5]] with ``random_permutation`` and seed 1

        '''

        if prompts.dimensions()[0] != 1 and not nonTOF_template:
            raise ValueError('If called with TOF prompts, non-TOF template must be passed to create a correct acquisition model L and B(nonTOF)!.')

        if mode == "sequential":
            return _partition_deterministic( prompts, background, multiplicative_factors, num_batches, stagger=False, initial_image=initial_image, nonTOF_templ = nonTOF_template)
        elif mode == "staggered":
            return _partition_deterministic( prompts, background, multiplicative_factors, num_batches, stagger=True, initial_image=initial_image, nonTOF_templ = nonTOF_template)
        elif mode == "random_permutation":
            return _partition_random_permutation( prompts, background, multiplicative_factors, num_batches, seed=seed, initial_image=initial_image)
        else:
            raise ValueError('Unknown partition mode {}'.format(mode))


def get_acq_model_no_att(image, sino):
    ''' we are creating an acquisition model without attenuation, because our attenuation factors change at every
    iteration.'''

    try:
        acq_model = pet.AcquisitionModelUsingParallelproj()
    except AttributeError:
        acq_model = pet.AcquisitionModelUsingRayTracingMatrix()
        acq_model.set_num_tangential_LORs(5)

    acq_model.set_up(sino, image)

    return acq_model

def get_acq_model_for_mumap(mu_map, sino_non_TOF):
    ''' the simple "line integral" acquisition model needs to take the voxel size into account
            '''
    x_voxel_size = mu_map.spacing[2]

    asm = pet.AcquisitionSensitivityModel(sino_non_TOF.get_uniform_copy(x_voxel_size/10))
    asm.set_up(sino_non_TOF)

    try:
        acq_model_for_mumap = pet.AcquisitionModelUsingParallelproj()
    except AttributeError:
        acq_model_for_mumap = pet.AcquisitionModelUsingRayTracingMatrix()
        acq_model_for_mumap.set_num_tangential_LORs(5)
        
    acq_model_for_mumap.set_acquisition_sensitivity(asm)
    acq_model_for_mumap.set_up(sino_non_TOF, mu_map)

    return acq_model_for_mumap

def _partition_deterministic( prompts, background, multiplicative_factors, num_batches, stagger=False, indices=None, initial_image=None, nonTOF_templ = None):
    '''Partition the data into ``num_batches`` batches.
    
    Parameters
    ----------
    prompts: 
            Noisy data
    background:
        background factors
    multiplicative_factors:
        bin efficiency   
    num_batches : int
        The number of batches to partition the data into.
    stagger : bool, optional
        If ``True``, the batches will be staggered. Default is ``False``.
    indices : list of int, optional
        The indices to partition. If not specified, the indices will be generated from the number of projections.
    initial_image: Optional,  ImageData
        If passed, the returned objectives and acquisition models will be set-up. If not, they will be passed uninitialised
    projector: Optional
        If not specified, parallelproj will be used. If specified (anything other than PP), the ray-tracing matrix will be used.
    tof: Optional
        default is false, if true, the acquisition model B will be set up for TOF
    nonTOF_template: Optional


        
    Returns
    -------
    List of prompts subsets

    List of multiplicative factors subsets

    List of background subsets
    
    List of acquisition models B

    List of acquisition models L
    
    
    '''
    acquisition_models_B=[]
    acquisition_models_B_nonTOF=[]
    acquisition_models_L=[]
    prompts_subsets=[]
    multiplicative_factors_subsets = []
    const_subsets = []
    
    views=prompts.dimensions()[2]
    if indices is None:
        indices = list(range(views))
    partition_indices = _partition_indices(num_batches, indices, stagger)
  
    for i in range(len(partition_indices)):
        prompts_subset = prompts.get_subset(partition_indices[i])
        background_subset = background.get_subset(partition_indices[i])
        multiplicative_factors_subset = multiplicative_factors.get_subset(partition_indices[i])
        if nonTOF_templ: nonTOF_subset = nonTOF_templ.get_subset(partition_indices[i])
        
        ##### get acquisition models here!!
        
        acquisition_model_B = get_acq_model_no_att(initial_image, prompts_subset)

        if nonTOF_templ:
            acquisition_model_L = get_acq_model_for_mumap(initial_image, nonTOF_subset)
            acquisition_model_B_nonTOF = get_acq_model_no_att(initial_image, nonTOF_subset)
        else:
            acquisition_model_L = get_acq_model_for_mumap(initial_image, prompts_subset)
            acquisition_model_B_nonTOF = acquisition_model_B

        prompts_subsets.append(prompts_subset)
        multiplicative_factors_subsets.append(multiplicative_factors_subset)
        const_subsets.append(background_subset)
        acquisition_models_B.append(acquisition_model_B)
        acquisition_models_B_nonTOF.append(acquisition_model_B_nonTOF)
        acquisition_models_L.append(acquisition_model_L)


    return prompts_subsets, const_subsets, multiplicative_factors_subsets , acquisition_models_B, acquisition_models_B_nonTOF, acquisition_models_L


def _partition_random_permutation( prompts, background, multiplicative_factor, num_batches, seed=None, initial_image=None):
    '''Partition the data into ``num_batches`` batches using a random permutation.

    Parameters
    ----------
    prompts: 
            Noisy data
    background:
        background factors
    multiplicative_factors:
        bin efficiency 
    views:
        The measurement views 
    num_batches : int
        The number of batches to partition the data into.
    seed : int, optional
        The seed to use for the random permutation. If not specified, the random number generator
        will not be seeded.
    initial_image: Optional,  AquisitionData
            If passed, the returned objectives and acquisition models will be set-up. If not, they will be passed uninitialised
            
    Returns
    -------
    List of data subsets 
    
    List of acquisition models 
    
    List of objective functions
    
    '''
    views=prompts.dimensions()[2]
    if seed is not None:
        numpy.random.seed(seed)
    
    indices = numpy.arange(views)
    numpy.random.shuffle(indices)

    indices = list(indices)            
    
    return _partition_deterministic(prompts, background, multiplicative_factor,views, num_batches, stagger=False, indices=indices, initial_image=initial_image)

def _partition_indices(num_batches, indices, stagger=False):
        """Partition a list of indices into num_batches of indices.
        
        Parameters
        ----------
        num_batches : int
            The number of batches to partition the indices into.
        indices : list of int, int
            The indices to partition. If passed a list, this list will be partitioned in ``num_batches``
            partitions. If passed an int the indices will be generated automatically using ``range(indices)``.
        stagger : bool, default False
            If True, the indices will be staggered across the batches.

        Returns
        --------
        list of list of int
            A list of batches of indices.
        """
        # Partition the indices into batches.
        if isinstance(indices, int):
            indices = list(range(indices))

        num_indices = len(indices)
        # sanity check
        if num_indices < num_batches:
            raise ValueError(
                'The number of batches must be less than or equal to the number of indices.'
            )

        if stagger:
            batches = [indices[i::num_batches] for i in range(num_batches)]

        else:
            # we split the indices with floor(N/M)+1 indices in N%M groups
            # and floor(N/M) indices in the remaining M - N%M groups.

            # rename num_indices to N for brevity
            N = num_indices
            # rename num_batches to M for brevity
            M = num_batches
            batches = [
                indices[j:j + math.floor(N / M) + 1] for j in range(N % M)
            ]
            offset = N % M * (math.floor(N / M) + 1)
            for i in range(M - N % M):
                start = offset + i * math.floor(N / M)
                end = start + math.floor(N / M)
                batches.append(indices[start:end])

        return batches