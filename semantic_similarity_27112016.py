# Module for calculating the semantic similarity between pairs of keywords:

# Read keywords and group them semantically:

# import libraries:

from __future__ import division
import math
import numpy as np
import sys
import os
import csv
import time

from semantic_similarity_functions import word_similarity

def calculate_keyword_semantic_similarity(test, target_word, output_directory, input_file, output_file, min_similarity_score):
 
    # Files and paths:

    #path = os.getcwd().replace("code", "data")# get path of current file, then change sub directory from "code" to "data"
    #path_in = path + r'\output\Telkom_pride_embarassment\Telkom_' + target_word
    
    # read list of keywords:
    count_keywords = 0
    keywords = list()
    with open(os.path.join(output_directory, input_file), 'rb') as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            count_keywords += 1
            kw = row[0]
            # freq = row[1]
            if test == "yes":
                if count_keywords <= 10:
                    keywords.append(kw)
            else:
                keywords.append(kw)

    # write output file:

    # write similarity scores between keyword pairs:
    keywords = sorted(set(keywords))
    word2wordsim = dict() # maps a pair of words to their similarity score

    with open(os.path.join(output_directory, output_file), 'wb') as outfile:
        output = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        for word1 in keywords:
            for word2 in keywords:
                if word1 != word2:
                    print "word1:" + str(word1)
                    print "word2:"+str(word2)
                    sim = word_similarity(word1, word2)
                    print "\tsim:"+str(sim)
                    output.writerow([word1, word2, str(round(sim, 2))])

                    #if sim > min_similarity_score:
                    #    word2wordsim[(word1, word2)] = sim
