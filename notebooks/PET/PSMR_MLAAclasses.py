#%%
#
# SPDX-License-Identifier: Apache-2.0
#
# Classes implementing the BSREM algorithm in sirf.STIR
#
# Authors:  Kris Thielemans
#
# Copyright 2024 University College London

import numpy
import sirf.STIR as STIR
from sirf.Utilities import examples_data_path
import copy

from cil.optimisation.algorithms import Algorithm 

class __MLAA_step__(Algorithm):
    def __init__(self, acq_data, acq_models_act, initial, const_term, det_effs, prior_strength, **kwargs):
        super(__MLAA_step__, self).__init__(**kwargs) #update_objective_interval=1, max_iteration=None, log_file=None
        self.x = initial.clone() # self.x is always the current estimate, as I understand.
        self.acq_data = [a.clone() for a in acq_data]
        self.const_term = [a.clone() for a in const_term]
        self.det_effs = [a.clone() for a in det_effs]
        self.att_factors = [a.get_uniform_copy(1) for a in det_effs]
        self.num_subsets = len(acq_data)
        self.curr_subset = 0
        self.configured = True # I don't know what implications this has specifically, but fine by me
        self.acq_models_act = acq_models_act
        self.prior_strength = prior_strength
        self.estimates = [self.x.clone()]

    def update(self):
        raise NotImplementedError

    def update_objective(self):
        raise NotImplementedError

    def objective_function(self, x):
        ''' value of objective function summed over all subsets '''
        v = 0
        for s in range(len(self.acq_data)):
            v += self.subset_objective(x, s)
        return v

    def subset_objective(self, x, subset_num):
        ''' value of objective function for one subset '''
        raise NotImplementedError
    
    def get_QP_and_grad(self, x):
        ''' returns QuadraticPrior and its gradient '''
        qp = STIR.QuadraticPrior()
        qp.set_penalisation_factor(self.prior_strength)
        qp.set_up(x)
        qp_grad = qp.get_gradient(x)

        return qp, qp_grad


#%%

class MLEM(__MLAA_step__):
    ''' MLEM step'''
    def __init__(self, acq_data, acq_models_act, initial, const_term, det_effs, prior_strength, **kwargs):
        '''
        '''
        super(MLEM, self).__init__(acq_data, acq_models_act, initial, const_term, det_effs, prior_strength, **kwargs)
        self.quotient = [a.clone() for a in acq_data]
        self.DE_A = [a.multiply(b) for a, b in zip(self.att_factors, self.det_effs)]
        self.const_term_corr = [c.divide(d) for c, d in zip(self.const_term, self.DE_A)]

    def update(self):
        ''' update step '''
        
        forw_of_estimate = self.acq_models_act[self.curr_subset].forward(self.x.clone())
        denom = forw_of_estimate + self.const_term_corr[self.curr_subset]
        curr_quotient_array = self.acq_data[self.curr_subset].divide(denom).as_array()
        self.quotient[self.curr_subset].fill(numpy.nan_to_num(curr_quotient_array))

        backw_of_quot = self.acq_models_act[self.curr_subset].backward(self.quotient[self.curr_subset])
        self.x_update = backw_of_quot.divide(self.subset_sensitivity(self.curr_subset))
        self.x_update.fill(numpy.nan_to_num(self.x_update.as_array()))

        self.x *= self.x_update
        # threshold to non-negative
        self.x.maximum(0, out=self.x)

        self.estimates.append(self.x.clone())
        self.curr_subset = (self.curr_subset + 1) % self.num_subsets

    def subset_sensitivity(self, subset_num):
        return self.acq_models_act[subset_num].backward(self.DE_A[subset_num].clone())

#%%
class MLTR(__MLAA_step__):
    ''' MLTR step'''
    def __init__(self, nonTOF_template, acq_models_att, step_size, **kwargs):
        '''
        '''
        super(MLTR, self).__init__(**kwargs)

    def prior(self, x):
        ''' value of prior function '''
        raise NotImplementedError
    
    def prior_gradient(self, x):
        ''' gradient of prior function '''
        raise NotImplementedError
    

class MLAA(Algorithm):
    def __init__(self, **kwargs):
        super(MLAA, self).__init__(**kwargs)