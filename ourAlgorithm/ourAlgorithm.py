import networkx as nx
import csv
import sys
import random

source_i = 0
dest_i = 1
wght_i = 2

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

def get_n_subgraph_nodes(G,node,n):
    subgraphNodes = [node]
    if(n==0):
        return subgraphNodes
    neighbors = list(G.neighbors(node))
    for neighbor in neighbors:
        neighbor_nodes = get_n_subgraph_nodes(G,neighbor,n-1)
        subgraphNodes.extend(neighbor_nodes)
    return subgraphNodes

def get_n_subgraph(G,node,n):
    subgraphNodes = get_n_subgraph_nodes(G,node,n)
    return nx.subgraph(G, subgraphNodes)

def do_neighborhoods_match(subG, node, candidate_subG, candidate):
    if(subG.out_degree[node]==0):
        # Base case: every neighbor of node found a match with a neighbor of candidate
        return True
    for node_neighbor in list(subG.neighbors(node)):
        for cand_neighbor in list(candidate_subG.neighbors(candidate)):
            if(subG.out_degree[node_neighbor]==candidate_subG.out_degree[cand_neighbor]):
                # Remove potential 'match' and check the rest
                subG_copy = subG.copy()
                subG_copy.remove_node(node_neighbor)

                cand_subG_copy = candidate_subG.copy()
                cand_subG_copy.remove_node(cand_neighbor)

                if(do_neighborhoods_match(subG_copy, node, cand_subG_copy, candidate)):
                    return True
    return False

def coalition_neighbors(G,coalition_nodes):
    neighbors = []
    for node in coalition_nodes:
        neighbors.extend(list(G.neighbors(node)))
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

# Counting only 'out-edges' 
def brute_force_deanonymize(G, subG, node):
    matches_in_g = []
    node_degree = subG.out_degree[node] 
    for candidate in list(G.nodes):
        if(G.out_degree[candidate]==node_degree):
            candidate_neighborhood = get_n_subgraph(G,candidate,2)
            if(do_neighborhoods_match(subG, node, candidate_neighborhood, candidate)):
                matches_in_g.append(candidate)
    return matches_in_g

if __name__ == "__main__":
    if(len(sys.argv)==2 or len(sys.argv)==3):
        G = get_graph_from_csv(sys.argv[1])
        print("Nodes: ",G.number_of_nodes())
        print("Edges: ",G.number_of_edges())
        initial_attacker = sys.argv[2] if len(sys.argv)==3 else random.choice(list(G.nodes))
        coalition = make_coalition(G, initial_attacker, 3)
        print("Coalition of 'deanonymizers':")
        print(coalition)
        known_nodes = coalition
        known_nodes.extend(coalition_neighbors(G,coalition))
        chosen_node = node_with_max_degree(G,known_nodes) # <-- potential for choosing the 'optimal' node here, may not be biggest degree
        subG = nx.subgraph(G, known_nodes)
        matches = brute_force_deanonymize(G, subG, chosen_node)
        if(len(matches)==0):
            print("No matches found")
        else:
            if(len(matches)!=1):
                print(len(matches)," matches found")
            else:
                print("Attack Successful, we found ", matches[0])
                compromised_nodes = coalition_neighbors(G, subG)
                if(len(compromised_nodes)>0):
                    print("Compromised ", len(compromised_nodes)," identities!")
                    #print(compromised_nodes)
                else:
                    print("Unable to compromise any identities.")
    else:
        print("Usage: python file-to-graph.py [filename] [node to check (if any)]")
