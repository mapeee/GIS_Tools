#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name: PrT Accessibility
# Purpose: Calculate accessibility measures for private transport (car, walk, bike) using ArcGIS NA
# Author:      mape
# Created:     08/12/2021
# Copyright:   (c) mape 2021
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
from datetime import date
import h5py
import numpy as np
import pandas
import time
start_time = time.time()
pandas.options.mode.chained_assignment = None
arcpy.CheckOutExtension("Network")

#--ArcGIS Parameter--#
PrT = arcpy.GetParameterAsText(0)
Modus = arcpy.GetParameterAsText(1)
Database = arcpy.GetParameterAsText(2)
Group_R = arcpy.GetParameterAsText(3)
Table_R = arcpy.GetParameterAsText(4)
A_Shape = arcpy.GetParameterAsText(5)
P_Shape = arcpy.GetParameterAsText(6)
Filter_P = arcpy.GetParameterAsText(7)
Filter_Group_P = arcpy.GetParameterAsText(8)
to_find = int(arcpy.GetParameterAsText(9))
Network = arcpy.GetParameterAsText(10)
Mode = arcpy.GetParameterAsText(11)
MaxCosts = int(arcpy.GetParameterAsText(12))
StructField = arcpy.GetParameterAsText(13).split(";")
Measures = arcpy.GetParameterAsText(14).split(";")
sumfak_t = arcpy.GetParameterAsText(15).split(";")
sumfak_d = arcpy.GetParameterAsText(16).split(";")
potfak = arcpy.GetParameterAsText(17).split(";")

ID_A = "ID"
ID_P = "ID"
Barriers = None
if sumfak_d == ['']: sumfak_d = None
if PrT == "Motorized": loops = 100
else: loops = 1000
if "Potential" in Modus: to_find = ""

def checkfm(FC, FC_ID):
    if PrT == "Motorized": mode = "MT"
    else: mode = "NMT"
    for field in arcpy.Describe(FC).fields:
        if "SnapX" in field.name:
            arcpy.AddMessage("> using FieldMappings for "+FC)
            fm = "Name "+FC_ID+" 0; SourceID SourceID_"+mode+" 0;SourceOID SourceOID_"+mode+" 0"\
            ";PosAlong PosAlong_"+mode+" 0;SideOfEdge SideOfEdge_"+mode+" 0; SnapX SnapX_"+mode+" 0"\
            "; SnapY SnapY_"+mode+" 0; DistanceToNetworkInMeters DistanceToNetworkInMeters_"+mode+" 0"
            return fm

def costattr():
    global cost_attr
    attributes = arcpy.Describe(Network).attributes ##cost attributes from network
    cost_attr = []
    for attribute in attributes:
        if attribute.usageType == "Cost":cost_attr.append(attribute.name)

def distance(group, groups):
    arcpy.Delete_management("P_Shape")
    if Filter_Group_P:
        arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape",Filter_Group_P+"= "+str(group))
        arcpy.AddMessage("> group ID "+str(int(group))+" with "+str(len(dataP[dataP[Filter_Group_P]==group]))+" places")
    else:
        arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape")
        arcpy.AddMessage("\n> distances to next place out of "+str(len(dataP))+" places")

    if Filter_P: arcpy.SelectLayerByAttribute_management("P_Shape", "ADD_TO_SELECTION", Filter_P+">0")

    fm_P = checkfm("P_Shape",ID_P)
    arcpy.na.AddFieldToAnalysisLayer("ODLayer", "Destinations","tto_park", "Integer")
    if fm_P is None: arcpy.na.AddLocations("ODLayer","Destinations","P_Shape","Name "+ID_P+\
                                           " 0; tto_park # 2","","",search_crit,search_query=search_query) 
    else:
        fm_P = fm_P+"; tto_park tZu 2"
        arcpy.na.AddLocations("ODLayer","Destinations","P_Shape",fm_P,"","","","","CLEAR")

    arcpy.na.Solve("ODLayer","SKIP","CONTINUE")

    if PrT == "Motorized":
        arcpy.DeleteField_management("Lines",["tfrom_park","tto_park"])
        arcpy.management.JoinField("Lines", "OriginID","Origins", "ObjectID", "tfrom_park")
        arcpy.management.JoinField("Lines", "DestinationID","Destinations", "ObjectID", "tto_park")
        routes = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("ODLayer\Lines",["Name"]+["Total_"+x for x in cost_attr]+["DestinationRank","tfrom_park","tto_park"]))
        routes["Total_"+Costs] = routes["Total_"+Costs]+routes["tfrom_park"]+routes["tto_park"]

    else: routes = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("ODLayer\Lines",["Name"]+["Total_"+x for x in cost_attr]+["DestinationRank"]))
    routes[[ID_A,ID_P+"_P"]] = routes.Name.str.split(' - ',expand=True,).astype(int)
    routes.columns = routes.columns.str.replace("Total_", "")
    routes.drop("Name", axis=1, inplace=True)

    if Filter_Group_P:
        routes[Filter_Group_P] = group
        if PrT == "Motorized": Result = routes[[ID_A,ID_P+"_P"]+cost_attr+["tfrom_park","tto_park","DestinationRank"]+[Filter_Group_P]]
        else: Result = routes[[ID_A,ID_P+"_P"]+cost_attr+["DestinationRank"]+[Filter_Group_P]]
    else:
        if PrT == "Motorized": Result = routes[[ID_A,ID_P+"_P"]+cost_attr+["tfrom_park","tto_park","DestinationRank"]]
        else: Result = routes[[ID_A,ID_P+"_P"]+cost_attr+["DestinationRank"]]

    Result = np.array(Result)
    oldsize = len(Results_T)
    sizer = oldsize + len(Result)
    Results_T.resize((sizer,))
    Result = list(map(tuple, Result))
    Results_T[oldsize:sizer] = Result
    file5.flush()

def HDF5_Results():
    if "Potential" in Modus:
        Fields = [('Orig_ID', 'int32')]
        for i in Measures:
            if i[-4:] == "Expo":
                for e in potfak:
                    e = str(e.split(".")[1])
                    if len(e)==2: e+="0"
                    Fields.append(((i+e),'int32'))
            elif i[-3:] == "Sum":
                for e in sumfak_t: Fields.append(((i+e),'int32'))
                if sumfak_d is not None:
                    for e in sumfak_d: Fields.append(((i+e),'int32'))
            else: Fields.append((i,'int32'))

    if "Distance" in Modus:
        Fields = [('Orig_ID', 'int32'),('Place_ID','int32')]
        for i in cost_attr: Fields.append((i,'f8'))
        if PrT == "Motorized":
            Fields.append(('tfrom_park','f8'))
            Fields.append(('tto_park','f8'))
        Fields.append(('tofind','i2'))
        if Filter_Group_P: Fields.append(('Group','i2'))

    if Table_R in group5_Results.keys(): del group5_Results[Table_R]
    group5_Results.create_dataset(Table_R, data=np.array([],Fields), dtype=np.dtype(Fields), maxshape = (None,))
    Results_T = group5_Results[Table_R]
    Results_T.attrs.create("Parameter",str(Text()))
    file5.flush()

    return Results_T

def ODLayer():
    arcpy.Delete_management("ODLayer")

    arcpy.na.MakeODCostMatrixAnalysisLayer(Network,"ODLayer",Mode,MaxCosts,to_find,"","","NO_LINES",cost_attr)

    if Barriers: arcpy.na.AddLocations("ODLayer","Line Barriers",Barriers)

    if "Distance" in Modus:
        fm_A = checkfm(A_Shape,ID_A)
        arcpy.na.AddFieldToAnalysisLayer("ODLayer", "Origins","tfrom_park", "Integer")
        if fm_A is None: arcpy.na.AddLocations("ODLayer","Origins",A_Shape,"Name "+ID_A+\
                                               " 0; tfrom_park # 1","","",search_crit,search_query=search_query)  
        else:
            fm_A = fm_A+"; tfrom_park tAb 1"
            arcpy.na.AddLocations("ODLayer","Origins",A_Shape,fm_A,"","","","","CLEAR")

    if "Potential" in Modus:
        arcpy.Delete_management("P_Shape")
        if Filter_P: arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape",Filter_P+">0")
        else: arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape")
        fm_P = checkfm("P_Shape",ID_P)
        if fm_P is None: arcpy.na.AddLocations("ODLayer","Destinations","P_Shape","Name "+ID_P+\
                                                   " 0","","",search_crit,search_query=search_query) 
        else: arcpy.na.AddLocations("ODLayer","Destinations","P_Shape",fm_P,"","","","","CLEAR")

def potential(origins,loop):
    global Result, Column, e, routes, ID_A
    arcpy.AddMessage("> origins from "+str(origins)+" to "+str(min((origins+loop),Origins))+" from "+str(Origins))
    arcpy.Delete_management("A_Shape")
    for field in arcpy.Describe(A_Shape).fields:
            if field.type == "OID": OID = str(field.name)
    arcpy.MakeFeatureLayer_management(A_Shape, "A_Shape",OID+" >= "+str(origins)+" and "+OID+" < "+str(origins+loop))

    fm_A = checkfm("A_Shape",ID_A)
    if fm_A is None: arcpy.na.AddLocations("ODLayer","Origins","A_Shape","Name "+ID_A+\
                                           " 0","","",search_crit,search_query=search_query) 
    else: arcpy.na.AddLocations("ODLayer","Origins","A_Shape",fm_A,"","","","","CLEAR")

    arcpy.na.Solve("ODLayer","SKIP","CONTINUE")
    routes = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("ODLayer\Lines",["Name"]+["Total_"+x for x in cost_attr]))
    if len(routes)==0: return
    
    routes[[ID_A,ID_P+"_P"]] = routes.Name.str.split(' - ',expand=True,).astype(int)
    for a in routes.columns: routes.rename(columns={a: a.replace("Total_","")},inplace=True)
    routes.drop("Name", axis=1, inplace=True)

    StructData = pandas.DataFrame(dataP[[ID_P]+StructField])
    StructData = StructData.rename(columns = {ID_P:ID_P+"_P"})

    routes = pandas.merge(routes,StructData)

    Result = pandas.DataFrame(np.unique(routes[ID_A]))
    Result = Result.rename(columns = {0:ID_A})

    for e in Measures:
        Column = e.split("__")[0] ##to get the name of places
        if e[-3:] == "Sum":
            for n in sumfak_t:
                Values = routes[routes[Costs]<=int(n)].groupby([ID_A])[Column].agg('sum').reset_index(drop=False)
                Result = pandas.merge(Result,Values,how="left",left_on=ID_A,right_on=ID_A)
            if sumfak_d:
                for n in sumfak_d:
                    Values = routes[routes["Meter"]<=int(n)].groupby([ID_A])[Column].agg('sum').reset_index(drop=False)
                    Result = pandas.merge(Result,Values,how="left",left_on=ID_A,right_on=ID_A)
        if e[-4:] == "Expo":
            for n in potfak:
                n = float(n)
                Values = routes.groupby([ID_A])[Column].agg(lambda x: int(round(np.sum(np.exp(routes[Costs] * n) * x)))).reset_index()
                Result = pandas.merge(Result,Values,how="left",left_on=ID_A,right_on=ID_A)

    Result = Result.fillna(0)
    Result = np.array(Result)

    for row in Result:
        row = [tuple(row)]
        oldsize = len(Results_T)
        Results_T.resize((oldsize+1,))
        Results_T[oldsize:oldsize+1] = row
        file5.flush()

def search_params():
    global search_crit
    search_crit = []
    desc = arcpy.Describe(Network)
    for i in desc.edgeSources:search_crit.append([i.name,"SHAPE"])
    for i in desc.junctionSources:search_crit.append([i.name,"NONE"])
    
    global search_query
    try:
        if PrT != "Motorized": search_query = [[desc.edgeSources[0].name, "(bridge = 'F' and tunnel = 'F') or (tunnel = 'T' and access = 'customers')"],
                                           [desc.junctionSources[0].name,"Snap = 1"]]
        else: search_query = [[desc.edgeSources[0].name, "bridge = 'F' and tunnel = 'F' and highway not in ('motorway', 'trunk', 'motorway_link', 'trunk_link')"],
                              [desc.junctionSources[0].name,"Snap = 1"]]
    except: search_query = ""
    
    global Costs
    travel_modes = arcpy.na.GetTravelModes(Network)
    for tm in travel_modes:
        if tm == Mode: Costs = travel_modes[tm].impedance

def Text():
    text = "Date: "+date.today().strftime("%B %d, %Y")+"; " +str(PrT)+"; "+str(Modus)+"; Costs: "+str(Costs)+\
    "; Max-Costs: "+str(MaxCosts)+";tofind: "+str(to_find)+"; Origins: "+str(A_Shape.split("\\")[-1])+"; Places: "+str(P_Shape.split("\\")[-1])
    if "Potential" in Modus: text = text + "; Measures: "+str("/".join(Measures))
    if Filter_Group_P: text = text + "; Filter Group: "+str(Filter_Group_P)
    return text

#--preparation--#
costattr()
search_params()
file5 = h5py.File(Database,'r+')
group5_Results = file5[Group_R]
Results_T = HDF5_Results()

#--measures--#
ODLayer()

dataP = arcpy.da.FeatureClassToNumPyArray(P_Shape,["*"],null_value=0)
if Modus == "Distance":
    arcpy.AddMessage("\n> calculate distance measures")
    if Filter_Group_P:
        Groups = np.unique(dataP[Filter_Group_P])
        arcpy.AddMessage("> groups: "+str(len(Groups))+"\n")
    else: Groups = [1]
    for e,i in enumerate(Groups):
        if len(Groups) >1: arcpy.AddMessage("> group "+str(e+1)+"/"+str(len(Groups)))
        distance(i, Groups)

if "Potential" in Modus:
    arcpy.AddMessage("\n> calculate potential measures")
    Origins = int(arcpy.GetCount_management(A_Shape).getOutput(0))
    for origin_l in range(0,Origins,loops): potential(origin_l,loops)

arcpy.AddMessage("> "+Modus+" measures finished")

#end
arcpy.AddMessage("\n> finished after "+str(int(time.time()-start_time))+" seconds")
file5.flush()
file5.close()