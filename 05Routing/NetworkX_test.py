# -*- coding: cp1252 -*-
#!/usr/bin/python

#-------------------------------------------------------------------------------
# Name:        Shortest path without ArcGIS
# Purpose:
#
# Author:      mape
#
# Created:     27/07/2021
# Copyright:   (c) mape 2021
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# to try : Graph-tool
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy import spatial
import momepy
from networkx.classes.function import path_weight
import matplotlib.pyplot as plt
import time
start_time = time.time()

from pathlib import Path
f = open(Path.home() / 'python32' / 'python_dir.txt', mode='r')
for i in f: path = i
path = Path.joinpath(Path(path),'GIS_Tools','Networkx.txt')
f = path.read_text().split('\n')

#--Path--#
Network = f[0]

# import data from Shape
links = gpd.read_file(Network)
links = links.to_crs(epsg=25832)
links.plot()

# using momepy to build the graph
graph = momepy.gdf_to_nx(links, directed=True, length = 'Shape_Leng')
G = nx.Graph(crs="EPSG:25832")
pos = {k: v for k,v in enumerate(graph.nodes())}
G.add_nodes_from(pos.keys()) #Add nodes preserving coordinates
pos_df = pd.DataFrame.from_dict(pos,orient='index')

for data in graph.edges(data=True):
    x = pos_df.loc[(pos_df[0] == data[0][0]) & (pos_df[1] == data[0][1])].index[0]
    y = pos_df.loc[(pos_df[0] == data[1][0]) & (pos_df[1] == data[1][1])].index[0]
    G.add_edge(x,y,tAkt=data[2]['tAkt'])

##########################
# graphic output
##########################
nx.draw(graph)
nx.draw(G,pos)
f, ax = plt.subplots(figsize=(10, 10))
links.plot(ax=ax)
ax.set_axis_off()
plt.show()

f, ax = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)
links.plot(color='#e32e00', ax=ax[0])
for i, facet in enumerate(ax):
    facet.set_title(("Streets", "Primal graph", "Overlay")[i])
    facet.axis("off")
nx.draw(graph, {n:[n[0], n[1]] for n in list(graph.nodes)}, ax=ax[1], node_size=15)
links.plot(color='#e32e00', ax=ax[2], zorder=-1)
nx.draw(graph, {n:[n[0], n[1]] for n in list(graph.nodes)}, ax=ax[2], node_size=15)
degree = momepy.node_degree(graph, name='degree')

nodes, edges, sw = momepy.nx_to_gdf(degree, points=True, lines=True,
                                    spatial_weights=True)

f, ax = plt.subplots(figsize=(10, 10))
nodes.plot(ax=ax, column='degree', cmap='tab20b', markersize=(nodes['degree'] * 100), zorder=2)
edges.plot(ax=ax, color='lightgrey', zorder=1)
ax.set_axis_off()
plt.show()

##########################
# route
##########################

#testing to add new links for better representation of addlocations
pos[106] = (645855.629,5956835.576)
pos[107] = (638129.780,5954136.820)
# --> then build new graph


start = [645855.629,5956835.576]
target = [638129.780,5954136.820]
nodes = np.array(graph.nodes())
nodes[spatial.KDTree(nodes).query(start)[1]]
distance_s,index_s = spatial.KDTree(nodes).query(start)
distance_t,index_t = spatial.KDTree(nodes).query(target)

route = nx.shortest_path(G=G, source=index_s, target=index_t, weight='tAkt')
print(str(28)+" -- "+str(96)+": "+str(path_weight(G=G, path=route, weight="tAkt")))

path_edges = zip(route,route[1:])
path_edges = set(path_edges)
nx.draw_networkx_nodes(G,pos,node_size=10,node_color='black')
nx.draw_networkx_edges(G,pos,edge_color='grey',width=1)
nx.draw_networkx_nodes(G,pos,nodelist=route,node_color='blue',node_size=10)
nx.draw_networkx_edges(G,pos,edgelist=path_edges,edge_color='blue',width=3)


##########################
# Import network-data from OSM
##########################
place_name = "Sternschanze, Hamburg, Germany"
graph = ox.graph_from_place(place_name, network_type='drive', simplify=False)
graph_proj = ox.projection.project_graph(graph, "EPSG:25832") #CRS = EPSG:25832
nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj, nodes=True, edges=True)
buildings = ox.geometries_from_place(place_name, tags={'building':True})
buildings_proj = buildings.to_crs("EPSG:25832")

# project into metric system
fig, ax = ox.plot_graph(graph_proj)
base = buildings_proj.plot(facecolor='red', alpha=0.7)
edges_proj.plot(linewidth=0.7, color='gray', ax=base)

# Calculate the shortest path
found = 0
error = 0
for orig in nodes_proj.index:
    if found > 5000:break
    for dest in nodes_proj.index:
        try: route = nx.shortest_path(G=graph_proj, source=orig, target=dest, weight='length')
        except: 
            error+=1
            continue
        # print(str(orig)+" -- "+str(dest)+": "+str(path_weight(G=graph_proj, path=route, weight="length")))
        # fig, ax = ox.plot_graph_route(graph_proj, route)      
        found+=1


Sekunden = int(time.time() - start_time)
print("--finished after ",Sekunden,"seconds--")