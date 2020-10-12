# This code computes the mean position of the direct image for each visit
import sys
sys.path.insert(0, './util')
import gaussfitter, ancil

import matplotlib.pyplot as plt
import os
import yaml
from astropy.io import ascii, fits

obs_par_path = "config/obs_par.yaml"
with open(obs_par_path, 'r') as file:
	obs_par = yaml.safe_load(file)

ancil = ancil.AncillaryData(obs_par)

if ancil.direct_image_output ==True:
	f = open('config/xrefyref.txt', 'w')						#opens file to store positions of reference pixels

filetable = ascii.read('config/filelist.txt')

mask_di = filetable['filter/grism'] == ancil.filter
files_di = [ancil.path + '/' + i for i in filetable['filenames'][mask_di].data]
#print(files_di)

#iterate over the direct images
for i, file in enumerate(files_di):
	ima = fits.open(file)
	#print(ima[0].header['OBSTYPE'])

	if (ima[0].header['filter'] == ancil.filter):
		#print("filename", [file])
		LTV1 = ima[1].header['LTV1']					#X offset to get into physical pixels
		LTV2 = ima[1].header['LTV2']					#Y offset to get to physical pixels
		nrow = len(ima[1].data[:,0])
		ncol = len(ima[1].data[0,:])
		t = ima[0].header['expstart']

		dat = ima[1].data[ancil.rmin:ancil.rmax, ancil.cmin:ancil.cmax]				#cuts out stamp around the target star
		err = ima[2].data[ancil.rmin:ancil.rmax, ancil.cmin:ancil.cmax]

		results = gaussfitter.gaussfit(dat, err)
			
		if ancil.diagnostics==True:
			plt.title("Direct image")
			plt.imshow(dat*ima[0].header['exptime'], origin ='lower',vmin=0, vmax=5000)
			plt.plot(results[2], results[3],marker='x', color='orange', markeredgewidth=3., ms=10, label='centroid', linestyle="none")
			plt.legend(numpoints=1)
			plt.colorbar()
			if ancil.direct_image_output == True:
				if not os.path.isdir('config/images/'):
					os.makedirs('config/images/')
				plt.savefig('config/images/{0}.png'.format(i))
			plt.show()
		
		if ancil.direct_image_output==True:
			print(t, results[3]+ancil.rmin-LTV1, results[2]+ancil.cmin-LTV2, file=f)

		#print(t, results[3]+ancil.rmin-LTV1, results[2]+ancil.cmin-LTV2, [file]) 		#fit results
	ima.close()

if ancil.direct_image_output==True:
	f.close()
