# Module for creating bar plots from responses and their keywords

import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
import os
import csv

def create_bar_plot(input_path, input_file, output_path, output_file, n_words, type):
    
    input_words = []
    input_counts = []
    word_col = 0
    freq_col = 1
    if type == "clusters":
        word_col = 1
        freq_col = 2
    kw = ""
    freq = ""
    
    with open(os.path.join(input_path, input_file), 'rb') as csv_file:
        res_reader = csv.reader(csv_file, delimiter=',')
        my_count = 0
        prev_kw = ''
        for row in res_reader:
            kw = row[word_col]
            freq = row[freq_col]
            if my_count > 0:
                if row[word_col] != prev_kw:
                    try:
                        input_words.append(kw)
                        input_counts.append(int(freq))
                        prev_kw = kw
                    except IndexError:
                        pass
                        #print ", ".join(row)
                #else:
                #    print 'Repeated:', kw
            #else:
            #    print ", ".join(row)
            my_count += 1

    words = np.array(input_words)
    counts = np.array(input_counts)
    n = len(words)
    ids = counts.argsort()[::-1][:n]
    sorted_words = words[ids][:n_words]
    sorted_counts = counts[ids][:n_words]

    y_pos = np.arange(len(sorted_words))
    
    plt.bar(y_pos, sorted_counts, align='center', alpha=0.5)
    plt.xticks(y_pos, sorted_words, rotation=45)
    plt.ylabel('Frequency')
    plt.title(type)
    plt.tight_layout()
    plt.xlabel('', fontsize=7)
    plt.savefig(os.path.join(output_path, output_file))

