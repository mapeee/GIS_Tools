#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name: OSM Tags
# Purpose: Adding Info from OSM Tags to Shape file
# Author:      mape
# Created:     31/07/2023
# Copyright:   (c) mape 2023
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
import overpy
import sys

#--ArcGIS Parameter--#
geodata = arcpy.GetParameterAsText(0)
osm_id_field = arcpy.GetParameterAsText(1)
osm_type = arcpy.GetParameterAsText(2)
osm_tags = arcpy.GetParameterAsText(3).split(";")

def add_tags(FC, osmTags):
    tags_list = [["access","access","TEXT"],
            ["area","area","TEXT"],
            ["bicycle","bicycle","TEXT"],
            ["cycleway:left","bike_l","TEXT"],
            ["cycleway:right","bike_r","TEXT"],
            ["cycleway","cycleway","TEXT"],
            ["foot","foot","TEXT"],
            ["highway","highway","TEXT"],
            ["service","service","TEXT"],
            ["sidewalk:left","walk_l","TEXT"],
            ["sidewalk:right","walk_r","TEXT"],
            ["sidewalk", "sidewalk", "TEXT"],
            ["smoothness","smoothness","TEXT"],
            ["surface","surface","TEXT"],
            ["step_count","step_count","TEXT"]]
    
    FC_fields = [i.name for i in arcpy.ListFields(FC)]
    FCTags = []
    for tag in tags_list:
        if tag[0] in osmTags:
            if tag[1] in FC_fields:
                arcpy.AddMessage("> Field "+tag[1]+": existing")
                osmTags.remove(tag[0])
            else:
                arcpy.management.AddField(FC, tag[1], tag[2])
                arcpy.AddMessage("> Field "+tag[1]+": added") 
                FCTags.append(tag[1])
    
    if len(osmTags)==0:
        arcpy.AddError("> No new fields to add values")
        sys.exit()
        
    return [osmTags, FCTags]
                               
def List_osm_id(FC, osmID):
    List = [int(i[0]) for i in arcpy.da.FeatureClassToNumPyArray(FC, (osmID))]
    return List

def overpass_api(osmType, osmIDs):
    osmIDs = [str(x) for x in osmIDs]
    string_osm_IDs = ', '.join(osmIDs)
    query_api = osmType+"(id:"+string_osm_IDs+"); (._;>;); out body;"
    result = overpy.Overpass().query(query_api)
    return result

def write_data(FC, osmID, osmTags, osmType, FCrows):
    rows = 0
    with arcpy.da.UpdateCursor(FC, [osmID]+osmTags[1]) as cursor:
        for row in cursor:
            if FCrows[0] <= rows and FCrows[1]-1 >=rows:
                osmNo = int(row[0])
                for e, tag in enumerate(osmTags[0]):
                    if osmType == "way":
                        try: row[e+1] = str(osm_data.get_way(osmNo).tags.get(tag, "n/a"))
                        except: row[e+1] = "osm_id missing"
            
            cursor.updateRow(row)
            rows+=1
    
osm_tags = add_tags(geodata,osm_tags)
osm_IDs = List_osm_id(geodata, osm_id_field)

for i in range(int(len(osm_IDs)/5000)+1):
    arcpy.AddMessage("> Bunch "+str(i+1)+" / "+str(int(len(osm_IDs)/5000)+1))
    FC_rows = [i*5000, (i+1)*5000]
    osm_data = overpass_api(osm_type, osm_IDs[FC_rows[0]:FC_rows[1]])
    write_data(geodata, osm_id_field, osm_tags, osm_type, FC_rows)
    
