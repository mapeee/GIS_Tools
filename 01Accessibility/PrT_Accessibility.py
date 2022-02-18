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
#arcpy.management.SaveToLayerFile("ODMATRIX",r'PATH\\CF_Ergebnis',"RELATIVE")

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
Network = arcpy.GetParameterAsText(9)
Costs = arcpy.GetParameterAsText(10)
Max_Costs = int(arcpy.GetParameterAsText(11))
StructField = arcpy.GetParameterAsText(12).split(";")
Measures = arcpy.GetParameterAsText(13).split(";")
sumfak_t = arcpy.GetParameterAsText(14).split(";")
sumfak_d = arcpy.GetParameterAsText(15).split(";")
potfak = arcpy.GetParameterAsText(16).split(";")

ID_A = "ID"
ID_P = "ID"
Barriers = None
if sumfak_d == ['']: sumfak_d = None
if PrT == "Motorized": loops = 100
else: loops = 1000


def checkfm(FC, FC_ID):
    if PrT == "Motorized": mode = "MIV"
    else: mode = "NMIV"
    for field in arcpy.Describe(FC).fields:
        if "SnapX" in field.name:
            fm = "Name "+FC_ID+" 0; SourceID SourceID_"+mode+" 0;SourceOID SourceOID_"+mode+" 0"\
            ";PosAlong PosAlong_"+mode+" 0;SideOfEdge SideOfEdge_"+mode+" 0; Attr_Minutes # #"
            return fm

def costattr():
    global cost_attr
    attributes = arcpy.Describe(Network).attributes ##cost attributes from network
    cost_attr = []
    for attribute in attributes:
        if attribute.usageType == "Cost":cost_attr.append(str(attribute.name))

def exp_aggr(series): return int(round(sum(np.exp(series[Costs]*n) * series[Column])))

def distance(group, groups):
    arcpy.Delete_management("P_Shape")
    if Filter_Group_P:
        arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape",Filter_Group_P+"= "+str(group))
        arcpy.AddMessage("> group "+str(group)+"/"+str(len(groups))+" with "+str(len(dataP[dataP[Filter_Group_P]==group]))+" places")
    else:
        arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape")
        arcpy.AddMessage("> distances to next place out of "+str(len(dataP))+" places")

    if Filter_P: arcpy.SelectLayerByAttribute_management("P_Shape", "ADD_TO_SELECTION", Filter_P+">0")

    fm_P = checkfm("P_Shape",ID_P)
    if fm_P is None:arcpy.AddLocations_na("ODMATRIX","Destinations","P_Shape","Name "+ID_P+\
    " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","","","","EXCLUDE")
    else: arcpy.AddLocations_na("ODMATRIX","Destinations","P_Shape",fm_P,"","","","","CLEAR","","","EXCLUDE")

    arcpy.na.Solve("ODMATRIX")

    routes = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("ODMATRIX\Lines",["Name"]+["Total_"+x for x in cost_attr]))
    routes[[ID_A,ID_P+"_P"]] = routes.Name.str.split(' - ',expand=True,).astype(int)
    routes.columns = [map(lambda a:a.replace("Total_",""),routes.columns)]
    routes.drop("Name", axis=1, inplace=True)

    if Filter_Group_P:
        routes[Filter_Group_P] = group
        Result = routes[[ID_A,ID_P+"_P"]+cost_attr+[Filter_Group_P]]
    else: Result = routes[[ID_A,ID_P+"_P"]+cost_attr]

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
                    Fields.append(((i+e).encode('ascii'),'int32'))
            elif i[-3:] == "Sum":
                for e in sumfak_t: Fields.append(((i+e).encode('ascii'),'int32'))
                if sumfak_d is not None:
                    for e in sumfak_d: Fields.append(((i+e).encode('ascii'),'int32'))
            else: Fields.append((i.encode('ascii'),'int32'))

    if "Distance" in Modus:
        Fields = [('Orig_ID', 'int32'),('Place_ID','int32')]
        for i in cost_attr: Fields.append((i,'f8'))
        if Filter_Group_P: Fields.append(('Group','i2'))

    if Table_R in group5_Results.keys(): del group5_Results[Table_R]
    group5_Results.create_dataset(Table_R, data=np.array([],Fields), dtype=np.dtype(Fields), maxshape = (None,))
    Results_T = group5_Results[Table_R]
    Results_T.attrs.create("Parameter",str(Text()))
    file5.flush()

    return Results_T

def ODLayer():
    arcpy.Delete_management("ODMATRIX")

    if "Potential" in Modus: tofind = ""
    else: tofind = 1

    arcpy.MakeODCostMatrixLayer_na(Network,"ODMATRIX",Costs,Max_Costs,tofind,cost_attr,"","","","","NO_LINES")
    p = arcpy.na.GetSolverProperties(arcpy.mapping.Layer("ODMATRIX"))
    Restriction_0 = list(p.restrictions) ##activate all restrictions
    p.restrictions = Restriction_0
    if Barriers: arcpy.AddLocations_na("ODMATRIX","Line Barriers",Barriers,"","")

    if "Distance" in Modus:
        fm_A = checkfm(A_Shape,ID_A)
        if fm_A is None: arcpy.AddLocations_na("ODMATRIX","Origins",A_Shape,"Name "+ID_A+\
        " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","","","","EXCLUDE")
        else: arcpy.AddLocations_na("ODMATRIX","Origins",A_Shape,fm_A,"","","","","CLEAR","","","EXCLUDE")

    if "Potential" in Modus:
        arcpy.Delete_management("P_Shape")
        if Filter_P: arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape",Filter_P+">0")
        else: arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape")
        fm_P = checkfm("P_Shape",ID_P)
        if fm_P is None: arcpy.AddLocations_na("ODMATRIX","Destinations","P_Shape","Name "+ID_P+\
        " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","","","","EXCLUDE")
        else: arcpy.AddLocations_na("ODMATRIX","Destinations","P_Shape",fm_P,"","","","","CLEAR","","","EXCLUDE")

def potential(origins,loop):
    global n, Column
    global Result, Column, e, routes, ID_A
    arcpy.AddMessage("> origins from "+str(origins)+" to "+str(origins+loop)+" from "+str(Origins))
    arcpy.Delete_management("A_Shape")
    for field in arcpy.Describe(A_Shape).fields:
            if field.type == "OID": OID = str(field.name)
    arcpy.MakeFeatureLayer_management(A_Shape, "A_Shape",OID+" >= "+str(origins)+" and "+OID+" < "+str(origins+loop))

    fm_A = checkfm("A_Shape",ID_A)
    if fm_A is None:arcpy.AddLocations_na("ODMATRIX","Origins","A_Shape","Name "+ID_A+\
    " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","","","","EXCLUDE")
    else: arcpy.AddLocations_na("ODMATRIX","Origins","A_Shape",fm_A,"","","","","CLEAR","","","EXCLUDE")

    arcpy.na.Solve("ODMATRIX")
    routes = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("ODMATRIX\Lines",["Name"]+["Total_"+x for x in cost_attr]))
    routes[[ID_A,ID_P+"_P"]] = routes.Name.str.split(' - ',expand=True,).astype(int)
    routes.columns = [map(lambda a:a.replace("Total_",""),routes.columns)]
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
                Values = routes.groupby([ID_A]).agg(exp_aggr).reset_index(drop=False)[[ID_A,Column]]
                Result = pandas.merge(Result,Values,how="left",left_on=ID_A,right_on=ID_A)

    Result = Result.fillna(0)
    Result = np.array(Result)

    for row in Result:
        row = [tuple(row)]
        oldsize = len(Results_T)
        Results_T.resize((oldsize+1,))
        Results_T[oldsize:oldsize+1] = row
        file5.flush()

def Text():
    text = "Date: "+date.today().strftime("%B %d, %Y")+"; " +PrT+"; "+Modus+"; Costs: "+Costs+\
    "; Max-Costs: "+str(Max_Costs)+"; Origins: "+A_Shape.split("\\")[-1]+"; Places: "+P_Shape.split("\\")[-1]
    if "Potential" in Modus: text = text + "; Measures: "+"/".join(Measures)
    if Filter_Group_P: text = text + "; Filter Group: "+Filter_Group_P
    return text

#--preparation--#
costattr()
file5 = h5py.File(Database,'r+')
group5_Results = file5[Group_R]
Results_T = HDF5_Results()

#--measures--#
arcpy.AddMessage("> calculate measures\n")
ODLayer()

dataP = arcpy.da.FeatureClassToNumPyArray(P_Shape,["*"],null_value=0)
if Modus == "Distance":
    if Filter_Group_P: Groups = np.unique(dataP[Filter_Group_P])
    else: Groups = [1]
    for i in Groups: distance(i, Groups)

if "Potential" in Modus:
    Origins = int(arcpy.GetCount_management(A_Shape).getOutput(0))
    for origin_l in range(0,Origins,loops): potential(origin_l,loops)

arcpy.AddMessage("> "+Modus+" measures finished")

#end
arcpy.AddMessage("> finished after "+str(int(time.time()-start_time))+" seconds")
file5.flush()
file5.close()