# Pipeline for data processing and analysis for Resofact
# Version: 1.2
# Date: 27/11/2016
# Authors: Gard Jenset and Barbara McGillivray

# ----------------------------------
# Import modules:
# ----------------------------------

# For keyword extraction:

from __future__ import division
from topia.termextract import extract  # installed with pypm install topia.termextract
import nltk
import re
import os
import xlrd
import csv
import time

# For semantic clustering:

import math
import numpy as np
import sys
#import os
#import csv
#import time
import semantic_similarity_functions # our module

# For word clouds:

#import os
#import csv
from pytagcloud import create_tag_image, make_tags
from pytagcloud.lang.counter import get_tag_counts

# For bar plots:
import matplotlib.pyplot as plt; plt.rcdefaults()
#import numpy as np
#import os
#import csv

# ---------------------------------------
# Command-line interface:
# ---------------------------------------

# import argparse

# # instantiate a new argument parser
# parser = argparse.ArgumentParser()

# # these are the options for the interface:
# parser.add_argument('--dir', '-d', required=True, help='Full path to directory containing DT HTML output files.')
# parser.add_argument('--weekly', '-w', required=False, action="store_true",
                    # help='''Time period to do report for: Including it will accumulate results
                    # within the same week. Excluding it will accumulate results within the same day.''')
# parser.add_argument('--clean', '-c', required=False,
                    # help='Optional string/regex to clean from start of DT html filename for readability. E.g.: HP_DT_.')

# # parse what's been entered...
# args = parser.parse_args()

# # can now do...
# args.dir
# args.weekly
# args.clean


# Parameters:

test = raw_input("Is this a test? Reply yes or no. Leave empty for yes.")
target_word = raw_input("What is the target word for the survey? Leave empty for pride")  # 'embarassment'#'success'
input_directory = raw_input("What is the path to the input directory where the spread sheet with the responses is? Leave empty for default (...\data\input\Telkom_pride_embarassment\Telkom_pride\). The input spread sheet should have the same name as the target word and the responses should be in the sheet whose name is the target word.")
output_directory = raw_input("What is the path to the output directory where the output files should be saved? Leave empty for default (...\data\output\Telkom_pride_embarassment\Telkom_pride\).")
acronyms_file = raw_input("What is the name of the file containing the acronyms to be excluded from the list of keywords? Leave empty for default (acronyms_list_default.txt). Note that this file should be in the input folder.")
min_similarity_score = raw_input("What is the minimum threshold for the semantic similarity score? Leave empty for 0.8.")
column_number = raw_input("What is the number of the column containing the survey responses in the input spread sheet? Leave empty for 0.")  # 12
n_words = raw_input("What is the maximum number of words to include in the plots? Leave empty for 10.")

# ---------------------------------------
# File and directory names
# ---------------------------------------

#path = os.getcwd().replace("code", "data")
#path_plots = os.getcwd() + r'\plots'
path_plots = os.path.join(output_directory, "plots")
if not os.path.exists(path_plots):
    os.makedirs(path_plots)
   
#path_keyword_freq = path + r'\output\Telkom_pride_embarassment\Telkom_' + target_word
output_file_freq_name = 'Keywords_frequency_' + target_word + "_" + time.strftime("%d%m%Y") + ".csv"
output_word_cloud = 'word_cloud_' + target_word + "_" + time.strftime("%d%m%Y") + ".png"
output_bar_plot = 'bar_plot_' + target_word + "_" + time.strftime("%d%m%Y") + ".png"
output_graph = 'graph_' + target_word + "_" + time.strftime("%d%m%Y") + ".png"
output_file_cluster = 'Keywords_frequency_'+ target_word + "_" + time.strftime("%d%m%Y") + "_clustered.csv"
output_file_keywords_name = 'Responses_keywords_' + target_word + "_" + time.strftime("%d%m%Y") + ".csv"
output_file_sim_name = 'Keywords_frequency_'+ target_word + "_" + time.strftime("%d%m%Y") + "_similarities.csv"

# Default parameters:

if test == "":
    test = "yes"
    
if target_word == "":
    target_word = "pride"
    
if min_similarity_score == "":
    min_similarity_score = 0.8
    
if column_number == "":
    column_number = 0
else:
    column_number = int(column_number)
    
if n_words == "":
    n_words = 10
else:
    n_words = int(n_words)
    
if acronyms_file == "":
    acronyms_file = "acronyms_list_default.txt"
    
if input_directory == "":
    path = os.getcwd().replace("code", "data")
    input_directory = path + r'\input\Telkom_pride_embarassment\Telkom_' + target_word
    
if output_directory == "":
    path = os.getcwd().replace("code", "data")
    output_directory = path + r'\output\Telkom_pride_embarassment\Telkom_' + target_word

assert os.path.exists(input_directory), "I did not find the input directory "+str(input_directory)
assert os.path.exists(output_directory), "I did not find the output directory "+str(output_directory)

# Test files:    
    
if test == "yes":
    output_file_freq_name = output_file_freq_name.replace(".csv", "_test.csv")
    output_word_cloud = output_word_cloud.replace(".csv", "_test.csv")
    output_bar_plot = output_bar_plot.replace(".csv", "_test.csv")
    output_file_cluster = output_file_cluster.replace(".csv", "_test.csv")
    output_file_keywords_name = output_file_keywords_name.replace(".csv", "_test.csv")
    output_file_sim_name = output_file_sim_name.replace(".csv", "_test.csv")
    
# ----------------------------------------------------------
# Exclusion lists
# ----------------------------------------------------------

# List of words to be excluded, for example "e.g."

exclude = ['e. g. ', 'e.g.']

# Words to be excluded as keywords:

exclude_keywords = ['i']

# Exlude names of companies:

if target_word == "pride" or target_word == "embarassment":
    exclude_keywords.append('telkom')
   
# List of acronyms that should not be lemmatized:

assert os.path.exists(os.path.join(input_directory, acronyms_file)), "I did not find the file for acronyms "+str(acronyms_file) + " in " + str(input_directory)
with open(os.path.join(input_directory, acronyms_file)) as acronyms_f:
    acronyms = acronyms_f.read().splitlines()

#acronyms = ['SA', 'HR', 'ICT', 'IT']


# ----------------------------------------------------------
# Extract keywords
# ----------------------------------------------------------

from resofact_topic_extraction_27112016 import extract_keywords

# Extract keywords and write them to a file:

print "Extracting keywords..."
skip = raw_input("Do you want to skip this step? Leave empty if you want this.")
if skip != "yes" and skip != "":
    extract_keywords(test, target_word, input_directory, output_directory, output_file_keywords_name, output_file_freq_name, 
    column_number, acronyms, exclude, exclude_keywords)


# -----------------------------------
# Calculate semantic similarity:
# -----------------------------------

from semantic_similarity_27112016 import calculate_keyword_semantic_similarity

print "Calculating semantic similarity between keywords..."
skip = raw_input("Do you want to skip this step? Leave empty if you want this.")
if skip != "yes" and skip != "":
    calculate_keyword_semantic_similarity(test, target_word, output_directory, output_file_freq_name, output_file_sim_name, min_similarity_score)

# ----------------------------------
# Cluster keywords:
# ----------------------------------

from clustering_27112016 import cluster_keywords

print "Clustering keywords..."
skip = raw_input("Do you want to skip this step? Leave empty if you want this.")
if skip != "yes" and skip != "":
    cluster_keywords(test, target_word, min_similarity_score, output_directory, output_file_freq_name, output_file_sim_name, output_file_cluster)
    
# ---------------------------------
# Create word clouds:
# ---------------------------------

print "Creating word clouds..."

from create_word_cloud_23102016 import create_word_cloud

skip = raw_input("Do you want to skip this step? Leave empty if you want this.")
if skip != "yes" and skip != "":
    # One for clusters (clusters include singletons) and their frequencies:
    #create_word_cloud(path_keyword_freq, output_file_freq_name, path_plots, output_word_cloud)
    create_word_cloud(output_directory, output_file_freq_name, path_plots, output_word_cloud.replace(".png", "_keywords.png"), "keywords")
    create_word_cloud(output_directory, output_file_cluster, path_plots, output_word_cloud.replace(".png", "_clusters.png"), "clusters")
    

# --------------------------------
# Create bar plots:
# --------------------------------

print "Creating bar plots..."

from create_bar_plot_23102016 import create_bar_plot

skip = raw_input("Do you want to skip this step? Leave empty if you want this.")
if skip != "yes" and skip != "":
    create_bar_plot(output_directory, output_file_freq_name, path_plots, output_bar_plot.replace(".png", "_keywords.png"), n_words, "keywords")
    create_bar_plot(output_directory, output_file_cluster, path_plots, output_bar_plot.replace(".png", "_clusters.png"), n_words, "clusters")

    
# --------------------------------
# Create graphs:
# --------------------------------

print "Creating graphs..."

from create_graph_27112016 import create_graph

skip = raw_input("Do you want to skip this step? Leave empty if you want this.")
if skip != "yes" and skip != "":
    create_graph(output_directory, output_file_keywords_name, path_plots, output_graph.replace(".png", "_keywords.png"))
    