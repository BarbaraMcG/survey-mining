# Module for extracting keywords from Resofact survey data, and grouping them
# Changes from previous versions:
# - path for data is no longer hardcoded, it is computed based on the location of the current script
# - reading inputs from Excel file: the number of rows is no longer hard-coded
# - Extract keywords from each response rather than from the collection of all responses
# - Focus on single-word keywords, not phrases
# - Identify adjectives or nouns that modify those keywords, e.g. new products
# - Semantically cluster these attributes
# - If two keywords are nouns and appear one immediately after the other, we consider them a compound keyword
# - Extract adjectives that modify these compound keywords
# - After grouping the two keywords in the keyword compound, treat the keywords when they appear alone as any other keyword
# - Allow acronyms in the lemmatized response text used for creating compound keywords

# Load libraries:

from topia.termextract import extract  # installed with pypm install topia.termextract
# import operator
import nltk
import re
import os
import xlrd
# import xlwt
import csv
import time


# Function that maps Penn pos tags to WordNet pos tags:
def map_pos(pos_var):
    if pos_var.startswith("N"):
        return 'n'
    elif pos_var.startswith("J"):
        return 'a'
    elif pos_var.startswith("V"):
        return 'v'
    elif pos_var.startswith("R"):
        return 'r'
    else:
        return 'other'


# Function that replaces a string with the sequence of lemmas of its tokens:

def lemmatize_text(string, wnl_var):
    tokens = nltk.word_tokenize(string)
    pos_tokens = nltk.pos_tag(tokens)
    # print "pos_tokens:" + str(pos_tokens)
    my_raw_lemmas = []
    for i in range(0, len(tokens)):
        token = tokens[i]
        pos = pos_tokens[i][1]
        # print "pos", pos, "token", token
        # my_lemma = wnl_var.lemmatize(token, pos='n')  # assume noun since that's what term algorithm returns
        if map_pos(pos) != 'other':
            my_lemma = wnl_var.lemmatize(token, map_pos(pos))
        else:
            my_lemma = wnl_var.lemmatize(token)

        my_raw_lemmas.append(my_lemma)
    # lemma_string = ' '.join(my_raw_lemmas)
    return my_raw_lemmas


def clean_string(string):
    string = string.replace("\r\n", "\n").replace("\n\n", "\n").replace("\n", ".").replace("..", "."). \
        replace("?.", "?").replace(
        "!.", "!").replace(".", ". ").replace("?", "? ").replace("!", "! ")

    return string

 
# ------------------------------------------------------------------------
# Instantiate a new term extractor:
# -----------------------------------------------------------------------
extractor = extract.TermExtractor()
# extractor.filter = extract.DefaultFilter(singleStrengthMinOccur=2)
extractor.filter = extract.permissiveFilter

# ------------------------------------------------------------------------
# Instantiate a new Word Net lemmatizer:
# -----------------------------------------------------------------------
# wnl = nltk.stem.WordNetLemmatizer()
wnl = nltk.WordNetLemmatizer()

# -----------------------------------------------------------------------
# Data structure for key word adjectives
# ----------------------------------------------------------------------


class KwAdjective:
    def __init__(self):
        self.key_word = None
        self.adjectives = []

    def return_adjectives(self):
        return set(self.adjectives)

# -----------------------------------------------------------------------
# Function that returns the list of adjectives modifying a keyword:
# -----------------------------------------------------------------------

def find_adjectives_kw(kw_var, response_lemmatized, response_tagged, type_var):

    kw_adjective = ""
    kw_index = 0
    if type_var == "single":  # if the keyword is a single word

        if kw_var in response_lemmatized:
        # get position of kw in the tokenized response:
            kw_index = response_lemmatized.index(kw_var)

    elif type_var == "compound": # if the keyword is a compound of two keywords
        kw1 = kw_var.split(" ")[0]
        kw2 = kw_var.split(" ")[1]

        if kw1 in response_lemmatized and kw2 in response_lemmatized:
            # I consider the index of the first item of the compound for the purpose of finding its adjectives:
            kw_index = response_lemmatized.index(kw1)

    if kw_index > 0:
        kw_prev_index = kw_index - 1

        # find adjectives modifying keywords:
        if response_tagged[kw_prev_index][1] == 'JJ':
            kw_adjective = response_tagged[kw_prev_index][0]

    return kw_adjective

# -----------------------------------------------------------------------------------
# Functions that return the list of adjectives of the form keyword + BE + adjective:
# -----------------------------------------------------------------------------------

def find_adjectives_be_kw(kw_var, response_lemmatized, response_tagged, type_var):

    kw_adjective = ""
    if kw_var in response_lemmatized:
        # get position of kw in the tokenized response:
        if type_var == "single":
            kw_index = response_lemmatized.index(kw_var)
            kw_next_index = kw_index + 1
            kw_next2_index = kw_index + 2
        elif type_var == "compound":
            kw1 = kw_var.split(" ")[0]
            kw2 = kw_var.split(" ")[1]
            # I consider the index of the first item of the compound for the purpose of finding its adjectives:
            kw_index = response_lemmatized.index(kw1)
            kw_next_index = kw_index + 2
            kw_next2_index = kw_index + 3

        if kw_next2_index < len(response_tagged):
            if response_tagged[kw_next2_index][1] == 'JJ' and response_lemmatized[kw_next_index] == 'be':
                kw_adjective = response_tagged[kw_next2_index][0]

    return kw_adjective


def extract_keywords(test, target_word, input_directory, output_directory, output_file_keywords_name, output_file_freq_name, column_number, acronyms, exclude, exclude_keywords):    
    
    # Define directories and files:
    
    print "\tInitializing..."
    # get path of current file, then change sub directory from "code" to "data"
    
    input_file = target_word + '.xlsx'
        
    # Initialize objects:

    input_for_keyword_extractor = ""
    id_response = {}
    id_response_with_acronyms = {}
    kw_list = list()
    kw2freq = dict()
    kw2adj2freq = dict()
    kw_adjectives = dict()
    kw_adj_response = dict()

    # Prepare output file:

    outfile = open(os.path.join(output_directory, output_file_keywords_name), 'wb')
    output = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    output.writerow(["Id", "Response", "Keyword", "Adjectives"])

    # Read in input file:
    
    sheet_name = target_word
    row_id = 0
    assert os.path.exists(os.path.join(input_directory, input_file)), "I did not find the file "+str(input_file) + "in " + str(input_directory)
    sheet = xlrd.open_workbook(os.path.join(input_directory, input_file)).sheet_by_name(sheet_name)

    print "\tReading input..."
    if test == "yes":
        n = 10
    else:
        n = sheet.nrows
    for row_idx in range(2, n):
    #for row_idx in range(7, 8):
        if column_number == 0:
            row_id += 1
        else:
            row_id = sheet.cell(row_idx, 0).value

        print "\t\tReading response number " + str(row_id)
        response = sheet.cell(row_idx, column_number).value
        
        # response = line[2].lower()
        # if a response has a newline, replace it with a full stop so that the keyword extractor makes sense:
        if '\n' in response:
            response = clean_string(response)
        # add a full stop at the end of each response, otherwise the keyword extractor concatenates the responses:
        if not response.endswith(".") and not response.endswith("?") and not response.endswith("!"):
            response += " %s" % "."
        # if a response has a list, replace the list bullets with a full stop:
        if re.search(r'\d *?\)', response):
            response = re.sub(r'\d *?\)', '. ', response)
        response = response.replace(" - ", ". ")
        response_lower = response.lower()

        # replace -ing forms at the start of response with corresp. lemma. E.g. meeting -> meet
        response_tokens = nltk.word_tokenize(response_lower)

        if response_tokens[0].endswith('ing'):
            start_lemma = wnl.lemmatize(response_tokens[0], pos='v')
            response_tokens[0] = start_lemma
            response_lower = ' '.join(response_tokens)
        # remove acronyms from the responses:
        response_no_acronyms = response_lower
        for acronym in acronyms:
            my_regex = r"^(.+?)\b" + acronym + r"\b(.+?)$"
            if re.search(my_regex, response_lower):
                # tmp_response = response_noacronyms.replace(acronym.lower(), "")
                tmp_response = re.sub(my_regex, r'\1 \2', response_no_acronyms)
                response_no_acronyms = tmp_response

        id_response_with_acronyms[row_id] = response_lower

        response_no_acronyms = response_no_acronyms.replace("  ", " ").replace(" . ", ". ").replace("..", ".").replace(
            " . ", ".")
        response_no_acronyms = response_no_acronyms.replace(".", ". ").replace("  ", " ").replace(" . ", ". "). \
            replace("..", ".").replace(' . ', ".").replace("/", " ")
        response_no_acronyms = re.sub(r'[,\.;:\?!] *?\. *?', '. ', response_no_acronyms)
        response_no_acronyms = response_no_acronyms.replace("..", ".")
        
        response_yes_acronyms = response
        response_yes_acronyms = response_yes_acronyms.replace("  ", " ").replace(" . ", ". ").replace("..", ".").replace(
            " . ", ".")
        response_yes_acronyms = response_yes_acronyms.replace(".", ". ").replace("  ", " ").replace(" . ", ". "). \
            replace("..", ".").replace(' . ', ".").replace("/", " ")
        response_yes_acronyms = re.sub(r'[,\.;:\?!] *?\. *?', '. ', response_yes_acronyms)
        response_yes_acronyms = response_yes_acronyms.replace("..", ".")

        for w in exclude:
            my_regex = r"^(.*?)\b" + w + r"\b(.*?)$"
            if re.search(my_regex, response_no_acronyms):
                tmp_response = re.sub(my_regex, r'\1 \2', response_no_acronyms)
                response_no_acronyms = tmp_response
            if re.search(my_regex, response_yes_acronyms):
                tmp_response = re.sub(my_regex, r'\1 \2', response_no_acronyms)
                response_yes_acronyms = tmp_response
                
        id_response[row_id] = response_no_acronyms

        # ------------------------------------------------------------------------
        # Extract keywords:
        # -----------------------------------------------------------------------
        formatted_no_acronyms = re.sub(r'\bi\b', 'I', response_no_acronyms.lower())
        #print "formatted_no_acronyms:" + str(formatted_no_acronyms)
        my_extractor = extractor(formatted_no_acronyms)

        my_response_tokenized_no_acronyms = nltk.word_tokenize(formatted_no_acronyms)
        #print "my_response_tokenized_no_acronyms:" + str(my_response_tokenized_no_acronyms)
        my_response_tagged_no_acronyms = nltk.pos_tag(my_response_tokenized_no_acronyms)
        #print "my_response_tagged_no_acronyms:" + str(my_response_tagged_no_acronyms)
        my_response_lemmatized_no_acronyms = lemmatize_text(formatted_no_acronyms, wnl)
        #print "my_response_lemmatized_no_acronyms:" + str(my_response_lemmatized_no_acronyms)
        
        formatted_yes_acronyms = re.sub(r'\bi\b', 'I', response_yes_acronyms)
        #print "formatted_yes_acronyms:" + str(formatted_yes_acronyms)
        #my_extractor = extractor(formatted_yes_acronyms)

        my_response_tokenized_yes_acronyms = nltk.word_tokenize(formatted_yes_acronyms)
        my_response_tagged_yes_acronyms = nltk.pos_tag(my_response_tokenized_yes_acronyms)
        my_response_lemmatized_yes_acronyms = lemmatize_text(formatted_yes_acronyms, wnl)

        # ----------------------------------------------------------------------
        # Select keywords:
        # ----------------------------------------------------------------------

        kws_response = list()
        for item in my_extractor:
            kw = item[0]
            print "\t\t\tkw:" + kw
            # exclude keywords that do not contain any alphabetical characters;
            # only keep one-word keywords and exclude certain words from the list of keywords:
            if re.search('[a-zA-Z]', kw) and len(kw.split(" ")) < 2 and kw not in exclude_keywords:
                kw_list.append(kw)
                kws_response.append(kw)
                kw2freq[kw] = kw2freq.get(kw, 0) + 1

                # --------------------------------------------------
                # find adjectives associated with this keyword:
                # --------------------------------------------------
                
                #print "response:" + str(my_response_lemmatized_yes_acronyms)
                kw_adj_response[kw] = ""
                my_adjective = ""
                my_adjective = find_adjectives_kw(kw, my_response_lemmatized_yes_acronyms, my_response_tagged_yes_acronyms, "single")
                #print "adj:" + my_adjective
                my_adjective_be = ""
                my_adjective_be = find_adjectives_be_kw(kw, my_response_lemmatized_yes_acronyms, my_response_tagged_yes_acronyms, "single")

                for my_adj in [my_adjective, my_adjective_be]:
                    if my_adj != "" and my_adj is not None:
                        # exclude adjectives that do not contain any alphabetical characters:
                        if re.search('[a-zA-Z]', my_adj):
                            kw_adj_response[kw] = my_adj.lower()
                            if (kw, my_adj) in kw2adj2freq:
                                kw2adj2freq[(kw, my_adj)] += 1
                            else:
                                kw2adj2freq[(kw, my_adj)] = 1
                            if kw in kw_adjectives:
                                kw_adjectives[kw].adjectives.append(my_adj)
                            else:
                                kw_a_object = KwAdjective()
                                kw_a_object.key_word = kw
                                kw_a_object.adjectives.append(my_adj)
                                kw_adjectives[kw] = kw_a_object
                                
        # -----------------------------------------------------
        # Add acronyms to the list of keywords:
        # -----------------------------------------------------

        for acronym in acronyms:
            freq_acronym = 0
            response_withacronyms = response
            my_regex = r".+?\b" + acronym + r"\b.+?"
            if re.search(my_regex, response_lower):
                kw_list.append(acronym)
                kws_response.append(acronym)
                kw2freq[acronym] = kw2freq.get(acronym, 0) + 1

        # If two keywords are nouns and appear one immediately after the other, we consider them a compound keyword;
        # e.g. "brand name", "track record":
        
        #print my_response_lemmatized_yes_acronyms
        for kw1 in kws_response:
            for kw2 in kws_response:
                if kw1 != kw2 and len(kw1.split(" ")) == 1 and len(kw2.split(" ")) == 1:
                    compound_kw = ""
                    try:
                        index_kw1 = my_response_lemmatized_yes_acronyms.index(kw1)
                        index_kw2 = my_response_lemmatized_yes_acronyms.index(kw2)
                        #print "index 1:" + str(index_kw1)
                        #print "index 2:" + str(index_kw2)                        
                        if index_kw2 > 1 and index_kw1 == index_kw2 - 1:
                            compound_kw = kw1 + " " + kw2
                        elif index_kw1 > 1 and index_kw2 == index_kw1 - 1:
                            compound_kw = kw2 + " " + kw1
                        #print "compound:" + compound_kw
                    except:
                        #print "Error for " + kw1 + " and " + kw2
                        compound_kw = ""
                        
                    if compound_kw != "":
                        kws_response.append(compound_kw)
                        kw_list.append(compound_kw)
                        kw2freq[compound_kw] = kw2freq.get(compound_kw, 0) + 1
                        #print "frequency:" + str(kw2freq[compound_kw])

                        # add adjectives of compound keyword:
                        kw_adj_response[compound_kw] = ""
                        try:
                            my_adjective_c = find_adjectives_kw(compound_kw, my_response_lemmatized_yes_acronyms, my_response_tagged_yes_acronyms, "compound")
                        except:
                            my_adjective_c = ""
                        #print "adjective:" + my_adjective_c
                        try:
                            my_adjective_c_be = find_adjectives_be_kw(compound_kw, my_response_lemmatized_yes_acronyms, my_response_tagged_yes_acronyms, "compound")
                        except:
                            my_adjective_c_be = ""
                        #print "adjective be:" + my_adjective_c_be

                        for my_adj_c in [my_adjective_c, my_adjective_c_be]:
                            if my_adj_c != "":
                                if re.search('[a-zA-Z]', my_adj_c):
                                    kw_adj_response[compound_kw] = my_adj_c.lower()
                                    if (compound_kw, my_adj_c) in kw2adj2freq:
                                        kw2adj2freq[(compound_kw, my_adj_c)] += 1
                                    else:
                                        kw2adj2freq[(compound_kw, my_adj_c)] = 1
                                    if compound_kw in kw_adjectives:
                                        kw_adjectives[compound_kw].adjectives.append(my_adj_c)
                                    else:
                                        kw_a_object = KwAdjective()
                                        kw_a_object.key_word = compound_kw
                                        kw_a_object.adjectives.append(my_adj_c)
                                        kw_adjectives[compound_kw] = kw_a_object
                    

        # --------------------------------------------------
        # Print out keywords:
        # --------------------------------------------------
        kws_response = set(kws_response)
        for kw in kws_response:
            output.writerow([row_id, response, kw, kw_adj_response.get(kw, "")])

    outfile.close()

    # ---------------------------------------------
    # Open output file with keywords' frequency:
    # ---------------------------------------------
    
    print "\tWriting output..."
    outfile_freq = open(os.path.join(output_directory, output_file_freq_name), 'wb')
    output_freq = csv.writer(outfile_freq, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    output_freq.writerow(
        ["Keyword", "Number of responses of keyword", "Adjective", "Number of responses of keyword and adjective"])
    kw_list = sorted(list(set(kw_list)))

    count = 0
    for kw in kw_list:
        count += 1
        print "\t\t" + str(count) + " out of " + str(len(kw_list)) + ": Printing frequencies: " + kw
        if kw in kw_adjectives:
            my_adj_list = kw_adjectives[kw].return_adjectives()
        else:
            my_adj_list = list()

        if len(my_adj_list) > 0:
            for adj in my_adj_list:
                output_freq.writerow([kw, str(kw2freq[kw]), adj, str(kw2adj2freq[(kw, adj)])])
        else:
            output_freq.writerow([kw, str(kw2freq[kw]), "", ""])

    outfile_freq.close()
