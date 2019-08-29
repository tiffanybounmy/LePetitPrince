# -*- coding: utf-8 -*-
########################
# python cluster.py --login ap259944 --password XxxxX --fmri_data /home/ap259944/inputs/fmri_data/ --design_matrices /home/ap259944/inputs/design_matrices/ --model_name lstm_wikikristina_embedding-size_600_nhid_600_nlayers_1_dropout_02_hidden_first-layer --subject sub-057
########################

from soma_workflow.client import Job, Workflow, Helper, Group, WorkflowController, FileTransfer, SharedResourcePath
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from nilearn.masking import compute_epi_mask # cause warning
from nilearn.image import math_img, mean_img
from nilearn.input_data import MultiNiftiMasker
from nilearn.plotting import plot_glass_brain
import nibabel as nib
import glob
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import argparse



############################
### Functions definition ###
############################

def check_folder(path):
    # Create adequate folders if necessary
    try:
        if not os.path.isdir(path):
            check_folder(os.path.dirname(path))
            os.mkdir(path)
    except:
        pass


def transform_design_matrices(path):
    # Read design matrice csv file and add a column with only 1
    dm = pd.read_csv(path, header=0).values
    # add the constant
    const = np.ones((dm.shape[0], 1))
    dm = np.hstack((dm, const))
    return dm 


def standardization(matrices, model_name, pca_components="300"):
    if (pca_components) and (matrices[0].shape[1] > int(pca_components)):
        print('PCA analysis running...')
        matrices = pca(matrices, model_name, n_components=int(pca_components))
        print('PCA done.')
    else:
        print('Skipping PCA.')
        for index in range(len(matrices)):
            scaler = StandardScaler(with_mean=True, with_std=False)
            scaler.fit(matrices[index])
            matrices[index] = scaler.transform(matrices[index])
    return matrices


def pca(X, data_name, n_components=50):
    """
    See paper:
    General overview of methods of analysis of multi-group datasets
    Aida Eslami, El Mostafa Qannari, Achim Kohler, Stephanie Bougeard
    """
    M = len(X) # number of groups
    # Computing variance-covariance matrix for each group
    cov_matrices = [np.cov(matrix, rowvar=False) for matrix in X]
    R = np.zeros((M, M))
    for i in range(M):
        for k in range(M):
            R[i,k] = np.trace(np.dot(cov_matrices[i], cov_matrices[k]))
    # Computing alphas
    eig_values, eig_vectors = np.linalg.eig(R)
    alphas = eig_vectors[:, np.argmax(eig_values)] # eigen vector associated with the largest eigen value
    # 'Mean' variance-covariance matrix construction
    Vc = np.zeros(cov_matrices[0].shape)
    for index in range(len(cov_matrices)):
        Vc = np.add(Vc, np.dot(alphas[index], cov_matrices[index]))
    # spectral decomposition of Vc
    eig_values_Vc, A = np.linalg.eig(Vc)
    #############################
    eig_pairs = [(np.abs(eig_values_Vc[i]), A[:,i]) for i in range(len(eig_values_Vc))]
    eig_pairs.sort()
    eig_pairs.reverse()
    ##################################################
    projected_matrices = []
    projector = eig_pairs[0][1].reshape(-1, 1)
    for index in range(1, n_components):
        projector = np.hstack((projector, eig_pairs[index][1].reshape(-1, 1)))
    for matrix in X:
        projected_matrices.append(np.dot(matrix, projector))
    # normalizing each matrix
    for index in range(len(projected_matrices)):
        scaler = StandardScaler(with_mean=True, with_std=False)
        scaler.fit(projected_matrices[index])
        projected_matrices[index] = scaler.transform(projected_matrices[index])
    return projected_matrices


def compute_global_masker(files): # [[path, path2], [path3, path4]]
    # return a MultiNiftiMasker object
    masks = [compute_epi_mask(f) for f in files]
    global_mask = math_img('img>0.5', img=mean_img(masks)) # take the average mask and threshold at 0.5
    masker = MultiNiftiMasker(global_mask, detrend=True, standardize=True) # return a object that transforms a 4D barin into a 2D matrix of voxel-time and can do the reverse action
    masker.fit()
    return masker



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""Objective:\nUse cluster nodes to perform the Ridge analysis.""")
    parser.add_argument("--login", type=str, default=None, help="Login to connect to the cluster.")
    parser.add_argument("--password", type=str, default=None, help="Password to connect to the cluster.")
    parser.add_argument("--fmri_data", type=str, default='', help="Path to fMRI data directory.")
    parser.add_argument("--design_matrices", type=str, default='', help="Path to design-matrices directory(for a given model).")
    parser.add_argument("--model_name", type=str, default='', help="Name of the model.")
    parser.add_argument("--subject", type=str, default='sub-057', help="Subject name.")
    parser.add_argument("--pca", type=str, default=None, help="Number of components to keep for the PCA.")

    args = parser.parse_args()


    ###################
    ### Credentials ###
    ###################

    login = args.login 
    password = args.password 


    ######################
    ### Data retrieval ###
    ######################

    inputs_path =  "/home/ap259944/inputs/"  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/inputs/{}".
    scripts_path =  "/home/ap259944/inputs/scripts/"  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/code/utilities"
    fmri_path = "/home/ap259944/inputs/y/{}/".format(args.subject)  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/y/"
    design_matrices_path = "/home/ap259944/inputs/x/"  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/x/"
    derivatives_path = "/home/ap259944/derivatives/{}/".format(args.subject)  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/derivatives/"
    shuffling_path = "/home/ap259944/derivatives/{}/shuffling.npy".format(args.subject)  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/outputs/shuffling.npy"
    r2_path = "/home/ap259944/derivatives/{}/r2/".format(args.subject)  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/r2/"
    distribution_path = "/home/ap259944/derivatives/{}/distribution/".format(args.subject)  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/distribution/"
    yaml_files_path = "/home/ap259944/derivatives/{}/yaml_files/".format(args.subject)  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/yaml_files/"
    output_path = "/home/ap259944/outputs/{}/".format(args.subject)  # "/neurospin/unicog/protocols/IRMf/LePetitPrince_Pallier_2018/LePetitPrince/test/outputs/"

    design_matrices = sorted(glob.glob(os.path.join(args.design_matrices, 'design-matrices_*run*')))
    fmri_runs = sorted(glob.glob(os.path.join(args.fmri_data, 'fMRI_*run*')))


    ####################
    ### Sanity check ###
    ####################

    all_paths = [inputs_path, 
                    scripts_path,
                    fmri_path, 
                    design_matrices_path, 
                    derivatives_path, 
                    r2_path, 
                    distribution_path, 
                    yaml_files_path, 
                    output_path]
    for path in all_paths:
        check_folder(path)



    ###########################
    ### Data transformation ###
    ###########################

    masker = compute_global_masker(list(fmri_runs))
    matrices = [transform_design_matrices(run) for run in design_matrices] # list of design matrices (dataframes) where we added a constant column equal to 1
    x = standardization(matrices, args.model_name, pca_components=args.pca)
    y = [masker.transform(f) for f in fmri_runs] # return a list of 2D matrices with the values of the voxels in the mask: 1 voxel per column

    for index in range(len(y)):
        np.save(os.path.join(fmri_path, 'y_run{}.npy'.format(index+1)), y[index])
        np.save(os.path.join(design_matrices_path, 'x_run{}.npy'.format(index+1)), y[index])

    ##################
    ### Parameters ###
    ##################

    nb_runs = str(len(fmri_runs))
    nb_voxels = str(y[0].shape[1])
    nb_features = str(x[0].shape[1])
    nb_permutations = str(300)
    alpha_list = np.logspace(-3, 3, 2)
    alphas = ','.join([str(alpha) for alpha in alpha_list]) 
    alpha_percentile = str(95)


    ################
    ### Pipeline ###
    ################

    ### FileTransfers
    # FileTransfer creation for input/output files
    raw_data_directory = FileTransfer(is_input=True,
                        client_path=inputs_path,
                        name="raw data directory")
    scripts_directory = FileTransfer(is_input=True,
                        client_path=scripts_path,
                        name="working directory")
    fmri_directory = FileTransfer(is_input=True,
                        client_path=fmri_path,
                        name="fmri data directory")
    design_matrices_directory = FileTransfer(is_input=True,
                        client_path=design_matrices_path,
                        name="design-matrices directory")
    derivatives_directory = FileTransfer(is_input=True,
                        client_path=derivatives_path,
                        name="derivatives directory")
    shuffling_path = FileTransfer(is_input=True,
                        client_path=shuffling_path,
                        name="shuffling file")
    r2_directory = FileTransfer(is_input=True,
                        client_path=r2_path,
                        name="R2 directory")
    distribution_directory = FileTransfer(is_input=True,
                        client_path=distribution_path,
                        name="distribution directory")
    yaml_files_directory = FileTransfer(is_input=True,
                        client_path=yaml_files_path,
                        name="yaml files directory")
    output_directory = FileTransfer(is_input=False,
                        client_path=output_path,
                        name="Outputs directory")


    ### Create the workflow:
    dependencies = []
    jobs = []

    # first job: split the dataset
    job_0 = Job(command=["python", "shuffling_preparation.py", 
                            "--nb_features", nb_features,
                            "--output", output_directory,
                            "--n_permutations", nb_permutations], 
                name="Preparing permutations for significance analysis", 
                referenced_input_files=[scripts_directory],
                referenced_output_files=[output_directory],
                working_directory=scripts_directory)

    jobs.append(job_0)

    # significativity retrieval 
    job_generator = Job(command=["python", "generate_jobs.py", 
                                    "--x", design_matrices_directory, 
                                    "--y", fmri_directory, 
                                    "--alphas", alphas, 
                                    "--output", output_directory, 
                                    "--nb_permutations", nb_permutations, 
                                    "--alpha_percentile", alpha_percentile, 
                                    "--login", login, 
                                    "--password", password], 
                        name="Launch the internal workflow to compute R2 and voxels distribution", 
                        referenced_input_files=[scripts_directory],
                        referenced_output_files=[r2_directory, distribution_directory], 
                        working_directory=scripts_directory)


    # cross-validation on alpha for each split 
    group_cv_alphas = []

    for run in range(1, 1+int(nb_runs)):
        indexes = np.arange(1, 1+int(nb_runs))
        indexes = ','.join([str(i) for i in np.delete(indexes, run-1, 0)]) 
        job = Job(command=["python", "cv_alphas.py", 
                                "--indexes", indexes, 
                                "--x", design_matrices_directory, 
                                "--y", fmri_directory, 
                                "--run", str(run), 
                                "--alphas", alphas, 
                                "--output", yaml_files_directory],  
                name="Alphas CV - split {}".format(run), 
                referenced_input_files=[scripts_directory],
                referenced_output_files=[yaml_files_directory], 
                working_directory=scripts_directory)

        group_cv_alphas.append(job)
        jobs.append(job)
        dependencies.append((job_0, job))
        dependencies.append((job, job_generator))

    jobs.append(job_generator)
                
    # Merging the results and compute significant r2
    job_merge = Job(command=["python", "merge_results.py", 
                                "--input_r2", r2_directory, 
                                "--input_distribution", distribution_directory, 
                                "--output", output_directory, 
                                "--nb_runs", nb_runs, 
                                "--n_permutations", nb_permutations, 
                                "--alpha_percentile", alpha_percentile], 
            name="Merging all the r2 and distribution respectively together.", 
            referenced_input_files=[scripts_directory, r2_directory, distribution_directory],
            referenced_output_files=[output_directory], 
            working_directory=scripts_directory)

    jobs.append(job_merge)
    dependencies.append((job_generator, job_merge))

    # Plotting the maps
    job_final = Job(command=["python", "merge_results.py", 
                                "--output", output_directory, 
                                "--subject", args.subject, 
                                "--pca", args.pca, 
                                "--fmri_data", raw_data_directory], 
                        name="Creating the maps.", 
                        referenced_input_files=[scripts_directory, raw_data_directory, output_directory],
                        referenced_output_files=[output_directory], 
                        working_directory=scripts_directory)
    jobs.append(job_final)
    dependencies.append((job_merge, job_final))

    cv_alphas = Group(elements=group_cv_alphas,
                        name="CV on alphas")

    workflow = Workflow(jobs=jobs,
                    dependencies= dependencies,
                    root_group=[job_0, cv_alphas, job_generator, job_merge, job_final])


    ### Submit the workflow to computing resource (configured in the client-server mode)

    controller = WorkflowController("DSV_cluster_ap259944", login, password) #"DSV_cluster_ap259944", login, password

    workflow_id = controller.submit_workflow(workflow=workflow,
                                            name="Ridge - LPP")

    # You may use the gui or manually transfer the files:
    manual = True
    if manual:
        Helper.transfer_input_files(workflow_id, controller)
        Helper.wait_workflow(workflow_id, controller)
        Helper.transfer_output_files(workflow_id, controller)
        #Helper.delete_all_workflows(controller)

    print("Finished !!!")