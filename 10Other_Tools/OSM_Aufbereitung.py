# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skriptzum Aufbereiten von OSM-Netzen für den VISUM-Import.
#Marcus März 2015
#für Python 2.6.7

"""
Die Idee ist die Folgende:
1.
"""

#---Vorbereitung---#
import win32com.client.dynamic
import arcpy
import time
import numpy
from OSM_Bruecke import Typ
start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben
arcpy.AddMessage("--Dieses Skript ermöglicht die Umwandlung in Spalten aus mehreren Zeilen.--")
arcpy.AddMessage("--Beginne mit der Berechnung!--")

#--Eingabe-Parameter--#
FC = arcpy.GetParameterAsText(0)
Loeschen = arcpy.GetParameterAsText(1)
Typen = arcpy.GetParameterAsText(2)
Knoten = arcpy.GetParameterAsText(3)
Knoten_Ort = arcpy.GetParameterAsText(4)
Knoten_Name = arcpy.GetParameterAsText(5)
Trennen = arcpy.GetParameterAsText(6)
Radius = arcpy.GetParameterAsText(7)+" Meters"
Trennen_Ort = arcpy.GetParameterAsText(8)
Trennen_Name = arcpy.GetParameterAsText(9)
Netz = arcpy.GetParameterAsText(10)
Doppelt_Knoten = arcpy.GetParameterAsText(11)
Doppelt_Strecken = arcpy.GetParameterAsText(12)

#--Weiterer Parameter--#
if bool(Knoten) == True:
    Knoten_Name = Knoten_Ort+"\\"+Knoten_Name
if bool(Trennen) == True:
    Trennen_Name = Trennen_Ort+"\\"+Trennen_Name

desc = arcpy.Describe(FC)
Type = desc.shapeType
if Type == "Point":
    Knoten_Name = FC


#--Losch-Parameter--#
Loesch_Typ = ["service",
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

###########################################################################
#--Bereinigung der Strecken--#
###########################################################################
arcpy.AddMessage("--Beginne mit der Bereinigung der Strecken--")
with arcpy.da.UpdateCursor(FC, ['type']) as cursor:
    for row in cursor:
        if bool(Loeschen) == True:
            if row[0] in Loesch_Typ:
                cursor.deleteRow()

###########################################################################
#--VISUM-Streckentypen hinzufügen--#
###########################################################################
if bool(Typen) == True:
    arcpy.AddMessage("--Beginne mit der Erstellung der VISUM-Streckentypen--")
    arcpy.AddField_management(FC, 'STRECKENTYPEN', "LONG")
    arcpy.AddField_management(FC, 'STRECKENKLASSEN', "SHORT")

    """Wechsle in das Modul mit den Brückenschlüsseln und führe es aus!"""
    Typ(FC)

###########################################################################
#--Knoten--#
###########################################################################
if bool(Knoten) == True:
    arcpy.AddMessage("--Erstelle die Knoten--")
    arcpy.FeatureVerticesToPoints_management(FC, Knoten_Name, "BOTH_ENDS")
    arcpy.AddMessage("--Lösche gestapelte Knoten--")
    arcpy.AddXY_management(Knoten_Name) ##legt Koordinatenfelder an.
    fields = ["POINT_X", "POINT_Y"]
    arcpy.DeleteIdentical_management(Knoten_Name, fields)
    arcpy.DeleteField_management(Knoten_Name, fields)

###########################################################################
#--Trennen--#
###########################################################################
if bool(Trennen) == True:
    arcpy.AddMessage("--Trenne die Strecken an den Knoten--")
    arcpy.SplitLineAtPoint_management(FC, Knoten_Name, Trennen_Name, Radius)

###########################################################################
#--doppelte VISUM-Knoten und Strecken vermeiden--#
###########################################################################

if bool(Doppelt_Knoten) or bool(Doppelt_Strecken) == True:
    VISUM = win32com.client.dynamic.Dispatch("Visum.Visum.14")
    VISUM.loadversion(Netz)
    VISUM.Filters.InitAll() ##entfernt erstmal alle Filter

if bool(Doppelt_Knoten) == True:
    arcpy.AddMessage("--Erstelle eindeutige Knoten-IDs--")
    arcpy.AddField_management(Knoten_Name, "ID", "LONG")
    Nodes = numpy.array(VISUM.Net.Nodes.GetMultiAttValues("No")).astype("int")[:,1] ##Nimmt nur die Spalte mit den Knotennummern
    with arcpy.da.UpdateCursor(Knoten_Name, ['ID']) as cursor: ##zum erstellen eindeutiger IDs
        Wert = 20000 ##wegen Nummernvergabe der Haltestellen
        for row in cursor:
            while Wert in Nodes: ##Solange Wert in en bestehenden Knoten schon vorhanden ist, jeweils '1' addieren.
                Wert = Wert+1
            row[0] = Wert ##erstelle erstmal eindeutige IDs
            cursor.updateRow(row)
            Wert = Wert+1

if bool(Doppelt_Strecken) == True:
    if Trennen_Name != True:
        Trennen_Name = FC ##Fals nur die eindeutigen IDs generiert werden sollen.
        arcpy.AddMessage("FALSE")
    arcpy.AddMessage("--Erstelle eindeutige Strecken-IDs--")
    arcpy.AddField_management(Trennen_Name, "ID", "LONG")
    Links = numpy.array(VISUM.Net.Links.GetMultiAttValues("No")).astype("int")[:,1] ##Nimmt nur die Spalte mit den Knotennummern
    with arcpy.da.UpdateCursor(Trennen_Name, ['ID']) as cursor: ##zum erstellen eindeutiger IDs
        Wert = 20000
        for row in cursor:
            while Wert in Links:
                Wert = Wert+1
            row[0] = Wert ##erstelle erstmal eindeutige IDs
            cursor.updateRow(row)
            Wert = Wert+1

hh
###########
#--Ende--#
###########
arcpy.AddMessage("--Berechnung erfolgreich!--")