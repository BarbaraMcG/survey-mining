# Module for clustering keywords based on their semantic similarity

# Changes from previous version: added singleton clusters

# Read keywords and group them semantically:

# import libraries:

import sys
import os
import csv
import time

# Import functions for semantic similarity:
import semantic_similarity_functions

def cluster_keywords(test, target_word, min_similarity_score, output_directory, kwfreq_file, sim_file, output_file_cluster):
                    
    # Files and paths:

    #path = os.getcwd().replace("code", "data")# get path of current file, then change sub directory from "code" to "data"
    #path_in = path + r'\output\Telkom_pride_embarassment\Telkom_' + target_word
    
    #if test == "yes":
    #    kwfreq_file = kwfreq_file.replace(".csv", "_test.csv")
    #    sim_file = sim_file.replace(".csv", "_test.csv")


    # Read list of keywords:
    keywords = list()
    kw2freq = dict() # maps every keyword to its frequency
    kw2adj = dict() # maps every keyword to the list of its adjectives
    kwadj2freq = dict() # maps every (keyword, adjective) pair to their frequency together
    with open(os.path.join(output_directory, kwfreq_file), 'rb') as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            kw = row[0]
            print "Reading " + kw
            freq = row[1]
            adj = row[2]
            freq_kw_adj = row[3]
            keywords.append(kw)
            kw2freq[kw] = int(freq)
            list_adj_kw = list()
            if freq_kw_adj != "":
                freq_kw_adj = int(freq_kw_adj)
            kwadj2freq[(kw, adj)] = freq_kw_adj
            
            if kw in kw2adj:
                list_adj_kw = kw2adj[kw]
                list_adj_kw.append(adj)
            else:
                list_adj_kw = [adj]
            kw2adj[kw] = list_adj_kw
                
    keywords = sorted(set(keywords))

    # OUTPUT FILE:

    # Write clustered keywords:

    clustered_words = list()

    with open(os.path.join(output_directory, output_file_cluster), 'wb') as outfile:
        output = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        output.writerow(["Keyword cluster", "Keyword cluster name", "Number of responses of keyword cluster",
        "Highest-frequency adjective for cluster"
        #"Number of responses of keyword and adjective
        ])
        #for kw in keywords-set(clustered_words):
        count_keywords = 0
        for kw in keywords:
            count_keywords += 1
            print "Trying to cluster keyword " + kw + "..."
            if kw2freq[kw] > 1 and " " not in kw and kw not in clustered_words and ((test == "yes" and count_keywords <= 10) or (test != "yes")):
                candidate = semantic_similarity_functions.most_similar_word(kw, set(keywords)-set([kw]))
                candidate_kw = candidate[0]
                print "Candidate:" + str(candidate_kw)
                if " " not in candidate and candidate_kw not in clustered_words:
                    sim = candidate[1]
                    print "\tScore: " + str(sim)
                    if sim > min_similarity_score:
                        if len(clustered_words) == 0:
                            clustered_words = [kw]
                        else:
                            clustered_words.append(kw)
                        clustered_words.append(candidate_kw)
                        cluster = kw + "_" + candidate_kw
                        print "\t\tCreated cluster " + cluster + "!"
                        freq_cluster = kw2freq[kw] + kw2freq[candidate_kw]
                        cluster_name = kw
                        if kw2freq[candidate_kw] > kw2freq[kw]:
                            cluster_name = candidate_kw
                        adjs_kw = kw2adj[kw]
                        adjs_candidate = kw2adj[candidate_kw]
                        adj_cluster = ""
                        max_freq_adj = 0
                        
                        for adj in adjs_kw:
                            print "adj1:" + adj
                            if kwadj2freq[(kw, adj)] > max_freq_adj and kwadj2freq[(kw, adj)] > 1 and adj != "":
                                adj_cluster = adj
                                print "yes" + adj_cluster
                        for adj in adjs_candidate:
                            print "adj2:" + adj
                            if kwadj2freq[(candidate_kw, adj)] > max_freq_adj and kwadj2freq[(candidate_kw, adj)] > 1 and ((adj_cluster != "" and kwadj2freq[(candidate_kw, adj)] > kwadj2freq[(kw, adj_cluster)]) or (adj_cluster == "" ))  and adj != "":
                                adj_cluster = adj
                                print "yes" + adj_cluster
                        
                        print cluster, cluster_name, freq_cluster, adj_cluster
                        output.writerow([cluster, cluster_name, freq_cluster, adj_cluster])
                        
                # singleton clusters:
                if kw not in clustered_words:
                    adjs_kw = kw2adj[kw]
                    max_freq_adj = 0
                    adj_cluster = ""
                    
                    for adj in adjs_kw:
                        if kwadj2freq[(kw, adj)] > max_freq_adj and kwadj2freq[(kw, adj)] > 1 and adj != "":
                            adj_cluster = adj

                    output.writerow([kw, kw, kw2freq[kw], adj_cluster])
                        
        #for kw in keywords-set(clustered_words):
        #    print "Non-clustered keyword:" + kw
        #    for adj in kw2adj[kw]:
        #        output.writerow([kw, kw2freq[kw], adj])
