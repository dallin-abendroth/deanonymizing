import networkx as nx
import csv
import sys
import random

source_i = 0
dest_i = 1
wght_i = 2

class TreeNode(object):
    """Tree class made for quick convenience"""
    def __init__(self, name, parent=None):
        self.parent = parent
        self.name = name
        self.children = {}
    def add(self, childname):
        if(childname not in self.children):
            child = TreeNode(childname, self)
            self.children[childname] = child
    def get(self, childname):
        if(childname in self.children):
            return self.children[childname]
    def leaf_nodes(self):
        if(not self.children):
            return [self]
        leaf_nodes = []
        for child in self.children:
            leaf_nodes = leaf_nodes+self.children[child].leaf_nodes()
        return leaf_nodes
    def path_to_root(self):
        if(self.parent!=None):
            return [self.name] + self.parent.path_to_root()
        else:
            return []

def get_weighted_directed_graph_from_csv(filename):
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

def get_simple_graph_from_csv(filename):
    G = nx.Graph()
    with open(filename, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        for entry in datareader:
            source = entry[source_i]
            dest = entry[dest_i]
            edge = [(source, dest)]
            G.add_edges_from(edge)
    return G

def coalition_neighbors_simple(G,coalition_nodes):
    neighbors = []
    for node in coalition_nodes:
        neighbors.extend(list(G.neighbors(node)))
    return neighbors

def coalition_neighbors_directed(G,coalition_nodes):
    neighbors = []
    for node in coalition_nodes:
        neighbors.extend(list(G.successors(node)))
        neighbors.extend(list(G.predecessors(node)))
    return neighbors

def make_coalition(G,attacker,k,coalition_neighbors_fn):
    coalition = [attacker]
    while len(coalition)<k:
        potential_recruits = coalition_neighbors_fn(G, coalition)
        if(len(potential_recruits)==0):
            return coalition
        new_member = random.choice(potential_recruits)
        coalition.append(new_member)
    return coalition

def extract_matches(tree,k):
    matches = []
    for leaf in tree.leaf_nodes():
        path = leaf.path_to_root()
        if(len(path)==k):
            matches.append(path)
    return matches

def tree_search(G,H,node,tree_search_rec_fn):
    T = TreeNode('base')
    for candidate in list(G.nodes):
        tree_search_rec_fn(G,H,T,candidate,node) 
    k = len(list(H.nodes))
    return extract_matches(T,k)

def tree_search_rec_directed(G,H,T,candidate_node,x):
    x_out_degree = H.nodes[x]['orig_out_degree'] 
    x_in_degree = H.nodes[x]['orig_in_degree'] 
    if(candidate_node in T.path_to_root()): # potential nodes count once
        return
    if(G.out_degree[candidate_node]==x_out_degree # check out-degrees
            and G.in_degree[candidate_node]==x_in_degree): # check in-degrees
        for x_nbr in H.successors(x): # check weights of out-edges
            for cand_nbr in G.successors(candidate_node):
                if(G[candidate_node][cand_nbr]['weight']==H[x][x_nbr]['weight']):
                    T.add(candidate_node)
                    tree_search_rec_directed(G,H,T.get(candidate_node),cand_nbr,x_nbr)
        for x_nbr in H.predecessors(x): # check weights of in-edges
            for cand_nbr in G.predecessors(candidate_node):
                if(G[cand_nbr][candidate_node]['weight']==H[x_nbr][x]['weight']):
                    T.add(candidate_node)
                    tree_search_rec_directed(G,H,T.get(candidate_node),cand_nbr,x_nbr)

def tree_search_rec_simple(G,H,T,candidate_node,x):
    x_degree = H.nodes[x]['orig_degree'] 
    if(candidate_node in T.path_to_root()): # potential nodes count once
        return
    if(G.degree[candidate_node]==x_degree): # check degrees
        for x_nbr in H.neighbors(x): 
            for cand_nbr in G.neighbors(candidate_node):
                T.add(candidate_node)
                tree_search_rec_simple(G,H,T.get(candidate_node),cand_nbr,x_nbr)

def setup_H_subgraph_directed(G, subG):
    nx.set_node_attributes(subG, 'orig_out_degree', 0)
    nx.set_node_attributes(subG, 'orig_in_degree', 0)
    for node in list(subG.nodes):
        subG.nodes[node]['orig_out_degree'] = G.out_degree[node]
        subG.nodes[node]['orig_in_degree'] = G.in_degree[node]

def setup_H_subgraph_simple(G, subG):
    nx.set_node_attributes(subG, 'orig_degree', 0)
    for node in list(subG.nodes):
        subG.nodes[node]['orig_degree'] = G.degree[node]

def deanonymize_weighted_directed(G,k,given_coalition):
    initial_attacker = random.choice(list(G.nodes))
    coalition = make_coalition(G, initial_attacker, k, coalition_neighbors_directed)
    if(len(given_coalition)>0):
        initial_attacker = given_coalition[0]
        coalition = given_coalition
    subG = nx.subgraph(G, coalition)
    setup_H_subgraph_directed(G, subG)
    matches = tree_search(G, subG, initial_attacker, tree_search_rec_directed)
    if(len(matches)!=1):
        return 0
    return len(coalition_neighbors_directed(G, subG))

def deanonymize_simple(G,k,given_coalition):
    initial_attacker = random.choice(list(G.nodes))
    coalition = make_coalition(G, initial_attacker, k, coalition_neighbors_simple)
    if(len(given_coalition)>0):
        initial_attacker = given_coalition[0]
        coalition = given_coalition
    subG = nx.subgraph(G, coalition)
    setup_H_subgraph_simple(G, subG)
    matches = tree_search(G, subG, initial_attacker, tree_search_rec_simple)
    if(len(matches)!=1):
        return 0
    return len(coalition_neighbors_simple(G, subG))

def print_usage():
    print("""Usage: 
        python file-to-graph.py [csv file to use] [simple|directed] random [size of coalition] 
        python file-to-graph.py [csv file to use] [simple|directed] random [size of coalition] [times to run]
        python file-to-graph.py [csv file to use] [simple|directed] given-coalition [coalition member 1] ... [coalition member N]""")
    sys.exit(0)
    
if __name__ == "__main__":
    if(len(sys.argv)<5):
        print_usage()
    if(sys.argv[2] != 'simple' and sys.argv[2] != 'directed'):
        print_usage()
    if(sys.argv[3] != 'random' and sys.argv[3] != 'given-coalition'):
        print_usage()

    given_coalition = []
    if(sys.argv[3]=='given-coalition'):
        member_index = 4
        while(member_index<len(sys.argv)):
            given_coalition.append(sys.argv[member_index])
            member_index+=1

    k = len(given_coalition)
    if(k==0):
        try:
            k = int(sys.argv[4])
        except:
            print_usage()

    times_to_run = 1
    if(len(sys.argv)==6):
        try:
            times_to_run = int(sys.argv[5])
            if(times_to_run<1):
                print("Yes, you have to run at least once.")
        except:
            print_usage()

    if(sys.argv[2]=='simple'):
        print("--------------------------------")
        print("Running simple algorithm ",times_to_run," time(s) on dataset: ",sys.argv[1])
        if(len(given_coalition)>0):
            print("Using given coalition: ",given_coalition)
        print("k = ",k)
        G = get_simple_graph_from_csv(sys.argv[1])
        results = []
        for i in range(0,times_to_run):
            results.append(deanonymize_simple(G,k,given_coalition))
        avg = sum(results) / float(len(results))
        if(times_to_run>1):
            print("avg = ",avg)
        else:
            print("Deanonymized nodes: ",results[0])
        print("--------------------------------")
        sys.exit(0)
    
    if(sys.argv[2]=='directed'):
        print("--------------------------------")
        print("Running weighted, directed algorithm ",times_to_run," time(s) on dataset: ",sys.argv[1])
        if(len(given_coalition)>0):
            print("Using given coalition: ",given_coalition)
        print("k = ",k)
        G = get_weighted_directed_graph_from_csv(sys.argv[1])
        results = []
        for i in range(0,times_to_run):
            results.append(deanonymize_weighted_directed(G,k,given_coalition))
        avg = sum(results) / float(len(results))
        if(times_to_run>1):
            print("avg = ",avg)
        else:
            print("Deanonymized nodes: ",results[0])
        print("--------------------------------")
        sys.exit(0)

    print_usage()
