import pickle
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
#%% Load Results
res_file_name='2019-01-11 13:16:09.768874.pkl'
result_folder = "Results/Cards/"
with open(result_folder+res_file_name, 'rb') as f:
       [file_names,number_of_nets,mean,var,bench_results] = pickle.load(f)
   
#%% Plots
x = range(3)
distances = ('Euclidean','Normalised Euclidean','Bhattacharya')            
for net in range(number_of_nets):
    fig, ax = plt.subplots()
    plt.bar(x,mean[net]*100,yerr=var[net]*100)
    plt.xticks(x,distances)
    plt.ylim(0,100)
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.set_title(file_names[net][:-4])
    plt.show()