#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name: Next_Stops
# Purpose: Connecting places to next stops in a network
#
# Author:      mape
#
# Created:     02/09/2015 (new Version 2021)
# Copyright:   (c) mape 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#arcpy.management.SaveToLayerFile("ODLayer",r'PATH\\CF_Ergebnis',"RELATIVE")

import arcpy
import h5py
import numpy as np
import time
start_time = time.clock()
arcpy.CheckOutExtension("Network")

#--GIS Parameters--#
Start = arcpy.GetParameterAsText(0)
Start_ID = arcpy.GetParameterAsText(1)
Ziel = arcpy.GetParameterAsText(2)
Ziel_ID = arcpy.GetParameterAsText(3)
Datenbank = arcpy.GetParameterAsText(4)
Group = arcpy.GetParameterAsText(5)
Network = arcpy.GetParameterAsText(6)
Costs = arcpy.GetParameterAsText(7) ##costs (trad, Meter, etc.)
Anzahl = arcpy.GetParameterAsText(8) ##amount of next stops
Result_table = arcpy.GetParameterAsText(9)
MaxCosts = arcpy.GetParameterAsText(10)
BahnFeld = arcpy.GetParameterAsText(11)
Potential = arcpy.GetParameterAsText(12).split(";")
Barrieren = arcpy.GetParameterAsText(13)
Modus = ["bus",int(Anzahl.split(",")[0])],["train",int(Anzahl.split(",")[1])]

def checkfm(FC, FC_ID):
    OID, fm = "", ""
    for field in arcpy.Describe(FC).fields:
        if field.type == "OID": OID = field.name
        if "SnapX" in field.name:
            fm = "Name "+FC_ID+" 0; SourceID SourceID_NMIV 0;SourceOID SourceOID_NMIV 0"\
            ";PosAlong PosAlong_NMIV 0;SideOfEdge SideOfEdge_NMIV 0; Attr_tAkt # #"
    return OID, fm

def costattr():
    global cost_attr
    attributes = arcpy.Describe(Network).attributes ##cost attributes from network
    cost_attr = []
    for attribute in attributes:
        if attribute.usageType == "Cost":cost_attr.append(attribute.name)

def ExportRoutes(mod):
    routes = arcpy.SearchCursor("ODLayer\Lines")
    route = routes.next()
    array = []
    if mod[0] == "bus": TRAIN = 0
    else: TRAIN = 1
    while route:
        l = (int(route.NAME.split(" - ")[0]),int(route.NAME.split(" - ")[1]),TRAIN)
        for field in cost_attr:
            field = "Total_"+field
            a = route.getValue(field)
            l = l+(a,)
        array.append(l)
        route = routes.next()
    del route,routes
    arcpy.Delete_management("places")
    arcpy.AddMessage("> routes: "+str(len(array)))
    return array

def HDF5(Datenbank,Potential,results):
    file5 = h5py.File(Datenbank,'r+')
    group5 = file5[Group]
    Fields = [('Start_ID', 'int32'),('Stop_NO', 'int32'),('Bahn', 'i2')]
    for i in cost_attr: Fields.append((i.encode('ascii'),'f8'))

    #--Basic data HDF5--#
    if Potential[0] != "":
        Potential = (Start_ID.encode('ascii'),) + tuple(Potential)
        Strukturen = arcpy.da.FeatureClassToNumPyArray(Start,Potential)
        dtypes = Strukturen.dtype
        for i in range(len(Potential)-1): ##-1 without Start_ID
            Fields.append((dtypes.names[i+1],dtypes[i+1].name)) ##+1 skip first row
        for i in range(len(results)):
            index = np.where(Strukturen[Start_ID.encode('ascii')]==results[i][0])[0][0]
            for h in range(len(Strukturen[index])-1):
                w = Strukturen[index][h+1] ##+1, um die erste Spalte zu überspringen
                results[i] = results[i]+(w,)

    #--Results tablen--#
    Fields = np.dtype(Fields)
    data = np.array(results,Fields)
    if Result_table in group5.keys(): del group5[Result_table]
    dset5 = group5.create_dataset(Result_table, data=data, dtype=Fields)

    #--HDF5-Attributes--#
    text = "date: "+str(time.localtime()[0:3])+", places: "+Start+", stops: "+\
    Ziel+", costs: "+Costs+", bus, train: "+Anzahl+", maximal costs: "+str(MaxCosts)
    dset5.attrs.create("Parameters",str(text))
    return file5

def ODLayer(mod,FC,FC_ID,fieldmap):
    arcpy.AddMessage("> starting with: "+mod[0])
    costattr()
    if mod[0] == "bus": arcpy.MakeFeatureLayer_management(FC, "stops",BahnFeld+" = 0")
    else: arcpy.MakeFeatureLayer_management(FC, "stops",BahnFeld+" > 0")
    if mod[1] == 0: arcpy.AddMessage("> no stops in mode: "+mod[0])

    arcpy.MakeODCostMatrixLayer_na(Network,"ODLayer",Costs,MaxCosts,mod[1],cost_attr,"","","","","NO_LINES")
    if fieldmap == "": arcpy.AddLocations_na("ODLayer","Destinations","stops","Name "+FC_ID+\
    " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","","","","EXCLUDE")
    else: arcpy.AddLocations_na("ODLayer","Destinations","stops",fieldmap,"","","","","","","","EXCLUDE")
    arcpy.AddMessage("> "+mod[0]+"stops added \n")
    if Barrieren != "": arcpy.AddLocations_na("ODLayer","Line Barriers",Barrieren)

def ODRouting(FC,FC_ID,OID,row,fieldmap):
    arcpy.MakeFeatureLayer_management(FC, "places",OID+" >= "+str(row)+" and "+OID+" < "+str(row+5000))
    if fieldmap == "": arcpy.AddLocations_na("ODLayer","Origins","places","Name "+FC_ID+\
    " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","CLEAR","","","EXCLUDE")
    else: arcpy.AddLocations_na("ODLayer","Origins","places",fieldmap,"","","","","CLEAR","","","EXCLUDE")
    try: arcpy.Solve_na("ODLayer","SKIP") ##SKIP:Not Located is skipped
    except:
        arcpy.AddMessage("> error "+str(row)+" bis "+str(row+5000))
        arcpy.Delete_management("places")
        raise

##############
#--starting--#
##############
Places = int(arcpy.GetCount_management(Start).getOutput(0))
arcpy.AddMessage("> amount of places: "+str(Places)+"\n")
Orig_fm = checkfm(Start, Start_ID)
Desti_fm = checkfm(Ziel, Ziel_ID)

#--routing--#
results = [] ##to fill into HDF5 table
for mod in Modus:
    ODLayer(mod, Ziel, Ziel_ID, Desti_fm[1])
    for place in range(0,Places,5000):
        arcpy.AddMessage("> placaes from "+str(place)+" to "+str(place+5000))
        ODRouting(Start, Start_ID, Orig_fm[0], place, Orig_fm[1])
        results = results + ExportRoutes(mod)
        arcpy.AddMessage("> time: "+str(int((time.clock() - start_time)/60))+" minutes \n")
    arcpy.Delete_management("stops")
    arcpy.Delete_management("ODLayer")
    arcpy.AddMessage("> "+mod[0]+" finished")

#--HDF5--#
arcpy.AddMessage("\n> starting with HDF5 \n")
file5 = HDF5(Datenbank,Potential,results)

#end
arcpy.AddMessage("> finished")
file5.flush()
file5.close()