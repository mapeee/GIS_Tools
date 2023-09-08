#-------------------------------------------------------------------------------
# Name:        Prepare places
# Purpose:     Prepace the places for usage concerning accessibility tools
# Author:      mape
# Created:     20.04.2022
# Copyright:   (c) peter 2022
#-------------------------------------------------------------------------------

import arcpy
import collections
import time
start_time = time.time()

#--ArcGIS Parameter--#
places = arcpy.GetParameterAsText(0)
ID_corr = bool(arcpy.GetParameterAsText(1)=="true")
car_network = arcpy.GetParameterAsText(2)
search_tolerance_car = arcpy.GetParameterAsText(3)+" Meters"
NMT_network = arcpy.GetParameterAsText(4)
search_tolerance_NMT = arcpy.GetParameterAsText(5)+" Meters"

arcpy.AddMessage("> starting\n")

def calc_locations(locations, network,search_tolerance,ND):
    search_params(network,ND)
    arcpy.AddMessage("> calculate locations for "+ND)

    try: arcpy.DeleteField_management(locations, ["SourceID_"+ND,"SourceOID_"+ND,"PosAlong_"+ND,"SideOfEdge_"+ND,"SnapX_"+ND,
                                                  "SnapY_"+ND,"DistanceToNetworkInMeters_"+ND])
    except: pass

    arcpy.na.CalculateLocations(locations, network, search_tolerance,search_crit,
                    "MATCH_TO_CLOSEST","SourceID_"+ND,"SourceOID_"+ND,"PosAlong_"+ND,"SideOfEdge_"+ND,"SnapX_"+ND,
                    "SnapY_"+ND,"DistanceToNetworkInMeters_"+ND,search_query=search_query,travel_mode=travel_mode)

def search_params(Net,mod):
    global search_crit
    search_crit = []
    desc = arcpy.Describe(Net)
    for i in desc.edgeSources:search_crit.append([i.name,"SHAPE"])
    for i in desc.junctionSources:search_crit.append([i.name,"NONE"])
    
    global search_query
    if mod == "NMT": search_query = [["MRH_Links", "(bridge = 'F' and tunnel = 'F') or (tunnel = 'T' and access = 'customers')"]]
    elif mod == "MT": search_query = [["MRH_Links", "(bridge = 'F' and tunnel = 'F')"]]
    else: search_query = ""
    
    global travel_mode
    if mod == "NMT": travel_mode = "Walking"
    else: travel_mode = "Car"

#--ID Field--#
if ID_corr == True:
    arcpy.AddMessage("> correcting 'ID' Field")
    field_names = [f.name for f in arcpy.ListFields(places)]
    if "ID" in field_names:
        arcpy.AddMessage("> 'ID' Field still existing")
        values = [row[0] for row in arcpy.da.SearchCursor(places, ["ID"])]
        if 0 in values:arcpy.AddMessage("> 'ID' Field including '0' value!")
        if None in values: arcpy.AddMessage("> 'ID' Field including 'None' value!")

        duplicates = [item for item, count in collections.Counter(values).items() if count > 1]
        if len(duplicates) > 0: arcpy.AddMessage("> duplicate values: "+str(duplicates))

        arcpy.AddMessage("\n")

    else:
        arcpy.AddMessage("> adding 'ID' Field")
        arcpy.DeleteField_management(places,"id")
        arcpy.AddField_management(places,"ID","LONG")
        n = 1
        with arcpy.da.UpdateCursor(places, ["ID"]) as cursor:
            for row in cursor:
                row[0] = n
                n+=1
                cursor.updateRow(row)

#--calculate locations--#
if car_network: calc_locations(places, car_network,search_tolerance_car,"MT")
if NMT_network: calc_locations(places, NMT_network,search_tolerance_NMT,"NMT")
arcpy.AddMessage("\n")

#end
arcpy.AddMessage("> finished after "+str(int(time.time()-start_time))+" seconds")