# Module for creating graphs from responses and their keywords

#import plotly.plotly as py
#from plotly.graph_objs import *
import networkx as nx
import matplotlib.pyplot as plt
import time
import os
import csv

def create_graph(input_path, input_file, output_path, output_file, min_freq):
    
    # Create empty graph:

    G = nx.Graph()

    # Populate the graph with the keywords/clusters as nodes:
    
    id_response = ""
    keyword_nodes = list()
    kw2response = dict() # maps a kw to the list of responses containing it

    with open(os.path.join(input_path, input_file), 'rb') as csv_file:
        next(csv_file)
        res_reader = csv.reader(csv_file, delimiter=',')
        my_count = 0
        for row in res_reader:
            id_response = row[0]
            kw = row[2]
            keyword_nodes.append(kw)
            if kw in kw2response:
                responses_for_kw = kw2response[kw]
                responses_for_kw.append(id_response)
                kw2response[kw] = responses_for_kw
            else:
                kw2response[kw] = [id_response]
            
    
    keyword_nodes = list(set(keyword_nodes))
    keyword_nodes.sort()
    
    # only keep keywords that occur in more than min_response response:
    for kw in keyword_nodes:
        if len(kw2response[kw]) < min_freq + 1:
            keyword_nodes.remove(kw)
    
    
    for kw in keyword_nodes:
        G.add_node(kw)
    #print(str(G.nodes()))
    
    # Add edges to graph:
    
    # two nodes (keywords) are connected if they appear in the same response:
    for kw1 in keyword_nodes:
        responses_kw1 = kw2response[kw1]
        for kw2 in keyword_nodes:
            responses_kw2 = kw2response[kw2]
            overlap = len(list(set(responses_kw1).intersection(responses_kw2)))
            if overlap > 0:
                G.add_edge(kw1, kw2, weight = overlap^2)
            
    #print(str(G.edges()))
    
    # Plot graph:
    
    pos = nx.spring_layout(G) # positions for all nodes
    edges = G.edges()
    weights = [G[u][v]['weight'] for u,v in edges]

    nx.draw(G, pos, edges = edges, width=weights, with_labels = True)
    #plt.show()
    plt.savefig(os.path.join(output_path, output_file))        

    
#create_graph("C:\Users\Barbara\Dropbox\Resofact\data\output\Telkom_pride_embarassment\Telkom_pride", "Responses_keywords_pride_23102016_test.csv", "C:\Users\Barbara\Dropbox\Resofact\code\plots", 'graph_pride_' + time.strftime("%d%m%Y") + ".png")
    
    
