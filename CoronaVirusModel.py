from City import City
import networkx as nx
import matplotlib.pyplot as plt
import osmnx as ox



city = City('Ketchum, Idaho, USA', 10)
city.run_seir(20)
infected_nodes =[]
removed_nodes=[]
for node in city.network.nodes(data=True):
    if (node[1]['state']) == "Infected":
        infected_nodes.append(node[0])
    elif (node[1]['state']) == "Removed":
        removed_nodes.append(node[0])

nc = []
for node in city.network.nodes():
    if node in infected_nodes:
        nc.append('r')
    elif node in removed_nodes:
        nc.append('b')
    else:
        nc.append('g')

ox.plot_graph(city.network, node_color=nc)