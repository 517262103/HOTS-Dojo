import numpy as np 
from scipy import optimize 
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import time
from Libs.readwriteatis_kaerdat import readATIS_td
from Libs.Time_Surface_generators import Time_Surface_all, Time_Surface_event
from Libs.HOTS_Sparse_Network import HOTS_Sparse_Net, events_from_activations
from scipy.spatial import distance 


import os

os.environ['MKL_NUM_THREADS'] = '1'


# Plotting settings
plt.style.use("dark_background")

#activation_method = "CG"
activation_method = "Exp distance"
#activation_method = "Dot product"

# Network settings
# =============================================================================
# nbasis is a list containing the number of basis used for each layer
# ldim: is a list containing the linear dimension of every base for each layer
# taus: is a list containing the time coefficient used for the time surface creations
#       for each layer, all three lists need to share the same lenght obv.
# shuffle_seed, net_seed : seed used for dataset shuffling and net generation,
#                       if set to 0 the process will be totally random
# 
# =============================================================================

basis_number = [8]
basis_dimension = [[11,11]]
taus = [10000,15000,20000]
# I won't use polarity information because is not informative for the given task
first_layer_polarities = 1
shuffle_seed = 12
net_seed = 2

delay_coeff = 0
       
# Preparing the card dataset 
card_sets = ["cl_","di_","he_", "sp_"]
card_set_starting_number = [60, 17, 77, 75]
number_of_labels = 4
number_of_batch_per_label = 17
dataset = []
labels = []

# The number of cards recordings is not the same for every symbol, thus in order
# to have the same probability if extracting a certain card suit I will have to 
# take max 17 recordings of each symbol as i don't have more clubs recording than that
# Thus learning_set_length+testing_set_length needs to be < number_of_batch_per_label
# i.e. 17

learning_set_length = 7 
testing_set_length = 3
pips_folder_position = "Datasets/pokerDVS/usable/pips/"
# extracting data
for label in range(number_of_labels):
    for batch in range(number_of_batch_per_label):
         file_name = (pips_folder_position+card_sets[label]+np.str(card_set_starting_number[label]+batch)+"_td.dat")
         data = readATIS_td(file_name, orig_at_zero = True, drop_negative_dt = True, verbose = False, events_restriction = [0, np.inf])
         # I won't use polarity information because is not informative for the given task
         dataset.append([data[0].copy(), data[1].copy(), (data[2].copy()**0)-1])
         labels.append(label)



# learning dataset
dataset_learning = []
labels_learning = []
for label in range(number_of_labels):
    for batch in range(learning_set_length):
         dataset_learning.append(dataset[batch + label * number_of_batch_per_label])
         labels_learning.append(labels[batch + label * number_of_batch_per_label])

# testing dataset
dataset_testing = []
labels_testing = []
for label in range(number_of_labels):
    for batch in range(testing_set_length):
        testing_batch = batch + learning_set_length
        dataset_testing.append(dataset[testing_batch + label * number_of_batch_per_label])
        labels_testing.append(labels[testing_batch + label * number_of_batch_per_label])         
         


#Preparing to shuffle
rng = np.random.RandomState()
if(shuffle_seed!=0):         
    rng.seed(shuffle_seed)

#shuffle the dataset and the labels with the same order
combined_data = list(zip(dataset_learning, labels_learning))
rng.shuffle(combined_data)
dataset_learning[:], labels_learning[:] = zip(*combined_data)

#shuffle the dataset and the labels with the same order
combined_data = list(zip(dataset_testing, labels_testing))
rng.shuffle(combined_data)
dataset_testing[:], labels_testing[:] = zip(*combined_data)

# Print an element to check if it's all right
#batch = 9
#tsurface=Time_Surface_all(xdim=35, ydim=35, timestamp=dataset_testing[batch][0][1000], timecoeff=taus[0], dataset=dataset_testing[batch], num_polarities=1, minv=0.1, verbose=True)
#plt.show()

# Generate the network
Net = HOTS_Sparse_Net(basis_number, basis_dimension, taus, first_layer_polarities, delay_coeff, net_seed)

#%% Learning-online-Exp distance and Thresh

start_time = time.time()

sparsity_coeff = [0.7, 0.7, 10000]
learning_rate = [0.0008, 0.0008, 50000]
noise_ratio = [1, 0, 20000]
sensitivity = [6, 8, 50000]

Net.learn_online(dataset=dataset_learning,
                  method=activation_method, base_norm="Thresh",
                  noise_ratio=noise_ratio, sparsity_coeff=sparsity_coeff,
                  sensitivity=sensitivity,
                  learning_rate=learning_rate, verbose=True)

elapsed_time = time.time()-start_time
print("Learning elapsed time : "+str(elapsed_time))

# Taking the steady state values to perform the other tests
sparsity_coeff = sparsity_coeff[1]
learning_rate = learning_rate[1]
noise_ratio = noise_ratio[1]
sensitivity = sensitivity[1]

#%% Learning offline full batch

#start_time = time.time()
#
#sparsity_coeff = 0.8
#learning_rate = 0.2        
#max_steps = 10
#base_norm_coeff = 0.0005
#precision = 0.01
#  
#Net.learn_offline(dataset_learning, sparsity_coeff, learning_rate, max_steps, base_norm_coeff, precision, verbose=False)
#    
#elapsed_time = time.time()-start_time
#print("Learning elapsed time : "+str(elapsed_time))
#noise_ratio = 0
#sensitivity = 0           
    


#%% Classification train

Net.histogram_classification_train(dataset_learning, labels_learning,   
                                   number_of_labels, activation_method, noise_ratio,
                                   sparsity_coeff, sensitivity)
# Plotting results
legend = ("clubs","diamonds","heart", "spades")
Net.plot_histograms(legend)
plt.show()       

#%% Classification test 

test_results, distances, predicted_labels = Net.histogram_classification_test(dataset_testing, labels_testing,
                                                                              number_of_labels, activation_method,
                                                                              noise_ratio, sparsity_coeff, sensitivity)

# Plotting results
print("Euclidean distance recognition rate :             "+str(test_results[0]))
print("Normalsed euclidean distance recognition rate :   "+str(test_results[1]))
print("Bhattachaya distance recognition rate :           "+str(test_results[2]))

Net.plot_histograms(legend, labels=labels_testing)
plt.show()       

#%% Plot Network Evolution

#layer = 0
#sublayer = 0    
#Net.plot_evolution(layer,sublayer)
#plt.show()       

#%% Plot Basis 

layer = 1
sublayer = 0
Net.plot_basis(layer, sublayer)
plt.show()       
        
#%% Reconstruction/Generality Test _single surface_ 
#TODO check it, the reconstruction seems not working well (ofc in the online algorithm it doesn't have any meaning)
#card_n = -1
#surface_n = -3
#layer = 0
#sublayer = 0
#
#plt.figure("Original Surface")
#sns.heatmap(Net.surfaces[layer][sublayer][card_n][surface_n])           
#Net.sublayer_reconstruct(layer, sublayer, Net.surfaces[layer][sublayer][card_n][surface_n],
#                          "Exp distance", noise_ratio, sparsity_coeff, sensitivity)
#Net.activations[layer][sublayer]
#plt.show()       

#%% Complete batch reconstruction error for a single sublayer

#layer = 0
#sublayer = 0
#sparsity_coeff = 0
#timesurfaces = Net.surfaces[layer][sublayer]
#
#Cards_err = Net.batch_sublayer_reconstruct_error(layer, sublayer, timesurfaces,
#                                                 "Exp distance", noise_ratio,
#                                                 sparsity_coeff, sensitivity)
