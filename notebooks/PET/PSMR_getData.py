import os, sys
import sirf.STIR as pet
import re

#%%
os.chdir('/home/nicole/storage/SIRF-Exercises/data')

#%%

# def_sino = pet.AcquisitionData('GE Discovery 690')
# def_sino.fill(1)
# def_sino.write('GEDis690_def.hs')

# #%%
# def_img = def_sino.create_uniform_image(1)
# def_img.write('GEDis690_def_img.hv')


# #%%
# sino_maxrd1 = pet.AcquisitionData('GE Discovery 690', span = 3, max_ring_diff=1)
# sino_maxrd1.fill(1)
# sino_maxrd1.write('GEDis690_maxrd1_sp3.hs')
# sino_maxrd1 = pet.AcquisitionData('GEDis690_maxrd1_sp3.hs')

# %%
#### now: save header-file :
#### change line 32: Number of rings := 24 to 1
#### change name of data file := GEDis690_maxrd1_sp3.s to "/dev/zero"
def change_filename_in_interfile_header(header_filename, data_filename, new_header_filename):
    with open(header_filename) as f:
        data = f.read()
    poss = re.search(r'name of data file\s*:=[^\n]*', data).span()
    data = data.replace(data[poss[0]:poss[1]], \
        'name of data file:={}'.format(data_filename))
    with open(new_header_filename, 'w') as f2:
        f2.write(data)

change_filename_in_interfile_header('GEDis690_maxrd1_sp3.hs', '/dev/zero', 'GEDis690_1ring.hs')


# %%
def change_number_of_rings(header_filename_old, header_filename_new, number_of_rings):
    with open(header_filename_old) as f:
        data = f.read()
    poss = re.search(r'Number of rings\s*:=[^\n]*', data).span()
    data = data.replace(data[poss[0]:poss[1]], \
        'Number of rings:={}'.format(number_of_rings))
    with open(header_filename_new, 'w') as f2:
        f2.write(data)

change_number_of_rings('GEDis690_1ring.hs', 'GEDis690_1ring.hs', 1)
# %%
test_sino = pet.AcquisitionData('GEDis690_1ring.hs')
# %%
