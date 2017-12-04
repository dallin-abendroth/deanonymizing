import networkx as nx
import csv
import sys

source_i = 0
dest_i = 1
wght_i = 2

def get_graph(filename):
    G = nx.DiGraph()
    with open(filename, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        for entry in datareader:
            source = entry[source_i]
            dest = entry[dest_i]
            weight = entry[wght_i]
            edge = [(source, dest, {'weight':weight})]
            G.add_edges_from(edge)
    return G

if __name__ == "__main__":
    if(len(sys.argv)==2):
        G = get_graph(sys.argv[1])
        print "Nodes: ",G.number_of_nodes()
        print "Edges: ",G.number_of_edges()
    else:
        print "Usage: python file-to-graph.py [filename]"
