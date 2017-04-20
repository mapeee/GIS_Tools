# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript, mit dem Tabellen aus HDF5-Datenbanken gelöscht werden können.
#Marcus Oktober 2015
#für Python 2.7.5

#---Vorbereitung---#
import sys
sys.path.append('c:\\Program Files (x86)\\ArcGIS\\Desktop10.2\\bin')
sys.path.append('c:\\program files (x86)\\arcgis\\desktop10.2\\arcpy')
import arcpy
import h5py

arcpy.AddMessage("--Dieses Skript ermöglicht das Löschen von Tabellen in HDF5-Datenbanken--")




#--Eingabe-Parameter--#
Datenbank = arcpy.GetParameterAsText(0)
Group5 = arcpy.GetParameterAsText(1)
TabelleHDF5 = arcpy.GetParameterAsText(2)
TabelleHDF5 = TabelleHDF5.split(";")



###########################################################################
#--Verbindung zur HDF-5 Datenbank--#
###########################################################################
#--Datenzugriff--#
file5 = h5py.File(Datenbank,'r+') ##HDF5-File
group5 = file5[Group5]

###########################################################################
#--Löschung--#
for i in TabelleHDF5:
    del group5[i]



#--Ende--#
file5.flush()
file5.close()
arcpy.AddMessage("--Erfolgreich ausgeführt--")
