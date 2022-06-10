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
search_criteria_car = arcpy.GetParameterAsText(4).split(";")
NMT_network = arcpy.GetParameterAsText(5)
search_tolerance_NMT = arcpy.GetParameterAsText(6)+" Meters"
search_criteria_NMT = arcpy.GetParameterAsText(7).split(";")

arcpy.AddMessage("> starting\n")

def calc_locations(locations, network,search_tolerance,search_criteria,ND):
    arcpy.AddMessage("> calculate locations for "+ND)

    desc = arcpy.Describe(network)
    crit_network = [i.name for i in desc.sources]
    search_crit = []
    for i in crit_network:
        if i in search_criteria: search_crit.append([i,"Shape"])
        else: search_crit.append([i,"NONE"])

    try: arcpy.DeleteField_management(locations, ["SourceID_"+ND,"SourceOID_"+ND,"PosAlong_"+ND,"SideOfEdge_"+ND,"SnapX_"+ND,"SnapY_"+ND,"Distance_"+ND])
    except: pass

    arcpy.na.CalculateLocations(locations, network, search_tolerance,search_crit,
                    "MATCH_TO_CLOSEST","SourceID_"+ND,"SourceOID_"+ND,"PosAlong_"+ND,"SideOfEdge_"+ND,"SnapX_"+ND,"SnapY_"+ND,"Distance_"+ND)

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
if car_network: calc_locations(places, car_network,search_tolerance_car,search_criteria_car,"MIV")
if NMT_network: calc_locations(places, NMT_network,search_tolerance_NMT,search_criteria_NMT,"NMIV")
arcpy.AddMessage("\n")

#end
arcpy.AddMessage("> finished after "+str(int(time.time()-start_time))+" seconds")