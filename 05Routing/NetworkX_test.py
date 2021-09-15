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
from functools import reduce
import geopandas as gpd
import momepy
import networkx as nx
from networkx.classes.function import path_weight
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import spatial
import time
start_time = time.time()

##########################
# Functions
##########################
def addNode(xy_node, nodes, links, graph):
    dist,i = spatial.KDTree(nodes).query(xy_node)
    near = nodes[i]    
    k = links[links.apply(lambda row: near[0] in row.geometry.coords.xy[0] 
                          and near[1] in row.geometry.coords.xy[1],axis=1)].index[0]
    x,y = links.iloc[k].geometry.coords.xy
    v = float((links.iloc[k].vPkw)*0.9) ##due to loaded network

    #--add nodes and links--#
    graph.add_node(xy_node)
    if near[0] != x[0] and near[0] != x[-1]:
        graph.add_node((near[0],near[1]))
        
        dist1 = spatial.distance.cdist([(x[0],y[0])], [(near[0],near[1])], 'euclidean')[0][0]
        graph.add_edge((x[0],y[0]),(near[0],near[1]),tAkt=(dist1/(v/float(3.6)))/60)
        
        dist2 = spatial.distance.cdist([(x[-1],y[-1])], [(near[0],near[1])], 'euclidean')[0][0]
        graph.add_edge((x[-1],y[-1]),(near[0],near[1]),tAkt=(dist2/(v/float(3.6)))/60)
        
    graph.add_edge((xy_node),(near[0],near[1]),tAkt=(dist/(5/float(3.6)))/60)

##########################
# path
##########################
path = open(Path.home() / 'python32' / 'python_dir.txt', mode='r').readlines()[0]
f = Path.joinpath(Path(path),'GIS_Tools','Networkx.txt').read_text().split('\n')

Network = f[0]

##########################
# Import Graph
##########################
links = gpd.read_file(Network)
# links.to_crs(epsg=25832).plot()
#--build graphs--#
graph = momepy.gdf_to_nx(links.to_crs(epsg=25832), directed=True, length = 'Shape_Leng')
G = nx.Graph(crs="EPSG:25832")

nodes = links.apply(lambda x: [y for y in x['geometry'].coords], axis=1).values.flatten()
nodes = np.array(reduce(lambda x, y: x+y, nodes))

##########################
# Adding nodes
##########################
orig = (645855.629,5956835.576)
desti = (638129.780,5954136.820)

addNode(orig, nodes, links, graph)
addNode(desti, nodes, links, graph)

##########################
# Build network
##########################
#--nodes--#
pos = {k: v for k,v in enumerate(graph.nodes())}
G.add_nodes_from(pos.keys()) #Add nodes preserving coordinates
#--links--#
pos_df = pd.DataFrame.from_dict(pos,orient='index')
for data in graph.edges(data=True):
    x = pos_df.loc[(pos_df[0] == data[0][0]) & (pos_df[1] == data[0][1])].index[0]
    y = pos_df.loc[(pos_df[0] == data[1][0]) & (pos_df[1] == data[1][1])].index[0]
    G.add_edge(x,y,tAkt=data[2]['tAkt'])
nx.draw(G,pos, node_size=10, node_color='red')

##########################
# route
##########################
start = [645855.629,5956835.576]
target = [638129.780,5954136.820]
# nodes = np.array(graph.nodes())
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


Sekunden = int(time.time() - start_time)
print("--finished after ",Sekunden,"seconds--")