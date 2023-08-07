#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name:        OSM Speed
# Purpose:     Speed in (non)motorized transport networks
# Author:      mape
# Created:     07/08/2023
# Copyright:   (c) mape 2023
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
import sys

#--ArcGIS Parameter--#
geodata = arcpy.GetParameterAsText(0)
osm_id_field = arcpy.GetParameterAsText(1)
osm_type = arcpy.GetParameterAsText(2)

def field_test(FC, tags):
    missing = []
    FC_fields = [i.name for i in arcpy.ListFields(FC)]
    for tag in list(tags.keys()):
        if tag not in FC_fields:
            missing.append(tag)
    if len(missing)>0:
        arcpy.AddError("> Fields missing in FeatureClass: "+"; ".join(missing))
        sys.exit()
    else:
        arcpy.AddMessage("> All tags existing")

def osm_dict(id_field):
    tags = [id_field,"vBike","tBike","vWalk","tWalk","Meter",
                "access","highway","bike_osm","walk_osm","service","step_count"]
    tags = dict(zip(tags, [*range(0, len(tags))]))
    return tags
    
def speed(data, tags):
    vbike = 15
    vwalk = 5
    #--push the bike--#
    if data[tags["bike_osm"]] == "no":
        vbike = 4
    if data[tags["highway"]] == "footway":
        vbike = 4
    if data[tags["highway"]] == "steps":
        vbike = 2
        vwalk = 2
    if data[tags["highway"]] == "cycleway":
        vbike = 20
    data[tags["vBike"]] = vbike
    data[tags["vWalk"]] = vwalk
    
def time(id_field, osm_type, data, tags):
    vbike = data[tags["vBike"]]
    vwalk = data[tags["vWalk"]]
    meter = data[tags["Meter"]]
    
    data[tags["tBike"]] = (meter/(vbike/3.6))/60
    data[tags["tWalk"]] = (meter/(vwalk/3.6))/60
    
    #--steps--#
    if data[tags["highway"]] == "steps":
        data[tags["tBike"]] = data[tags["tBike"]]+0.25 #15s to sit on and off
        try:
            data[tags["tBike"]] = data[tags["tBike"]]+(int(data[tags["step_count"]])*(0.85/60))
            data[tags["tWalk"]] = data[tags["tWalk"]]+(int(data[tags["step_count"]])*(0.65/60))
        except:
            data[tags["tBike"]] = data[tags["tBike"]]+0.1
            data[tags["tWalk"]] = data[tags["tWalk"]]+0.1

#--editing--#        
osm_tags = osm_dict(osm_id_field)    
field_test(geodata,osm_tags)
with arcpy.da.UpdateCursor(geodata, list(osm_tags.keys())) as cursor:
    for row in cursor:
        speed(row,osm_tags)
        time(osm_id_field,osm_type,row,osm_tags)
        cursor.updateRow(row)
