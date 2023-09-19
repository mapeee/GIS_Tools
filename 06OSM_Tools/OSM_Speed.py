#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name:        OSM Speed
# Purpose:     Speed in (non-)motorized transport networks
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

global geo_type
geo_type = arcpy.Describe(geodata).ShapeType
arcpy.AddMessage("> Geometry type: "+geo_type)

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

def linktime(id_field, data, tags):
    vbike_FT, vbike_TF = data[tags["vBike_FT"]], data[tags["vBike_TF"]]
    vwalk_FT, vwalk_TF = data[tags["vWalk_FT"]], data[tags["vWalk_TF"]]
    vcar = data[tags["vCar"]]
    meter = data[tags["Shape_Length"]]
    
    data[tags["tBike_FT"]], data[tags["tBike_TF"]] = (meter/(vbike_FT/3.6))/60, (meter/(vbike_TF/3.6))/60
    data[tags["tWalk_FT"]], data[tags["tWalk_TF"]] = (meter/(vwalk_FT/3.6))/60, (meter/(vwalk_TF/3.6))/60
    data[tags["tCar"]] = (meter/(vcar/3.6))/60
    
    #--steps--#
    if data[tags["highway"]] == "steps":
        data[tags["tBike_FT"]], data[tags["tBike_TF"]] = data[tags["tBike_FT"]]+0.25, data[tags["tBike_TF"]]+0.25 #15s to sit on and off
        try:
            data[tags["tBike_FT"]] = data[tags["tBike_FT"]]+(int(data[tags["step_count"]])*(0.85/60))
            data[tags["tBike_TF"]] = data[tags["tBike_TF"]]+(int(data[tags["step_count"]])*(0.85/60))
            data[tags["tWalk_FT"]] = data[tags["tWalk_FT"]]+(int(data[tags["step_count"]])*(0.65/60))
            data[tags["tWalk_TF"]] = data[tags["tWalk_TF"]]+(int(data[tags["step_count"]])*(0.65/60))
        except:
            data[tags["tBike_FT"]], data[tags["tBike_TF"]] = data[tags["tBike_FT"]]+0.1, data[tags["tBike_TF"]]+0.1
            data[tags["tWalk_FT"]], data[tags["tWalk_TF"]] = data[tags["tWalk_FT"]]+0.1, data[tags["tWalk_TF"]]+0.1

def nodetime(data, tags):
    if data[tags["fclass"]] == "traffic_signals": data[tags["tBike"]], data[tags["tWalk"]], data[tags["tCar"]] = 10, 0, 10
    elif data[tags["fclass"]] == "crossing":
        if data[tags["crossing"]] == "traffic_signals": data[tags["tBike"]], data[tags["tWalk"]], data[tags["tCar"]] = 4, 5, 4
        elif data[tags["crossing"]] == "marked": data[tags["tBike"]], data[tags["tWalk"]], data[tags["tCar"]] = 3, 2, 3
        elif data[tags["crossing"]] == "zebra": data[tags["tBike"]], data[tags["tWalk"]], data[tags["tCar"]] = 3, 2, 3 
        else: data[tags["tBike"]], data[tags["tWalk"]], data[tags["tCar"]] = 0, 0, 0 
    else: data[tags["tBike"]], data[tags["tWalk"]], data[tags["tCar"]] = 0, 0, 0

def osm_dict(id_field):
    if geo_type == "Polyline":
        tags = [id_field,"vBike_FT","tBike_FT","vWalk_FT","tWalk_FT","vBike_TF","tBike_TF","vWalk_TF","tWalk_TF","Shape_Length",
                "vCar","tCar",
                "highway","bicycle","foot","step_count","cycleway", "sidewalk", "bike_l", "bike_r", "surface", "maxspeed",
                "walk_l", "walk_r", "town"]
    if geo_type == "Point":
        tags = [id_field, "tBike", "tWalk", "tCar", "fclass", "crossing"]
    tags = dict(zip(tags, [*range(0, len(tags))]))
    return tags
    
def speed(data, tags):
    vbike = [17, 17]
    vwalk = [4.8, 4.8]
    
    #--maxspeed car--#
    if data[tags["maxspeed"]] == 0 and data[tags["town"]] == 0:
        try: vcar = {'motorway': 120, 'tertiary': 70, 'secondary': 80, 'residential': 25,
                     'motorway_link': 50,'trunk_link': 40,'primary_link': 40, 'primary': 100}[data[tags["highway"]]]
        except: vcar = 15
    elif data[tags["maxspeed"]] == 0 and data[tags["town"]] == 1:
        try: vcar = {'motorway': 80, 'tertiary': 40, 'secondary': 45, 'residential': 25,
                     'motorway_link': 40,'trunk_link': 30,'primary_link': 30, 'primary': 50}[data[tags["highway"]]]
        except: vcar = 15
    else: vcar = data[tags["maxspeed"]]
    
    #--highway--#
    if data[tags["highway"]] in ["footway", "pedestrian"]: vbike, vwalk = [4,4], [5,5]
    if data[tags["highway"]] == "steps": vbike, vwalk = [2,2], [2,2]
    if data[tags["highway"]] == "cycleway": vbike, vwalk = [20,20], [3,3]
    #--bicycle / foot--"
    if data[tags["bicycle"]] in ["no", "use_sidepath"]: vbike = [4,4]
    if data[tags["bicycle"]] == "designated": vbike[0], vbike[1] = max(vbike[0], 18), max(vbike[1], 18)
    if data[tags["bicycle"]] == "yes" and data[tags["highway"]] in ["footway", "pedestrian"]: vbike[0], vbike[1] = max(vbike[0], 10), max(vbike[1], 10)
    if data[tags["bicycle"]] == "yes" and data[tags["highway"]] not in ["footway", "pedestrian"]: vbike[0], vbike[1] = max(vbike[0], 17), max(vbike[1], 17)
    if data[tags["foot"]] in ["no", "use_sidepath"]: vwalk = [3,3]
    #--cycleway / sidewalk--#
    if data[tags["cycleway"]] in ["lane", "cyclestreet", "track", "sidepath"]: vbike[0], vbike[1] = max(vbike[0], 18.5), max(vbike[1], 18.5)
    if data[tags["cycleway"]] == "opposite": vbike = [17,12]
    if data[tags["cycleway"]] == "share_busway": vbike = [15,15]
    if data[tags["sidewalk"]] in ["no", "use_sidepath", "none", "separate"]: vwalk[0], vwalk[1] = min(vwalk[0], 3), min(vwalk[1], 3)
    #--cycleway:right / cycleway:left--#
    if data[tags["bike_r"]] in ["lane", "track"]: vbike[0] = max(vbike[0], 18.5)
    if data[tags["bike_r"]] == "share_busway": vbike[0] = min(vbike[0], 15)
    if data[tags["bike_r"]] in ["opposite", "separate"]: vbike[0] = min(vbike[0], 4)
    if data[tags["bike_l"]] in ["lane", "track"]: vbike[0] = max(vbike[0], 18.5)
    if data[tags["bike_l"]] == "share_busway": vbike[1] = min(vbike[1], 15)
    if data[tags["bike_l"]] in ["no", "opposite", "separate"]: vbike[1] = min(vbike[1], 4)
    #--sidewalk:right / sidewalk:left--#
    if data[tags["walk_r"]] in ["no", "separate"]: vwalk[0] = min(vwalk[0], 3)
    if data[tags["walk_l"]] in ["no", "separate"]: vwalk[1] = min(vwalk[1], 3)
    vwalk[0], vwalk[1] = max(vwalk), max(vwalk)
    #--surface--#
    if data[tags["surface"]] in ["asphalt", "concrete"]: vbike[0], vbike[1], vcar = vbike[0]*1.05, vbike[1]*1.05, vcar*1.05
    if data[tags["surface"]] in ["compacted"]: vbike[0], vbike[1], vcar = vbike[0]*0.95, vbike[1]*0.95, vcar*0.95
    if data[tags["surface"]] in ["ground", "unpaved", "pebblestone", "gravel"]: vbike[0], vbike[1], vcar = vbike[0]*0.9, vbike[1]*0.9, vcar*0.9
    if data[tags["surface"]] in ["dirt", "grass", "cobblestone", "earth"]: vbike[0], vbike[1], vcar = vbike[0]*0.85, vbike[1]*0.85, vcar*0.85
    if data[tags["surface"]] in ["mud", "sand"]: vbike[0], vbike[1], vcar = vbike[0]*0.7, vbike[1]*0.7, vcar*0.7
    #--car--#
    if vcar > 70: vcar = max(vcar*0.85,70)
    
    data[tags["vBike_FT"]], data[tags["vBike_TF"]] = vbike[0], vbike[1]
    data[tags["vWalk_FT"]], data[tags["vWalk_TF"]] = vwalk[0], vwalk[1]
    data[tags["vCar"]] = vcar

#--editing--#        
osm_tags = osm_dict(osm_id_field)    
field_test(geodata,osm_tags)
with arcpy.da.UpdateCursor(geodata, list(osm_tags.keys())) as cursor:
    for row in cursor:
        if geo_type == "Polyline":
            speed(row,osm_tags)
            linktime(osm_id_field,row,osm_tags)
        if geo_type == "Point":
            nodetime(row,osm_tags)
        cursor.updateRow(row)
