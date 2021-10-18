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

# networkx to igraph
from functools import reduce
import geopandas as gpd
import matplotlib.pyplot as plt
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
def linknodenetwork(Network,draw):
    links = gpd.read_file(Network)
    nodes = links.apply(lambda x: [y for y in x['geometry'].coords], axis=1).values.flatten()
    nodes = np.array(reduce(lambda x, y: x+y, nodes))
    if draw == 1: links.to_crs(epsg=epsg).plot()
    return links, nodes

def graphs(links,epsg):
    graph = momepy.gdf_to_nx(links.to_crs(epsg=epsg), directed=True, length = 'Shape_Leng')
    G = nx.Graph(crs="EPSG:"+str(epsg))
    return graph, G

def addNode(xy_node, nodes, links, graph, v_add):
    dist,i = spatial.KDTree(nodes).query(xy_node)
    near = nodes[i]    
    k = links[links.apply(lambda row: near[0] in row.geometry.coords.xy[0] 
                          and near[1] in row.geometry.coords.xy[1],axis=1)].index[0]
    x,y = links.iloc[k].geometry.coords.xy
    v = float((links.iloc[k].vPkw)*0.9) ##due to loaded network and possibly detour

    #--add nodes and links--#
    graph.add_node(xy_node)
    pos_xy_node = len(graph.nodes)-1 ##-1 for index
    if near[0] != x[0] and near[0] != x[-1]:
        graph.add_node((near[0],near[1]))
        
        dist1 = spatial.distance.cdist([(x[0],y[0])], [(near[0],near[1])], 'euclidean')[0][0]
        graph.add_edge((x[0],y[0]),(near[0],near[1]),tAkt=(dist1/(v/float(3.6)))/60)
        
        dist2 = spatial.distance.cdist([(x[-1],y[-1])], [(near[0],near[1])], 'euclidean')[0][0]
        graph.add_edge((x[-1],y[-1]),(near[0],near[1]),tAkt=(dist2/(v/float(3.6)))/60)
        
    graph.add_edge((xy_node),(near[0],near[1]),tAkt=(dist/(v_add/float(3.6)))/60)
    
    return (xy_node,pos_xy_node)

def buildnetwork(graph,G,draw,impe):
    pos = {k: v for k,v in enumerate(graph.nodes())}
    G.add_nodes_from(pos.keys()) #Add nodes preserving coordinates
    #--links--#
    pos_df = pd.DataFrame.from_dict(pos,orient='index')
    for data in graph.edges(data=True):
        x = pos_df.loc[(pos_df[0] == data[0][0]) & (pos_df[1] == data[0][1])].index[0]
        y = pos_df.loc[(pos_df[0] == data[1][0]) & (pos_df[1] == data[1][1])].index[0]
        G.add_edge(x,y,tAkt=data[2][impe])
    if draw == 1: nx.draw(G,pos, node_size=10, node_color='red')
    return pos

def routeaccurate(G,orig,desti,impe):
    route = nx.shortest_path(G=G, source=orig[1], target=desti[1], weight=impe)
    return route

def routesimple(graph,G,orig,desti,impe):
    pos = buildnetwork(graph,G,draw=0,impe=impedance)
    nodes = np.array(graph.nodes())
    distance_s,index_s = spatial.KDTree(nodes).query(orig)
    distance_t,index_t = spatial.KDTree(nodes).query(desti)

    route = nx.shortest_path(G=G, source=index_s, target=index_t, weight=impe)
    return route, pos

def printroute(route,pos,col):
    path_edges = zip(route,route[1:])
    path_edges = set(path_edges)
    nx.draw_networkx_nodes(G,pos,node_size=6,node_color='black')
    nx.draw_networkx_edges(G,pos,edge_color='grey',width=1)
    nx.draw_networkx_nodes(G,pos,nodelist=route,node_color='green',node_size=8)
    nx.draw_networkx_edges(G,pos,edgelist=path_edges,edge_color=col,width=2,style='--',arrows=False)
    plt.show()

##########################
# path and parameters
##########################
path = open(Path.home() / 'python32' / 'python_dir.txt', mode='r').readlines()[0]
f = Path.joinpath(Path(path),'GIS_Tools','Networkx.txt').read_text().split('\n')
Network = f[0]
Locations = gpd.read_file(f[1])
epsg = 25832
impedance = "tAkt"
method = "accurate"

##########################
# initial network
##########################
links, nodes = linknodenetwork(Network,draw=0)
graph, G = graphs(links,epsg)

##########################
# Routes
##########################
# orig = (645855.629,5956835.576)
# desti = (638129.780,5954136.820)


####################
buildnetwork(graph,G,draw=0,impe=impedance)
# length, path = nx.multi_source_dijkstra(G, {14000},weight= impedance)
# length = nx.multi_source_dijkstra_path_length(G, {12000, 14000},weight= impedance)
start_time = time.time()
for p in range(12000,12100):length, path = nx.multi_source_dijkstra(G, {p},weight= impedance)
print(round((time.time() - start_time),1),"seconds--")

import igraph as ig
g = ig.Graph.from_networkx(G)
# path = g.get_shortest_paths(1,1000,mode="out",weights=impedance,output="epath")
# sum(g.es[path[0]][impedance])
start_time = time.time()
for p in range(12000,12100):path = g.get_all_shortest_paths(p, to=None, weights=impedance, mode='out')
print(round((time.time() - start_time),1),"seconds--")

route = nx.shortest_path(G=G, source=1, target=1000, weight=impedance)
print("impedance: "+str(round(path_weight(G=G, path=route, weight=impedance),1)))
#####################



orig = (Locations.iloc[0].geometry.coords.xy[0][0],Locations.iloc[0].geometry.coords.xy[1][0])
desti = (Locations.iloc[33].geometry.coords.xy[0][0],Locations.iloc[33].geometry.coords.xy[1][0])


if method == "simple":
    route, pos = routesimple(graph,G,orig,desti,impe=impedance)
    print("impedance: "+str(round(path_weight(G=G, path=route, weight=impedance),1)))
    printroute(route,pos,col="blue")

if method == "accurate":
    orig = addNode(orig, nodes, links, graph, v_add=50)
    desti = addNode(desti, nodes, links, graph, v_add=50)
    pos = buildnetwork(graph,G,draw=0,impe=impedance)
    
    route = routeaccurate(G,orig,desti,impe=impedance)
    print("impedance: "+str(round(path_weight(G=G, path=route, weight=impedance),1)))
    printroute(route,pos,col="red")

##########################
# End
##########################
Sekunden = round((time.time() - start_time),2)
print("--finished after ",Sekunden,"seconds--")