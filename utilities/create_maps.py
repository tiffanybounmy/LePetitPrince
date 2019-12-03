#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import numpy as np
import glob
import yaml

from nilearn.masking import compute_epi_mask
from nilearn.image import math_img, mean_img
from nilearn.input_data import MultiNiftiMasker
from nilearn.plotting import plot_glass_brain, plot_img
import nibabel as nib

import matplotlib.pyplot as plt
plt.switch_backend('agg')


subjects = ['sub-057', 'sub-058', 'sub-059', 'sub-061', 'sub-062', 'sub-063', 'sub-064', 'sub-065', 
            'sub-066', 'sub-067', 'sub-068', 'sub-069', 'sub-070', 'sub-072', 'sub-073', 'sub-074', 
            'sub-075', 'sub-076', 'sub-077', 'sub-078', 'sub-079', 'sub-080', 'sub-081', 'sub-082', 
            'sub-083', 'sub-084', 'sub-086', 'sub-087', 'sub-088', 'sub-089', 'sub-091', 'sub-092', 
            'sub-093', 'sub-094', 'sub-095', 'sub-096', 'sub-097', 'sub-098', 'sub-099', 'sub-100', 
            'sub-101', 'sub-103', 'sub-104', 'sub-105', 'sub-106', 'sub-108', 'sub-109', 'sub-110', 
            'sub-113', 'sub-114', 'sub-115']


def check_folder(path):
    # Create adequate folders if necessary
    try:
        if not os.path.isdir(path):
            check_folder(os.path.dirname(path))
            os.mkdir(path)
    except:
        pass


def compute_global_masker(files, smoothing_fwhm=None): # [[path, path2], [path3, path4]]
    # return a MultiNiftiMasker object
    masks = [compute_epi_mask(f) for f in files]
    global_mask = math_img('img>0.5', img=mean_img(masks)) # take the average mask and threshold at 0.5
    masker = MultiNiftiMasker(global_mask, detrend=True, standardize=True, smoothing_fwhm=smoothing_fwhm) # return a object that transforms a 4D barin into a 2D matrix of voxel-time and can do the reverse action
    masker.fit()
    return masker


def create_maps(masker, masker_smoothed, distribution, distribution_name, subject, output_parent_folder, vmax=None, pca='', voxel_wise=False, not_glass_brain=False):
    model = os.path.basename(output_parent_folder)
    language = os.path.basename(os.path.dirname(output_parent_folder))
    data_type = os.path.basename(os.path.dirname(os.path.dirname(output_parent_folder)))

    img = masker.inverse_transform(distribution)
    img_smoothed = masker_smoothed.inverse_transform(distribution)

    pca = 'pca_' + str(pca) if (pca!='') else 'no_pca'
    voxel_wise = 'voxel_wise' if voxel_wise else 'not_voxel_wise'
    
    path2output_raw = os.path.join(output_parent_folder, "{0}_{1}_{2}_{3}_{4}_{5}_{6}".format(data_type, language, model, distribution_name, pca, voxel_wise, subject)+'.nii.gz')
    path2output_png = os.path.join(output_parent_folder, "{0}_{1}_{2}_{3}_{4}_{5}_{6}".format(data_type, language, model, distribution_name, pca, voxel_wise, subject)+'.png')
    path2output_hist_png = os.path.join(output_parent_folder, "hist_{0}_{1}_{2}_{3}_{4}_{5}_{6}".format(data_type, language, model, distribution_name, pca, voxel_wise, subject)+'.png')

    nib.save(img, path2output_raw)

    plt.hist(distribution[~np.isnan(distribution)], bins=50)
    plt.savefig(path2output_hist_png)
    plt.close()

    if not_glass_brain:
        display = plot_img(img_smoothed, colorbar=True, black_bg=True, cut_coords=(-48, 24, -10))
        display.savefig(path2output_png)
        display.close()
    else:
        display = plot_glass_brain(img_smoothed, display_mode='lzry', colorbar=True, black_bg=True, vmax=vmax, plot_abs=False)
        display.savefig(path2output_png)
        display.close()

def write(path, text):
    with open(path, 'a+') as f:
        f.write(text)
        f.write('\n')



if __name__ =='__main__':

    parser = argparse.ArgumentParser(description="""Objective:\nGenerate password from key (and optionnally the login).""")
    parser.add_argument("--input", type=str, default=None, help="Path to input folders.")
    parser.add_argument("--subject", type=str, default='sub-057', help="Subject name.")
    parser.add_argument("--parameters", type=str, default='', help="Path to the yaml file containing the models names and column indexes.")
    parser.add_argument("--pca", type=str, default=None, help="Number of components to keep for the PCA.")
    parser.add_argument("--fmri_data", type=str, default='', help="Path to fMRI data directory.")
    parser.add_argument("--compute_distribution", type=bool, action="store_true", default=False, help="allow the computation of predictions over the randomly shuffled columns of the test set")

    args = parser.parse_args()

    with open(args.parameters, 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            quit()
    
    fmri_runs = {}
    language = 'english'
    inputs_path = "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/"
    compute = args.compute_distribution
    for subject in subjects:
        fmri_path = os.path.join(inputs_path, "data/fMRI/{language}/{subject}/func/")
        check_folder(fmri_path)
        fmri_runs[subject] = sorted(glob.glob(os.path.join(fmri_path.format(language=language, subject=subject), 'fMRI_*run*')))
    masker = compute_global_masker(list(fmri_runs.values()))
    masker_smoothed = compute_global_masker(list(fmri_runs.values()), smoothing_fwhm=5)

    for model in parameters['models']:
        model_name = model['name'] # model['name']=='' if we study the model as a whole

        # defining paths
        output = os.path.join(args.input, model_name, 'outputs')
        output_parent_folder = os.path.join(output, 'maps')
        alphas = np.mean(np.load(os.path.join(output, 'voxel2alpha.npy')), axis=0)

        r2 = np.load(os.path.join(output, 'r2.npy'))
        pearson_corr = np.load(os.path.join(output, 'pearson_corr.npy'))
        
        if compute:
            r2_significant_with_pvalues = np.load(os.path.join(output, 'r2_significant_with_pvalues.npy'))
            pearson_corr_significant_with_pvalues = np.load(os.path.join(output, 'pearson_corr_significant_with_pvalues.npy'))

            z_values_r2 = np.load(os.path.join(output, 'z_values_r2.npy'))
            z_values_pearson_corr = np.load(os.path.join(output, 'z_values_pearson_corr.npy'))

            p_values_r2 = np.load(os.path.join(output, 'p_values_r2.npy'))
            p_values_pearson_corr = np.load(os.path.join(output, 'p_values_pearson_corr.npy'))

        pca = int(args.pca) if type(args.pca)==str else None

        check_folder(output_parent_folder)
        
        # creating maps
        create_maps(masker, masker_smoothed, alphas, 'alphas', args.subject, output_parent_folder, pca=pca, vmax=10000) # alphas # argument deleted: , vmax=5e3

        create_maps(masker, masker_smoothed, r2, 'r2', args.subject, output_parent_folder, pca=pca,  voxel_wise=True) # r2 
        create_maps(masker, masker_smoothed, pearson_corr, 'pearson_corr', args.subject, output_parent_folder, pca=pca,  voxel_wise=True) # pearson_corr 
        
        if compute:
            create_maps(masker, masker_smoothed, r2_significant_with_pvalues, 'significant_r2_with_pvalues', args.subject, output_parent_folder, pca=pca, voxel_wise=True) # r2_significant
            create_maps(masker, masker_smoothed, pearson_corr_significant_with_pvalues, 'significant_pearson_corr_with_pvalues', args.subject, output_parent_folder, pca=pca, voxel_wise=True) # pearson_corr_significant

            create_maps(masker, masker_smoothed, p_values_r2, 'p_values_r2', args.subject, output_parent_folder, pca=pca, voxel_wise=True)
            create_maps(masker, masker_smoothed, p_values_pearson_corr, 'p_values_pearson_corr', args.subject, output_parent_folder, pca=pca, voxel_wise=True)

            create_maps(masker, masker_smoothed, z_values_r2, 'z_values_r2', args.subject, output_parent_folder, pca=pca, voxel_wise=True)
            create_maps(masker, masker_smoothed, z_values_pearson_corr, 'z_values_pearson_corr', args.subject, output_parent_folder, pca=pca, voxel_wise=True)
