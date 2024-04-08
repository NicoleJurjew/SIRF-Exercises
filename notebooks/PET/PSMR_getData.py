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
thorax_path = os.path.join(SIRF_data_path, 'examples/PET/thorax_single_slice')
brain_path = os.path.join(SIRF_data_path, 'examples/PET/brain')

if not os.path.exists(os.path.join(exersices_path, 'data')):
    os.makedirs(os.path.join(exersices_path, 'data'))

#%%
os.chdir(os.path.join(exersices_path, 'data'))

#%%

def_sino = pet.AcquisitionData('GE Discovery 690')
def_sino.fill(1)
def_sino.write('GEDis690_def.hs')

#%%
sino_maxrd1 = pet.AcquisitionData('GE Discovery 690', span = 3, max_ring_diff=1)
sino_maxrd1.fill(1)
sino_maxrd1.write('GEDis690_maxrd1_sp3.hs')

##### note: this image has 47 slices, even if I create the image from the "1 ring only" sinogram
def_img = def_sino.create_uniform_image(1)
def_img.write('GEDis690_maxrd1_sp3_img.hv')

#%%
### now: save header-file :
### change line 32: Number of rings := 24 to 1
### change name of data file := GEDis690_maxrd1_sp3.s to "/dev/zero"
def change_filename_in_interfile_header(header_filename, data_filename, new_header_filename):
    with open(header_filename) as f:
        data = f.read()
    poss = re.search(r'name of data file\s*:=[^\n]*', data).span()
    data = data.replace(data[poss[0]:poss[1]], \
        'name of data file:={}'.format(data_filename))
    with open(new_header_filename, 'w') as f2:
        f2.write(data)

change_filename_in_interfile_header('GEDis690_maxrd1_sp3.hs', '/dev/zero', 'GEDis690_1ring.hs')


#%%
def change_number_of_rings(header_filename_old, header_filename_new, number_of_rings):
    with open(header_filename_old) as f:
        data = f.read()
    poss = re.search(r'Number of rings\s*:=[^\n]*', data).span()
    data = data.replace(data[poss[0]:poss[1]], \
        'Number of rings:={}'.format(number_of_rings))
    with open(header_filename_new, 'w') as f2:
        f2.write(data)

change_number_of_rings('GEDis690_1ring.hs', 'GEDis690_1ring.hs', 1)

#%%
def change_tof_settings(sino_path, sino_path_new, time_res, tof_bins_no_new, tof_bins_size, tof_mashing_factor, tof_bins_max):

    with open(sino_path) as f:
        data = f.read()

    if tof_bins_max % tof_mashing_factor == 0:
        matrix_tof_size = tof_bins_no_new//tof_mashing_factor
    else:
        print('Combination of no of bins and TOF-mashing factor is not supported!')
        sys.exit()

    data = data.replace('%TOF mashing factor := [0-9]{1,3}', \
        '%TOF mashing factor := {}'.format(tof_mashing_factor))

    pos_tof_bins_no = re.search('Maximum number of \(unmashed\) TOF time bins\s*:=\s*[0-9]{1,3}', data).span()
    data = data.replace(data[pos_tof_bins_no[0]:pos_tof_bins_no[1]], \
        'Maximum number of (unmashed) TOF time bins :={}'.format(tof_bins_no_new))

    pos_tof_bins_size = re.search('Size of unmashed TOF time bins \(ps\)\s*:=\s*[0-9]{1,3}', data).span()
    data = data.replace(data[pos_tof_bins_size[0]:pos_tof_bins_size[1]], \
        'Size of timing bin (ps) :={}'.format(tof_bins_size))

    pos_time_res = re.search('TOF timing resolution \(ps\)\s*:=\s*[0-9]{1,3}', data).span()
    data = data.replace(data[pos_time_res[0]:pos_time_res[1]], \
        'TOF timing resolution (ps):={}'.format(time_res))

    with open(sino_path_new, 'w') as f2:
        f2.write(data)


#%%

sino_path = 'GEDis690_1ring.hs'
sino_path_new = 'GEDis690_1ring_test.hs'
time_res = 550
tof_bins_max = 55
tof_bins_size = 5*89
tof_mashing_factor = 5
tof_bins_no_new = tof_bins_max//tof_mashing_factor

#%%
change_tof_settings(sino_path, sino_path_new, time_res, tof_bins_no_new, tof_bins_size, tof_mashing_factor, tof_bins_max)

# %%
############### test if that works
test_sino = pet.AcquisitionData('GEDis690_1ring.hs')
img_GE690 = pet.ImageData(test_sino)

# am = pet.AcquisitionModelUsingParallelproj()
# am.set_up(test_sino, img_GE690)
# am.forward(img_GE690.clone())

#%%
th_em_slice = pet.ImageData(os.path.join(thorax_path, 'emission.hv'))
th_att_slice = pet.ImageData(os.path.join(thorax_path, 'attenuation.hv'))

br_em_slice = pet.ImageData(os.path.join(brain_path, 'emission.hv'))
br_att_slice = pet.ImageData(os.path.join(brain_path, 'attenuation.hv'))

print('emission dimensions:', th_em_slice.dimensions())
print('emission voxel sizes:', th_em_slice.voxel_sizes())
print('attenuation dimensions:', th_att_slice.dimensions())
print('attenuation voxel sizes:', th_att_slice.voxel_sizes())
print('brain emission dimensions:', br_em_slice.dimensions())
print('brain emission voxel sizes:', br_em_slice.voxel_sizes())
print('brain attenuation dimensions:', br_att_slice.dimensions())
print('brain attenuation voxel sizes:', br_att_slice.voxel_sizes())

print('GE 690 dimensions:', img_GE690.dimensions())
print('GE 690 voxel sizes:', img_GE690.voxel_sizes())

#%%
plt.figure()
plot_2d_image([1,2,1], th_em_slice.as_array()[0, :,:], "Emission image", cmap="hot")
plot_2d_image([1,2,2], th_att_slice.as_array()[0,:,:], "Attenuation image", cmap="bone")
plt.show()

plt.figure()
plot_2d_image([1,2,1], br_em_slice.as_array()[0, :,:], "Emission image", cmap="hot")
plot_2d_image([1,2,2], br_att_slice.as_array()[0,:,:], "Attenuation image", cmap="bone")
plt.show()

#### coronal:
plt.figure()
plot_2d_image([1,2,1], br_em_slice.as_array()[:, 169,:], "Emission image", cmap="hot")
plot_2d_image([1,2,2], br_att_slice.as_array()[:,169,:], "Attenuation image", cmap="bone")
plt.show()
#%%
# get the brain-data in GEDis690 format
br_GE_em = downsample(br_em_slice, img_GE690)
br_GE_att = downsample(br_att_slice, img_GE690)

plt.figure()
plot_2d_image([1,2,1], br_GE_em.as_array()[8, :,:], "Emission image", cmap="hot")
plot_2d_image([1,2,2], br_GE_att.as_array()[8,:,:], "Attenuation image", cmap="bone")
plt.show()


#### coronal:
plt.figure()
plot_2d_image([1,2,1], br_GE_em.as_array()[:, 169,:], "Emission image", cmap="hot")
plot_2d_image([1,2,2], br_GE_att.as_array()[:,169,:], "Attenuation image", cmap="bone")
plt.show()

#%%
br_GE_em.write('brain_GE_em.hv')
br_GE_att.write('brain_GE_att.hv')


# %%
# Remove all files starting with tmp_
file_list = [f for f in os.listdir('.') if f.startswith('tmp_')]
for f in file_list:
    os.remove(f)
# %%
