# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript, mit dem der Datenaustausch mit HDF5-Datenbanken gelingt.
#Marcus September 2015
#für Python 2.7.5
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mape
#
# Created:     15/06/2017
# Copyright:   (c) mape 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

#---Vorbereitung---#
import arcpy
import h5py
import numpy as np
from pathlib import Path
path = Path.home() / 'python32' / 'python_dir.txt'
f = open(path, mode='r')
for i in f: path = i
path = Path.joinpath(Path(r'C:'+path),'GIS_Tools','HDF5_to_GIS_join.txt')
f = path.read_text()
f = f.split('\n')


GIS_Layer = arcpy.GetParameterAsText(0)
HDF5_Tabelle = arcpy.GetParameterAsText(1)
GIS_Ergebnisse = arcpy.GetParameterAsText(2)
Modus = arcpy.GetParameterAsText(3)
Join = arcpy.GetParameterAsText(4)
Layer_Name = arcpy.GetParameterAsText(5)
Spalte_Name = arcpy.GetParameterAsText(6)

#--HDF5--#
HDF5 = "V:"+f[0]
file5 = h5py.File(HDF5,'r+') ##HDF5-File
group5 = file5["Ergebnisse"]


#--HDF5 in GIS--#
arcpy.AddMessage("--Kopiere HDF5-Tabelle--")
dset = group5[HDF5_Tabelle]
a = np.array(dset)

try:
    arcpy.da.NumPyArrayToTable(a,"C:"+f[1]+HDF5_Tabelle)
except:
    arcpy.Delete_management("C:"+f[1]+HDF5_Tabelle)
    arcpy.da.NumPyArrayToTable(a,"C:"+f[1]+HDF5_Tabelle)


#--Copy Feature--#
arcpy.AddMessage("--Kopiere GIS-Layer--")
try: arcpy.CopyFeatures_management(GIS_Layer,GIS_Ergebnisse)
except:
    arcpy.Delete_management(GIS_Ergebnisse)
    arcpy.CopyFeatures_management(GIS_Layer,GIS_Ergebnisse)

#--JOIN--#
arcpy.AddMessage("--Joine die Felder an den GIS-Layer--")
inFeatures = GIS_Ergebnisse
injoinField = "ID"
joinTable = "C:"+f[1]+HDF5_Tabelle
outjoinField = "Start_ID"
if "OEV" in Modus: fieldList = ["Reisezeit","UH","BH","Ziel_ID","Anbindungszeit","Abgangszeit"]
else: fieldList = ["Reisezeit","Ziel_ID","Meter","tAktRad"]

arcpy.JoinField_management (inFeatures, injoinField, joinTable, outjoinField, fieldList)

#--Feldnamen ändern--#
arcpy.AddMessage("--Aendere die Feldnamen--")
if "OEV" in Modus:
    arcpy.AlterField_management(GIS_Ergebnisse, "UH", "Umstiege", "Umstiege")
    arcpy.AlterField_management(GIS_Ergebnisse, "BH", "Verbindungen", "Verbindungen")
    arcpy.AlterField_management(GIS_Ergebnisse, "Reisezeit", "Minuten", "Minuten")
else: arcpy.AlterField_management(GIS_Ergebnisse, "Reisezeit", "Gehzeit", "Gehzeit")

#--NULL-Values entfernen--#
arcpy.AddMessage("--NULL-Values entfernen--")
arcpy.MakeFeatureLayer_management(GIS_Ergebnisse, "Shape")

if "OEV" in Modus:
    Layer = arcpy.SelectLayerByAttribute_management("Shape","NEW_SELECTION","Minuten is NULL")
    arcpy.CalculateField_management(Layer,"Anbindungszeit",999)
    arcpy.CalculateField_management(Layer,"Abgangszeit",999)
    arcpy.CalculateField_management(Layer,"Umstiege",999)
    arcpy.CalculateField_management(Layer,"Verbindungen",999)
    arcpy.CalculateField_management(Layer,"Ziel_ID",999)
    arcpy.CalculateField_management(Layer,"Minuten",999)
else:
    Layer = arcpy.SelectLayerByAttribute_management("Shape","NEW_SELECTION","Gehzeit is NULL")
    arcpy.CalculateField_management(Layer,"Ziel_ID",999)
    arcpy.CalculateField_management(Layer,"Meter",999)
    arcpy.CalculateField_management(Layer,"tAktRad",999)
    arcpy.CalculateField_management(Layer,"Gehzeit",999)
arcpy.SelectLayerByAttribute_management("Shape", "CLEAR_SELECTION")

#--Join der Namen der Strukturen--#
if Join == "Ja":
    arcpy.AddMessage("--Joine die Struktur-Namen--")
    arcpy.JoinField_management("Shape", "Ziel_ID", Layer_Name,"ID", Spalte_Name)
    Layer = arcpy.SelectLayerByAttribute_management("Shape","NEW_SELECTION","Ziel_ID = 999") ##Da sonst Join der Ziel-ID 999
    arcpy.CalculateField_management(Layer,Spalte_Name,'"nicht vorhanden"')


arcpy.Delete_management("C:/Geodaten/Material.gdb/"+HDF5_Tabelle)



arcpy.AddMessage("--FERTIG--")
hh
