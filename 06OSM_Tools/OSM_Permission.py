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
walkbike_man = bool(arcpy.GetParameterAsText(3)=="true")

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
    tags = [id_field,"Bike","Walk","Bike_man","Walk_man",
                "access","highway","bicycle","foot","service"]
    tags = dict(zip(tags, [*range(0, len(tags))]))
    return tags
    
def permission(data, tags, manual):
    bike = 1
    walk = 1
    #--both--#
    if data[tags["access"]] in ["private","no","permit","private;customers"]:
        bike = 0
        walk = 0
    if data[tags["access"]] == "customers" and data[tags["highway"]] == "service": ##without service == PT-Stops closed
        bike = 0
        walk = 0
    if data[tags["highway"]] in ["motorway","motorway_link","busway","construction","trunk","trunk_link"]:
        bike = 0
        walk = 0
    if data[tags["service"]] in ["parking_aisle"]:
        bike = 0
        walk = 0
    #--bike--#
    if data[tags["bicycle"]] in ["no", "use_sidepath"]:
        bike = 0
    if data[tags["bicycle"]] == "yes":
        bike = 1
    #--walk--#
    if data[tags["foot"]] in ["no", "use_sidepath"]:
        walk = 0
    if data[tags["foot"]] == "yes":
        walk = 1
    #--bike and walk--#
    if walk == 1:
        bike = 1
    
    #--use manual values--#
    if manual == True:
        if data[tags["Walk_man"]] != 9:
            walk = data[tags["Walk_man"]]
        if data[tags["Bike_man"]] != 9:
            bike = data[tags["Bike_man"]]

    data[tags["Bike"]] = bike
    data[tags["Walk"]] = walk

#--editing--#        
osm_tags = osm_dict(osm_id_field)    
field_test(geodata,osm_tags)
with arcpy.da.UpdateCursor(geodata, list(osm_tags.keys())) as cursor:
    for row in cursor:
        permission(row,osm_tags,walkbike_man)
        cursor.updateRow(row)
