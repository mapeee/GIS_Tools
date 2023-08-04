#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name: OSM Info
# Purpose: Giving Info of OSM Tags in ArcGIS Message
# Author:      mape
# Created:     28/07/2023
# Copyright:   (c) mape 2023
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
import overpy

#--ArcGIS Parameter--#
osmID = int(arcpy.GetParameterAsText(0))
osm_type = arcpy.GetParameterAsText(1)

def result_api(osmID, osm_type):
    query_api = osm_type+"(id:"+str(osmID)+"); (._;>;); out body;"
    result = overpy.Overpass().query(query_api)
    return result

def result_print(osmID, osm_type):
    result = result_api(osmID, osm_type)
    if osm_type == "way":
        for tag in result.get_way(osmID).tags:
            value = result.get_way(osmID).tags.get(tag, "n/a")
            arcpy.AddMessage(tag+": "+value)

result_print(osmID, osm_type)