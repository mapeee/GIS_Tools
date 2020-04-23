# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 14:51:45 2020

@author: marcus
"""

import pandas as pd
from qgis.core import QgsDistanceArea, QgsPointXY
distance = QgsDistanceArea()


def sj(in_data, join_data,in_x,in_y,join_x,join_y,id_in, id_join,max_value,**optional):
    final_tab = []
    try:
        optional["name_in"]
        name_out = True
    except KeyError:name_out = False

    for index_in, row_in in in_data.iterrows():
        if name_out is True: dist = [1000000,0,"",0,""]
        else: dist = [1000000,0,0]
        
        for index_join, row_join in join_data.iterrows():
            point1 = QgsPointXY(row_in[in_x],row_in[in_y])
            point2 = QgsPointXY(row_join[join_x],row_join[join_y])
            d = distance.measureLine(point1, point2)
            if d < dist[0] and d <= max_value:
                if name_out is True:dist = [round(d,3),row_in[id_in],row_in[optional["name_in"]],
                                            row_join[id_join],row_join[optional["name_join"]]]
                else: dist = [round(d,3),row_in[id_in],row_join[id_join]]
        final_tab.extend([dist])
      
    if name_out is True: final_tab = pd.DataFrame(final_tab, columns=["dist",id_in, optional["name_in"],
                                                                      id_join, optional["name_join"]])
    else: final_tab = pd.DataFrame(final_tab, columns=["dist",id_in, id_join])

    return final_tab


def sj_sum(in_data, join_data,in_x,in_y,join_x,join_y,id_in,max_value,value_join,**optional):
    final_tab = []
    try:
        optional["name_in"]
        name_out = True
    except KeyError:name_out = False
    
    for index_in, row_in in in_data.iterrows():        
        value = 0
        for index_join, row_join in join_data.iterrows():
            point1 = QgsPointXY(row_in[in_x],row_in[in_y])
            point2 = QgsPointXY(row_join[join_x],row_join[join_y])
            d = distance.measureLine(point1, point2)
            if d <= max_value: value+=row_join[value_join]
    
        if name_out is True: final_tab.extend([[row_in[id_in],row_in[optional["name_in"]],value]])
        else: final_tab.extend([[row_in[id_in],value]])
      
    if name_out is True: final_tab = pd.DataFrame(final_tab, columns=[id_in, optional["name_in"],value_join])
    else: final_tab = pd.DataFrame(final_tab, columns=[id_in,value_join])

    return final_tab