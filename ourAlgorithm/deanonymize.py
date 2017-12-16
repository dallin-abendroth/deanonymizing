import networkx as nx
import csv
import sys
import random
import datetime as dt

source_i = 0
dest_i = 1
wght_i = 2

class TreeNode(object):
    """Tree class made for quick convenience"""
    def __init__(self, name, match_in_h, parent=None):
        self.parent = parent
        self.name = name
        self.match_in_h = match_in_h
        self.children = {}
    def add(self, childname, childmatch):
        if(childname not in self.children):
            child = TreeNode(childname, childmatch, self)
            self.children[childname] = child
            return True
        return False
    def get(self, childname):
        if(childname in self.children):
            return self.children[childname]
    def get_root(self):
        if(self.parent==None):
            return self
        return self.parent.get_root()
    def leaf_nodes(self):
        if(not self.children):
            return [self]
        leaf_nodes = []
        for child in self.children:
            leaf_nodes = leaf_nodes+self.children[child].leaf_nodes()
        return leaf_nodes
    def path_to_root_h(self):
        if(self.parent!=None):
            return [self.match_in_h] + self.parent.path_to_root_h()
        else:
            return []
    def path_to_root_all(self):
        if(self.parent!=None):
            return [(self.name, self.match_in_h)] + self.parent.path_to_root_all()
        else:
            return []
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
    return set(neighbors)

def coalition_neighbors_directed(G,coalition_nodes):
    neighbors = []
    for node in coalition_nodes:
        neighbors.extend(list(G.successors(node)))
        neighbors.extend(list(G.predecessors(node)))
    return set(neighbors)

def make_coalition(G,attacker,k,coalition_neighbors_fn):
    coalition = [attacker]
    while len(coalition)<k:
        potential_recruits = list(coalition_neighbors_fn(G, coalition))
        if(len(potential_recruits)==0):
            return coalition
        new_member = random.choice(potential_recruits)
        if(new_member not in coalition):
            coalition.append(new_member)
    return coalition

def extract_matches(tree,k):
    matches = []
    for leaf in tree.leaf_nodes():
        path = leaf.path_to_root()
        if(len(path)==k):
            matches.append(frozenset(path))
    return set(matches)

def tree_search(G,H,node,tree_search_rec_fn):
    T = TreeNode('base','base')
    for candidate in list(G.nodes):
        tree_search_rec_fn(G,H,T,candidate,node) 
    k = len(list(H.nodes))
    return extract_matches(T,k)

def digraph_neighbors(G,node):
    neighbors = []
    neighbors.extend(G.predecessors)

def tree_search_rec_directed(G,H,T,candidate_node,x):
    x_out_degree = H.nodes[x]['orig_out_degree'] 
    x_in_degree = H.nodes[x]['orig_in_degree'] 

    real = ['3095', '4446', '1983'] # removed 35 and 3269

    if(candidate_node in T.path_to_root()): # potential nodes count once
        return
    if(G.out_degree[candidate_node]==x_out_degree # check out-degrees
            and G.in_degree[candidate_node]==x_in_degree): # check in-degrees
        new_child = T.add(candidate_node,x)
        if(not new_child):
            return
        for x_nbr in H.successors(x): # check weights of out-edges
            found_this_neighbor = False
            for cand_nbr in G.successors(candidate_node):
                if(G[candidate_node][cand_nbr]['weight']==H[x][x_nbr]['weight']):
                    if(candidate_node in real):
                        print("Added ", candidate_node," here!")
                    tree_search_rec_directed(G,H,T.get(candidate_node),cand_nbr,x_nbr)
        for x_nbr in H.predecessors(x): # check weights of in-edges
            for cand_nbr in G.predecessors(candidate_node):
                if(G[cand_nbr][candidate_node]['weight']==H[x_nbr][x]['weight']):
                    tree_search_rec_directed(G,H,T.get(candidate_node),cand_nbr,x_nbr)

def tree_search_rec_simple(G,H,T,candidate_node,x):
    nodes_matched = T.path_to_root_h()
    k = len(list(H.nodes))
    if(candidate_node in T.path_to_root()
            or x in nodes_matched): # potential nodes count once
        return
    x_degree = H.nodes[x]['orig_degree'] 
    if(G.degree[candidate_node]==x_degree): # check degrees
        new_child = T.add(candidate_node,x)
        T = T.get(candidate_node)
        nodes_matched = T.path_to_root_h()
        if(not new_child 
                or len(nodes_matched) == k):
            return
        for x_nbr in H.neighbors(x): 
            if(x_nbr in nodes_matched):
                continue
            for cand_nbr in G.neighbors(candidate_node):
                tree_search_rec_simple(G,H,T,cand_nbr,x_nbr)
        for parent in T.parent.path_to_root_all(): # check for paths only accessible to nodes previously visited
            # this check will probably add a lot of time :(
            for x_parent_nbr in H.neighbors(parent[1]):
                if(x_parent_nbr in nodes_matched):
                    continue
                for cand_parent_nbr in G.neighbors(parent[0]):
                    tree_search_rec_simple(G,H,T,cand_parent_nbr,x_parent_nbr)

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
    if(len(matches)==0):
        print("!!! zero matches found, this should be impossible. Coalition below !!!")
        print(' '.join(coalition))
        print(subG.edges(coalition))
        print(subG.edges(coalition))
    matched_self = False
    for match in matches:
        if set(coalition)==set(match):
            matched_self = True
    if(matched_self):
        print("!!! original coalition not found, this should be impossible. Coalition below !!!")
        print(' '.join(coalition))
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
        python deanonymize.py [csv file to use] [simple|directed] random [size of coalition] 
        python deanonymize.py [csv file to use] [simple|directed] random [size of coalition] [times to run]
        python deanonymize.py [csv file to use] [simple|directed] given-coalition [coalition member 1] ... [coalition member N]""")
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
    if(len(sys.argv)==6 and sys.argv[3]=='random'):
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
        timings = []
        for i in range(0,times_to_run):
            start = dt.datetime.now()
            results.append(deanonymize_simple(G,k,given_coalition))
            timings.append((dt.datetime.now()-start).microseconds / 1000)
        avg = sum(results) / float(len(results))
        avgtime = sum(timings) / float(len(timings))
        prob_success = (len(results) - results.count(0)) / float(len(results))
        if(times_to_run>1):
            print("avg = ",avg)
            print("probability of success = ",prob_success)
            print("avg time = ",avgtime)
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
        timings = []
        for i in range(0,times_to_run):
            start = dt.datetime.now()
            results.append(deanonymize_weighted_directed(G,k,given_coalition))
            timings.append((dt.datetime.now()-start).microseconds / 1000)
        avg = sum(results) / float(len(results))
        avgtime = sum(timings) / float(len(timings))
        prob_success = (len(results) - results.count(0)) / float(len(results))
        if(times_to_run>1):
            print("avg = ",avg)
            print("probability of success = ",prob_success)
            print("avg time = ",avgtime)
        else:
            print("Deanonymized nodes: ",results[0])
        print("--------------------------------")
        sys.exit(0)

    print_usage()
