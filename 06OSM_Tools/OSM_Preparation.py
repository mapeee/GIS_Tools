# -*- coding: cp1252 -*-
#!/usr/bin/python
#Prepare car network for import into PTV VISUM network
#March 2015
#für Python 2.6.7


import win32com.client.dynamic
import arcpy
import time
import numpy
from OSM_keys import Typ
start_time = time.time()
arcpy.AddMessage("> starting\n")

#--ArcGIS Parameter--#
FC = arcpy.GetParameterAsText(0)
Delete = arcpy.GetParameterAsText(1)
Types = arcpy.GetParameterAsText(2)
Nodes = arcpy.GetParameterAsText(3)
Node_Place = arcpy.GetParameterAsText(4)
Node_Name = arcpy.GetParameterAsText(5)
Split = arcpy.GetParameterAsText(6)
Radius = arcpy.GetParameterAsText(7)+" Meters"
Split_Place = arcpy.GetParameterAsText(8)
Split_Name = arcpy.GetParameterAsText(9)
Network = arcpy.GetParameterAsText(10)
Double_Node = arcpy.GetParameterAsText(11)
Double_Link = arcpy.GetParameterAsText(12)

if bool(Nodes) == True: Node_Name = Node_Place+"\\"+Node_Name
if bool(Split) == True: Split_Name = Split_Place+"\\"+Split_Name

desc = arcpy.Describe(FC)
Type = desc.shapeType
if Type == "Point": Node_Name = FC

#--Delete parameter--#
Del_types = ["service",
"track","road",
"steps","razed","turning_circle",
"proposed","planned","construction",
"pedestrian","path","ford","fixme",
"footway","cycleway","historic","street_lamp",
"abandoned_path","never_built",
"living_street","gliding","trail",
"centre_line","services",
"bridleway","raceway","emergency_bay",
"bus_stop","platform","escape",
"rest_area","corridor","byway",
"abandoned", "access_ramp", "ramp",
"corridor","crossing","elevator",
"destruction","disused","none","yes","no",
"unknown","traffic_island",
"traffic_signals","further_demand",
"emergency_access","bus_guideway","demolished"]

#--deleting links--#
arcpy.AddMessage("> deleting unused links\n")
with arcpy.da.UpdateCursor(FC, ['type']) as cursor:
    for row in cursor:
        if bool(Delete) == True:
            if row[0] in Del_types: cursor.deleteRow()

#--adding VISUM link types--#
if bool(Types) == True:
    arcpy.AddMessage("> adding PTV VISUM link types\n")
    arcpy.AddField_management(FC, 'STRECKENTYPEN', "LONG")
    arcpy.AddField_management(FC, 'STRECKENKLASSEN', "SHORT")
    Typ(FC)

#--nodes--#
if bool(Nodes) == True:
    arcpy.AddMessage("> creating nodes")
    arcpy.FeatureVerticesToPoints_management(FC, Node_Name, "BOTH_ENDS")
    arcpy.AddMessage("> deleting stacked nodes\n")
    arcpy.AddXY_management(Node_Name)
    fields = ["POINT_X", "POINT_Y"]
    arcpy.DeleteIdentical_management(Node_Name, fields)
    arcpy.DeleteField_management(Node_Name, fields)

#--spliting links--#
if bool(Split) == True:
    arcpy.AddMessage("> spliting links at nodes\n")
    arcpy.SplitLineAtPoint_management(FC, Node_Name, Split_Name, Radius)

#--create cleare node and link numbers--#
if bool(Double_Node) or bool(Double_Link) == True:
    VISUM = win32com.client.dynamic.Dispatch("Visum.Visum.22")
    VISUM.loadversion(Network)
    VISUM.Filters.InitAll()

if bool(Double_Node) == True:
    arcpy.AddMessage("> creating clear node numbers")
    arcpy.AddField_management(Node_Name, "ID", "LONG")
    Nodes = numpy.array(VISUM.Net.Nodes.GetMultiAttValues("No")).astype("int")[:,1]
    with arcpy.da.UpdateCursor(Node_Name, ['ID']) as cursor:
        Value = 20000
        for row in cursor:
            while Value in Nodes:
                Value = Value+1
            row[0] = Value
            cursor.updateRow(row)
            Value = Value+1

if bool(Double_Link) == True:
    if Split_Name != True:
        Split_Name = FC
    arcpy.AddMessage("> creating clear link numbers")
    arcpy.AddField_management(Split_Name, "ID", "LONG")
    Links = numpy.array(VISUM.Net.Links.GetMultiAttValues("No")).astype("int")[:,1]
    with arcpy.da.UpdateCursor(Split_Name, ['ID']) as cursor:
        Value = 20000
        for row in cursor:
            while Value in Links:
                Value = Value+1
            row[0] = Value ##erstelle erstmal eindeutige IDs
            cursor.updateRow(row)
            Value = Value+1

#end
arcpy.AddMessage("> finished after "+str(int(time.time()-start_time))+" seconds")