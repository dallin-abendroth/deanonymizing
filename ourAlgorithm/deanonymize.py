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
            return child
        return self.children[childname]
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
    def H_nodes_matched(self):
        if(self.parent!=None):
            return [self.match_in_h] + self.parent.H_nodes_matched()
        else:
            return []
    def G_nodes_matched(self):
        return self.path_to_root()
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

def subgraph_neighbors(G,nodes):
    neighbors = []
    for node in nodes:
        neighbors.extend(list(G.neighbors(node)))
        if(nx.is_directed(G)):
            neighbors.extend(list(G.predecessors(node)))
    neighbors = [x for x in neighbors if x not in nodes]
    return set(neighbors)

def coalition_neighbors(G,attacker):
    neighbors = []
    neighbors.extend(list(G.neighbors(attacker)))
    if(nx.is_directed(G)):
        neighbors.extend(list(G.predecessors(attacker)))
    return set(neighbors)

def make_coalition(G,attacker,k):
    coalition = [attacker,]
    while len(coalition)<k:
        potential_recruits = list(coalition_neighbors(G, attacker))
        potential_recruits = [item for item in potential_recruits if item not in coalition]
        if(len(potential_recruits)==0):
            return coalition
        new_member = max_degree(G,potential_recruits)
        if(new_member not in coalition):
            coalition.append(new_member)
    return coalition

def max_degree(G,nodes):
    max_degree = ('apple',0)
    for node in nodes:
        node_degree = G.degree[node]
        if(nx.is_directed(G)):
            node_degree += G.in_degree[node]
        if(node_degree>max_degree[1]):
            max_degree = (node,node_degree)
    return max_degree[0]

def extract_matches(tree,k):
    matches = []
    for leaf in tree.leaf_nodes():
        path = leaf.path_to_root()
        if(len(path)==k):
            matches.append(frozenset(path))
    return set(matches)

def tree_search_rec_directed(G,H,T,candidate_node,x):
    global multiple_matches_failure
    if(multiple_matches_failure): return
    for x_nbr in H.successors(x): # check weights of out-edges
        if(x_nbr in T.H_nodes_matched()): continue
        for cand_nbr in G.successors(candidate_node):
            if(multiple_matches_failure): return
            if(cand_nbr in T.G_nodes_matched()): continue
            if(G[candidate_node][cand_nbr]['weight']==H[x][x_nbr]['weight']
                    and degree_match(G,H,x_nbr,cand_nbr)):
                newT = T.add(cand_nbr, x_nbr)
                if(check_mult_matches(newT, k, newT.H_nodes_matched())): return
                tree_search_rec_simple(G,H,newT,candidate_node,x)
    for x_nbr in H.predecessors(x): # check weights of in-edges
        if(x_nbr in T.H_nodes_matched()): continue
        for cand_nbr in G.predecessors(candidate_node):
            if(multiple_matches_failure): return
            if(cand_nbr in T.G_nodes_matched()): continue
            if(G[cand_nbr][candidate_node]['weight']==H[x_nbr][x]['weight']
                    and degree_match(G,H,x_nbr,cand_nbr)):
                newT = T.add(cand_nbr, x_nbr)
                if(check_mult_matches(newT, k, newT.H_nodes_matched())): return
                tree_search_rec_simple(G,H,newT,candidate_node,x)

def tree_search_rec_simple(G,H,T,candidate_node,x):
    global multiple_matches_failure
    if(multiple_matches_failure): return
    for x_nbr in H.neighbors(x): 
        if(x_nbr in T.H_nodes_matched()): continue
        for cand_nbr in G.neighbors(candidate_node):
            if(multiple_matches_failure): return
            if(cand_nbr in T.G_nodes_matched()): continue
            if(degree_match(G,H,x_nbr,cand_nbr)):
                newT = T.add(cand_nbr, x_nbr)
                if(check_mult_matches(newT, k, newT.H_nodes_matched())): return
                tree_search_rec_simple(G,H,newT,candidate_node,x)

def tree_search(G,H,attacker, tree_search_rec_fn):
    T = TreeNode('base','base')
    for candidate in list(G.nodes):
        if(degree_match(G,H,attacker,candidate)):
            T_cand = T.add(candidate,attacker)
            tree_search_rec_fn(G,H,T_cand,candidate,attacker) 
    k = len(list(H.nodes))
    return extract_matches(T,k)

def degree_match(G,H,x,candidate):
    x_degree = H.nodes[x]['orig_degree']
    cand_degree = G.degree[candidate]
    if(nx.is_directed(G)):
        x_in_degree = H.nodes[x]['orig_in_degree']
        cand_in_degree = G.in_degree[candidate]
        return (x_degree == cand_degree
                and x_in_degree == cand_in_degree)
    return (x_degree == cand_degree)

def check_mult_matches(T, k, matched):
    global multiple_matches_failure
    global matches_so_far
    if(k == len(matched)):
        matches_so_far+=1
        if(matches_so_far>1):
            matches = extract_matches(T.get_root(),k)
            if(len(matches)>1):
                multiple_matches_failure = True
            else:
                matches_so_far = 1
        return True
    return False

def setup_H_subgraph(G, subG):
    directed = nx.is_directed(G)
    nx.set_node_attributes(subG, 'orig_degree', 0)
    if(directed): nx.set_node_attributes(subG, 'orig_in_degree', 0)
    for node in list(subG.nodes):
        subG.nodes[node]['orig_degree'] = G.degree[node]
        if(directed): subG.nodes[node]['orig_in_degree'] = G.in_degree[node]

def deanonymize_weighted_directed(G,k,given_coalition):
    global multiple_matches_failure
    initial_attacker = random.choice(list(G.nodes))
    coalition = make_coalition(G, initial_attacker, k)
    if(len(given_coalition)>0):
        initial_attacker = given_coalition[0]
        coalition = given_coalition
    subG = nx.subgraph(G, coalition)
    setup_H_subgraph(G, subG)
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
    if(not matched_self and not multiple_matches_failure):
        print("!!! original coalition not found, this should be impossible. Coalition below !!!")
        print(' '.join(coalition))
    if(len(matches)!=1): # cannot deanonymize
        return 0
    return len(subgraph_neighbors(G, coalition))

def deanonymize_simple(G,k,given_coalition):
    global multiple_matches_failure
    initial_attacker = random.choice(list(G.nodes))
    coalition = make_coalition(G, initial_attacker, k)
    if(len(given_coalition)>0):
        initial_attacker = given_coalition[0]
        coalition = given_coalition
    subG = nx.subgraph(G,coalition)
    setup_H_subgraph(G, subG)
    matches = tree_search(G, subG, initial_attacker, tree_search_rec_simple)
    if(len(matches)==0):
        print("!!! zero matches found, this should be impossible. Coalition below !!!")
        print(' '.join(coalition))
        print(subG.edges(coalition))
        print(subG.edges(coalition))
    matched_self = False
    for match in matches:
        if set(coalition)==set(match):
            matched_self = True
    if(not matched_self and not multiple_matches_failure):
        print("!!! original coalition not found, this should be impossible. Coalition below !!!")
        print(' '.join(coalition))
    if(len(matches)!=1): # cannot deanonymize
        return 0
    return len(subgraph_neighbors(G, coalition))

def print_usage():
    print("""Usage: 
        python deanonymize.py [csv file to use] [simple|directed] random [size of coalition] 
        python deanonymize.py [csv file to use] [simple|directed] random [size of coalition] [times to run]
        python deanonymize.py [csv file to use] [simple|directed] given-coalition [coalition member 1] ... [coalition member N]
        
        NOTE: coalition must strictly consist of a 'root' node and its neighbors""")
    sys.exit(0)
    
multiple_matches_failure = False
matches_so_far = 0
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
            multiple_matches_failure = False
            matches_so_far = 0
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
            multiple_matches_failure = False
            matches_so_far = 0
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
