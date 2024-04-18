#%%
import os, sys
import sirf.STIR as pet
import re
import matplotlib.pyplot as plt


from partitioner import data_partition
from PSMR_MLAAclasses import MLEM
import copy

pet.AcquisitionData.set_storage_scheme('memory')

#%%

def imshow(image, limits=None, title='', cmap='viridis'):
    """Usage: imshow(image, [min,max], title)"""
    plt.title(title)
    bitmap=plt.imshow(image, cmap=cmap)
    if len(limits)==0:
        limits=[image.min(),image.max()]

    plt.clim(limits[0], limits[1])
    plt.colorbar(shrink=.6)
    plt.axis('off');
    return bitmap

def plot_2d_image(idx,vol,title,clims=None,cmap="viridis"):
    """Customized version of subplot to plot 2D image"""
    plt.subplot(*idx)
    plt.imshow(vol,cmap=cmap)
    if not clims is None:
        plt.clim(clims)
    plt.colorbar(shrink=.6)
    plt.title(title)
    plt.axis("off")

def downsample(image, template):

    img_dims = image.dimensions()
    img_voxs = image.spacing

    temp_dims = template.dimensions()
    temp_voxs = template.voxel_sizes()

    zoom_factor_xy = img_voxs[2] / temp_voxs[2]
    zoom_factor_z = img_voxs[0] / temp_voxs[0]

    zoomed_img = pet.ImageData.zoom_image(image,
                                         zooms=(zoom_factor_z, zoom_factor_xy, zoom_factor_xy),
                                         size=(temp_dims[0], temp_dims[1], temp_dims[2]),
                                         scaling='preserve_values')

    return zoomed_img

#%%
forw_proj_name = 'brain_GE_attenuatedForward.hs'
sino_name_nonTOF = 'GEDis690_maxrd1_sp3_1ring_nonTOF.hs'


#%%
noteb_PET = os.getcwd()
exersices_path = os.path.abspath(os.path.join(noteb_PET, '..', '..'))
SIRF_data_path = os.path.abspath(os.path.join(exersices_path, '..', 'SIRF_data'))
data_path = os.path.join(exersices_path, 'data')

if not os.path.exists(os.path.join(exersices_path, 'working')):
    os.makedirs(os.path.join(exersices_path, 'working'))

#%%
os.chdir(os.path.join(exersices_path, 'working'))

#%%
emission = pet.ImageData(os.path.join(data_path, 'brain_GE_em.hv'))
attenuation = pet.ImageData(os.path.join(data_path, 'brain_GE_att.hv'))

proj_data = pet.AcquisitionData(os.path.join(data_path, forw_proj_name))
template_sino_nonTOF = pet.AcquisitionData(os.path.join(data_path, sino_name_nonTOF))

#%%
#### display data:
plt.figure()
plot_2d_image([1,2,1], emission.as_array()[8, :,:], "Emission image", cmap="hot")
plot_2d_image([1,2,2], attenuation.as_array()[8,:,:], "Attenuation image", cmap="bone")
plt.show()


#### coronal:
plt.figure()
plot_2d_image([1,2,1], emission.as_array()[:, 169,:], "Emission image, coronal", cmap="hot")
plot_2d_image([1,2,2], attenuation.as_array()[:,169,:], "Attenuation image, coronal", cmap="bone")
plt.show()


#%%
#### just test stuff
bg = proj_data.get_uniform_copy(0)
multi_factors = proj_data.get_uniform_copy(1)

#%%
prompts_subsets, \
    background_subsets, \
    multi_factors_subsets,\
    acquisition_models_B, \
    acquisition_models_B_nonTOF, \
    acquisition_models_L = data_partition(proj_data, bg, multi_factors, 4, emission.clone(), template_sino_nonTOF, 'staggered', None )


#%%

for i in range(len(prompts_subsets)):
    plt.figure()
    plot_2d_image([1,3,1], prompts_subsets[i].as_array()[27,47//2,:,:], "Prompts")
    plot_2d_image([1,3,2], background_subsets[i].as_array()[27,47//2,:,:], "Background")
    plot_2d_image([1,3,3], multi_factors_subsets[i].as_array()[27,47//2,:,:], "Multiplicative factors")
    plt.show()

#%%
algo_max2 = MLEM(acq_data=prompts_subsets.copy(), 
            acq_models_act=acquisition_models_B.copy(), 
            initial=emission.get_uniform_copy(1), 
            const_term=background_subsets.copy(), 
            det_effs=multi_factors_subsets.copy(), 
            prior_strength=0.1)

algo_max30 = MLEM(acq_data=prompts_subsets.copy(), 
            acq_models_act=acquisition_models_B.copy(), 
            initial=emission.get_uniform_copy(1), 
            const_term=background_subsets.copy(), 
            det_effs=multi_factors_subsets.copy(), 
            prior_strength=0.1)

algo_nomax = MLEM(acq_data=prompts_subsets.copy(), 
            acq_models_act=acquisition_models_B.copy(), 
            initial=emission.get_uniform_copy(1), 
            const_term=background_subsets.copy(), 
            det_effs=multi_factors_subsets.copy(), 
            prior_strength=0.1)

# %%
for i in range(3):
    algo_nomax.update()
    algo_max30.update()
    algo_max2.update()
    
    ### change order here and find out if you get the same artifacts to see if it's got to do with copying
    ### or with the num of max iterations
    

#%%
plt.figure(figsize=(12,6))
for i in range(len(algo_max2.estimates)):
    plot_2d_image([1,len(algo_max2.estimates),i+1], algo_max2.estimates[i].as_array()[8,:,:], title=f"Iteration {i}")
plt.title("Max 2")
plt.show()

# %%
plt.figure(figsize=(12,6))
for i in range(len(algo_max30.estimates)):
    plot_2d_image([1,len(algo_max30.estimates),i+1], algo_max30.estimates[i].as_array()[8,:,:], title=f"Iteration {i}")
plt.title("Max 30")
plt.show()
# %%
plt.figure(figsize=(12,6))
for i in range(len(algo_nomax.estimates)):
    plot_2d_image([1,len(algo_nomax.estimates),i+1], algo_nomax.estimates[i].as_array()[8,:,:], title=f"Iteration {i}")
plt.title("No max")
plt.show()
# %%

del algo_max2, algo_max30, algo_nomax

#%%
algo_max2 = MLEM(acq_data=prompts_subsets.copy(), 
            acq_models_act=acquisition_models_B.copy(), 
            initial=emission.get_uniform_copy(1), 
            const_term=background_subsets.copy(), 
            det_effs=multi_factors_subsets.copy(), 
            prior_strength=0.1)

#%%

algo_max30 = MLEM(acq_data=prompts_subsets.copy(), 
            acq_models_act=acquisition_models_B.copy(), 
            initial=emission.get_uniform_copy(1), 
            const_term=background_subsets.copy(), 
            det_effs=multi_factors_subsets.copy(), 
            prior_strength=0.1)

#%%
algo_nomax = MLEM(acq_data=prompts_subsets.copy(), 
            acq_models_act=acquisition_models_B.copy(), 
            initial=emission.get_uniform_copy(1), 
            const_term=background_subsets.copy(), 
            det_effs=multi_factors_subsets.copy(), 
            prior_strength=0.1)

# %%
for i in range(3):
    algo_max30.update()
    algo_max2.update()
    algo_nomax.update()
    
    ### change order here and find out if you get the same artifacts to see if it's got to do with copying
    ### or with the num of max iterations
    

#%%
plt.figure(figsize=(12,6))
for i in range(len(algo_max2.estimates)):
    plot_2d_image([1,len(algo_max2.estimates),i+1], algo_max2.estimates[i].as_array()[8,:,:], title=f"Iteration {i}")
plt.title("Max 2")
plt.show()

# %%
plt.figure(figsize=(12,6))
for i in range(len(algo_max30.estimates)):
    plot_2d_image([1,len(algo_max30.estimates),i+1], algo_max30.estimates[i].as_array()[8,:,:], title=f"Iteration {i}")
plt.title("Max 30")
plt.show()
# %%
plt.figure(figsize=(12,6))
for i in range(len(algo_nomax.estimates)):
    plot_2d_image([1,len(algo_nomax.estimates),i+1], algo_nomax.estimates[i].as_array()[8,:,:], title=f"Iteration {i}")
plt.title("No max")
plt.show()
# %%
