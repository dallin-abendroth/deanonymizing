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

def get_graph_from_csv(filename):
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

def coalition_neighbors(G,coalition_nodes):
    neighbors = []
    for node in coalition_nodes:
        neighbors.extend(list(G.successors(node)))
        neighbors.extend(list(G.predecessors(node)))
    return neighbors

def make_coalition(G,attacker,k):
    coalition = [attacker]
    while len(coalition)<k:
        potential_recruits = coalition_neighbors(G, coalition)
        if(len(potential_recruits)==0):
            return coalition
        new_member = random.choice(coalition_neighbors(G, coalition))
        coalition.append(new_member)
    return coalition

def node_with_max_degree(G,nodes):
    node_degrees = G.degree(nodes)
    node_degrees = dict((x,y) for x, y in node_degrees)
    return max(node_degrees, key=node_degrees.get)

def extract_matches(tree,k):
    matches = []
    for leaf in tree.leaf_nodes():
        path = leaf.path_to_root()
        if(len(path)==k):
            matches.append(path)
    return matches

def tree_search(G,H,node):
    T = TreeNode('base')
    for candidate in list(G.nodes):
        tree_search_rec(G,H,T,candidate,node) 
    k = len(list(H.nodes))
    return extract_matches(T,k)

def tree_search_rec(G,H,T,candidate_node,x):
    x_out_degree = subG.nodes[x]['orig_out_degree'] 
    x_in_degree = subG.nodes[x]['orig_in_degree'] 
    found_x = False
    found_x_nbr = False
    if(candidate_node in T.path_to_root()): # potential nodes count once
        return
    if(G.out_degree[candidate_node]==x_out_degree # check out-degrees
            and G.in_degree[candidate_node]==x_in_degree): # check in-degrees
        for x_nbr in H.successors(x): # check weights of out-edges
            for cand_nbr in G.successors(candidate_node):
                if(G[candidate_node][cand_nbr]['weight']==H[x][x_nbr]['weight']):
                    T.add(candidate_node)
                    tree_search_rec(G,H,T.get(candidate_node),cand_nbr,x_nbr)
        for x_nbr in H.predecessors(x): # check weights of in-edges
            for cand_nbr in G.predecessors(candidate_node):
                if(G[cand_nbr][candidate_node]['weight']==H[x_nbr][x]['weight']):
                    T.add(candidate_node)
                    tree_search_rec(G,H,T.get(candidate_node),cand_nbr,x_nbr)

if __name__ == "__main__":
    if(len(sys.argv)==2 or len(sys.argv)==3 or len(sys.argv)==5):
        G = get_graph_from_csv(sys.argv[1])
        print("Nodes: ",G.number_of_nodes())
        print("Edges: ",G.number_of_edges())
        initial_attacker = sys.argv[2] if len(sys.argv)>2 else random.choice(list(G.nodes))
        while(len(sys.argv)>3 and list(G.neighbors(initial_attacker))==0):
            initial_attacker = random.choice(list(G.nodes))
        coalition = [sys.argv[2], sys.argv[3], sys.argv[4]] if len(sys.argv)==5 else make_coalition(G, initial_attacker, 3)
        print("Initial attacker:")
        print(initial_attacker)
        print("Coalition of 'deanonymizers':")
        print(coalition)
        print("Out degrees:")
        coalition_out = [G.out_degree[x] for x in coalition]
        print(coalition_out)
        print("In degrees:")
        coalition_in = [G.in_degree[x] for x in coalition]
        print(coalition_in)

        known_nodes = coalition
        subG = nx.subgraph(G, known_nodes)
        nx.set_node_attributes(subG, 'orig_out_degree', 0)
        nx.set_node_attributes(subG, 'orig_in_degree', 0)
        for node in list(subG.nodes):
            subG.nodes[node]['orig_out_degree'] = G.out_degree[node]
            subG.nodes[node]['orig_in_degree'] = G.in_degree[node]
        matches = tree_search(G, subG, initial_attacker)
        if(len(matches)==0):
            print("No matches found")
        else:
            if(len(matches)!=1):
                print(len(matches)," matches found")
            else:
                print("Attack Successful, we found ", matches[0])
                compromised_nodes = coalition_neighbors(G, subG)
                if(len(compromised_nodes)>0):
                    print("Potentially compromised ", len(compromised_nodes)," identities!")
                    #print(compromised_nodes)
                else:
                    print("Unable to potentially compromise any identities.")
    else:
        print("""Usage: 
            python file-to-graph.py [csv file to use] [initial attacker]
            python file-to-graph.py [csv file to use] [initial attacker] [coalition member 2] [coalition member 3]""")
