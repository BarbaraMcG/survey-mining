# Module for creating word clouds from responses and their keywords

import os
import csv
from pytagcloud import create_tag_image, make_tags
from pytagcloud.lang.counter import get_tag_counts

# pip install pytagcloud
# depends on: pygame, simplejson (pip install...)
# from:
# https://pypi.python.org/pypi/pytagcloud

# test_words = ('hello', 'goodbye', 'yes')
# test_counts = (2, 3, 1)

def create_word_cloud(input_path, input_file, out_path, out_file, type):
    # function for repeating words n times into a continuous texts:
    def make_text(w, c):

        """
        :param w: a list of words, each of which is to be repeated
        :param c: a list of counts (how many times each word is repeated). Matching in position with w.
        :return: a string (white space separated) of continuous words.
        """
        assert (len(w) == len(c))

        my_out_list = []
        for i, item in enumerate(w):
            my_word = item
            my_n = c[i]
            for j in range(my_n):
                # print my_word
                my_out_list.append(my_word)

        my_res = ' '.join(my_out_list)
        return my_res


    # test:
    # print make_text(test_words, test_counts)

    input_words = []
    input_counts = []
    with open(os.path.join(input_path, input_file), 'rb') as csv_file:
        res_reader = csv.reader(csv_file, delimiter=',')
        my_count = 0
        prev_kw = ''
        kw = ""
        freq = ""
        word_col = 0
        freq_col = 1
        if type == "clusters":
            word_col = 1
            freq_col = 2
        for row in res_reader:
            kw = row[word_col]
            freq = row[freq_col]
            if my_count > 0:
                if kw != prev_kw:
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

    #print len(input_words)
    #print len(input_counts)

    x = make_text(input_words, input_counts)
    #print x

    tags = make_tags(get_tag_counts(x), maxsize=100)
    create_tag_image(tags, os.path.join(out_path, out_file), size=(900, 600))
    #print 'Done'
