#%%
import os, sys
import sirf.STIR as pet
import re
import matplotlib.pyplot as plt

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

template_sinogram = pet.AcquisitionData(os.path.join(data_path, 'GEDis690_1ring.hs'))

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

