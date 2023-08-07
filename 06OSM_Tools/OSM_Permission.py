#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name:        OSM Permission
# Purpose:     Permission (non)motorized transport on networks
# Author:      mape
# Created:     04/08/2023
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
    tags = [id_field,"Bike","Walk",
                "access","highway","bike_osm","walk_osm","service"]
    tags = dict(zip(tags, [*range(0, len(tags))]))
    return tags
    
def permission(data, tags):
    bike = 1
    walk = 1
    #--both--#
    if data[tags["access"]] in ["private","customers","no","permit","private;customers"]:
        bike = 0
        walk = 0
    if data[tags["highway"]] in ["motorway","motorway_link","busway","construction","trunk","trunk_link"]:
        bike = 0
        walk = 0
    if data[tags["service"]] in ["parking_aisle"]:
        bike = 0
        walk = 0
    #--bike--#
    if data[tags["bike_osm"]] == "no":
        bike = 0
    if data[tags["bike_osm"]] == "yes":
        bike = 1
    #--walk--#
    if data[tags["walk_osm"]] == "no":
        walk = 0
    if data[tags["walk_osm"]] == "yes":
        walk = 1
    #--bike and walk--#
    if walk == 1:
        bike = 1

    data[tags["Bike"]] = bike
    data[tags["Walk"]] = walk

#--editing--#        
osm_tags = osm_dict(osm_id_field)    
field_test(geodata,osm_tags)
with arcpy.da.UpdateCursor(geodata, list(osm_tags.keys())) as cursor:
    for row in cursor:
        permission(row,osm_tags)
        cursor.updateRow(row)
