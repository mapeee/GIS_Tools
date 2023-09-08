#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name:        Next_Stops
# Purpose:     Connecting places to next stops in a network
# Author:      mape
# Created:     02/09/2015 (new Version 2021)
# Copyright:   (c) mape 2015
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
from datetime import date
import h5py
import numpy as np
import time
start_time = time.time()
 
arcpy.CheckOutExtension("Network")

#--GIS Parameters--#
Places = arcpy.GetParameterAsText(0)
Places_ID = arcpy.GetParameterAsText(1)
Stops = arcpy.GetParameterAsText(2)
Stops_ID = arcpy.GetParameterAsText(3)
Database = arcpy.GetParameterAsText(4)
Group = arcpy.GetParameterAsText(5)
Network = arcpy.GetParameterAsText(6)
Mode = arcpy.GetParameterAsText(7)
ToFind = arcpy.GetParameterAsText(8)
Result_table = arcpy.GetParameterAsText(9)
MaxCosts = arcpy.GetParameterAsText(10)
TrainStation = arcpy.GetParameterAsText(11)
Potential = arcpy.GetParameterAsText(12).split(";")
Barriers = arcpy.GetParameterAsText(13)
Modus = ["bus",int(ToFind.split(",")[0])],["train",int(ToFind.split(",")[1])]


def checkfm(FC, FC_ID):
    OID, fm = "", ""
    for field in arcpy.Describe(FC).fields:
        if field.type == "OID": OID = field.name
        if "SnapX" in field.name:
            fm = "Name "+FC_ID+" 0; SourceID SourceID_NMT 0;SourceOID SourceOID_NMT 0"\
            ";PosAlong PosAlong_NMT 0;SideOfEdge SideOfEdge_NMT 0; SnapX SnapX_NMT 0"\
            "; SnapY SnapY_NMT 0; DistanceToNetworkInMeters DistanceToNetworkInMeters_NMT 0"
    return OID, fm

def costattr():
    global cost_attr
    attributes = arcpy.Describe(Network).attributes ##cost attributes from network
    cost_attr = []
    for attribute in attributes:
        if attribute.usageType == "Cost":cost_attr.append(attribute.name)

def ExportRoutes(mod):
    fields = ["NAME"]
    for field in cost_attr: fields.append("Total_"+field)
    array = []
    with arcpy.da.SearchCursor("ODLayer\Lines", fields) as routes:
        for route in routes:
            if mod[0] == "bus": TRAIN = 0
            else: TRAIN = 1  
            l= (int(route[0].split(" - ")[0]),int(route[0].split(" - ")[1]),TRAIN)
            for i,e in enumerate(fields[1:]): #without NAME field
                l = l+(route[i+1],)
            array.append(l)
    del route,routes
    arcpy.Delete_management("places")
    arcpy.AddMessage("> routes: "+str(len(array)))
    return array

def HDF5(Database,Potential,results):
    file5 = h5py.File(Database,'r+')
    group5 = file5[Group]
    Fields = [('Start_ID', 'int32'),('Stop_NO', 'int32'),('Bahn', 'i2')]
    for i in cost_attr: Fields.append((i,'f8'))

    #--Basic data HDF5--#
    if Potential[0] != "":
        Potential = (Places_ID,) + tuple(Potential)
        Strukturen = arcpy.da.FeatureClassToNumPyArray(Places,Potential)
        dtypes = Strukturen.dtype
        for i in range(len(Potential)-1): ##-1 without Start_ID
            Fields.append((dtypes.names[i+1],dtypes[i+1].name)) ##+1 skip first row
        for i in range(len(results)):
            index = np.where(Strukturen[Places_ID]==results[i][0])[0][0]
            for h in range(len(Strukturen[index])-1):
                w = Strukturen[index][h+1] ##+1, um die erste Spalte zu überspringen
                results[i] = results[i]+(w,)

    #--Results tablen--#
    Fields = np.dtype(Fields)
    data = np.array(results,Fields)
    if Result_table in group5.keys(): del group5[Result_table]
    dset5 = group5.create_dataset(Result_table, data=data, dtype=Fields)

    #--HDF5-Attributes--#
    text = "date: "+date.today().strftime("%B %d, %Y")+", places: "+str(Places)+", stops: "+\
    str(Stops)+", mode: "+str(Mode)+", bus, train: "+str(ToFind)+", maximal costs: "+str(MaxCosts)
    dset5.attrs.create("Parameters",str(text))
    return file5

def ODLayer(mod,FC,FC_ID,fieldmap):
    arcpy.AddMessage("> starting with: "+mod[0])
    costattr()
    search_params()
    if mod[0] == "bus": arcpy.MakeFeatureLayer_management(FC, "stops",TrainStation+" = 0")
    else: arcpy.MakeFeatureLayer_management(FC, "stops",TrainStation+" > 0")
    if mod[1] == 0: arcpy.AddMessage("> no stops in mode: "+mod[0])
    
    arcpy.na.MakeODCostMatrixAnalysisLayer(Network,"ODLayer",Mode,MaxCosts,mod[1],"","","NO_LINES",cost_attr)
    
    if fieldmap == "": arcpy.na.AddLocations("ODLayer","Destinations","stops","Name "+FC_ID+\
    " 0","","",search_crit,"","","SNAP")
    else: arcpy.na.AddLocations("ODLayer","Destinations","stops",fieldmap)
    arcpy.AddMessage("> "+mod[0]+"stops added \n")
    if Barriers != "": arcpy.na.AddLocations("ODLayer","Line Barriers",Barriers)

def ODRouting(FC,FC_ID,OID,row,fieldmap):
    arcpy.MakeFeatureLayer_management(FC, "places",OID+" >= "+str(row)+" and "+OID+" < "+str(row+5000))
    if fieldmap == "": arcpy.na.AddLocations("ODLayer","Origins","places","Name "+FC_ID+\
    " 0","","",search_crit,"","CLEAR","SNAP","","",search_query)
    else: arcpy.na.AddLocations("ODLayer","Origins","places",fieldmap,"","","","","CLEAR")
    try: arcpy.na.Solve("ODLayer","SKIP","CONTINUE")
    except:
        arcpy.AddMessage("> error "+str(row)+" bis "+str(row+5000))
        arcpy.Delete_management("places")
        raise
        
def search_params():
    global search_crit
    search_crit = []
    desc = arcpy.Describe(Network)
    for i in desc.edgeSources:search_crit.append([i.name,"SHAPE"])
    for i in desc.junctionSources:search_crit.append([i.name,"NONE"])
    
    global search_query
    if desc.name == "MRH_NMT_Network":
        search_query = [["MRH_Links", "(bridge = 'F' and tunnel = 'F') or (tunnel = 'T' and access = 'customers')"]]
    else: search_query = ""

##############
#--starting--#
##############
Places_n = int(arcpy.GetCount_management(Places).getOutput(0))
arcpy.AddMessage("> amount of places: "+str(Places_n)+"\n")
Orig_fm = checkfm(Places, Places_ID)
Desti_fm = checkfm(Stops, Stops_ID)

#--routing--#
results = [] ##to fill into HDF5 table
for mod in Modus:
    if mod[1]==0:continue
    ODLayer(mod, Stops, Stops_ID, Desti_fm[1])
    for place in range(0,Places_n,5000):
        arcpy.AddMessage("> places from "+str(place)+" to "+str(place+5000))
        arcpy.AddMessage("> mod: "+mod[0])
        ODRouting(Places, Places_ID, Orig_fm[0], place, Orig_fm[1])
        results = results + ExportRoutes(mod)
        arcpy.AddMessage("> time: "+str(round(int(time.time()-start_time)/60,1))+" minutes \n")
    arcpy.Delete_management("stops")
    arcpy.Delete_management("ODLayer")
    arcpy.AddMessage("> "+mod[0]+" finished")

#--HDF5--#
arcpy.AddMessage("\n> starting with HDF5 \n")
file5 = HDF5(Database,Potential,results)

#end
arcpy.AddMessage("> finished")
file5.flush()
file5.close()