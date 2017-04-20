# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript, mit dem der Datenaustausch mit HDF5-Datenbanken gelingt.
#Marcus September 2015
#für Python 2.7.5

#---Vorbereitung---#
import sys
sys.path.append('c:\\Program Files (x86)\\ArcGIS\\Desktop10.2\\bin')
sys.path.append('c:\\program files (x86)\\arcgis\\desktop10.2\\arcpy')
import arcpy
import time
import h5py
import numpy

arcpy.AddMessage("--Dieses Skript ermöglicht Datenaustausch zwischen GIS und HDF5-Datenbanken--")
arcpy.AddMessage("--Beginne mit der Berechnung!--")

start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben

#--Eingabe-Parameter--#
Methode = arcpy.GetParameterAsText(0)
FC = arcpy.GetParameterAsText(1)
Felder = arcpy.GetParameterAsText(2)
Felder = Felder.split(";") ##überführt den String in eine Liste mit dem Trennzeichen ";".
Datenbank = arcpy.GetParameterAsText(3)
Tabelle_E = arcpy.GetParameterAsText(4)
TabelleHDF5 = arcpy.GetParameterAsText(5)
TabelleHDF5 = TabelleHDF5.split(";")
Group = arcpy.GetParameterAsText(6)
Pfad_GIS = arcpy.GetParameterAsText(7)


arcpy.AddMessage("--Berechnung für: "+Methode.encode('ascii')+"--")


###########################################################################
#--Verbindung zur HDF-5 Datenbank--#
###########################################################################
#--Datenzugriff--#
file5 = h5py.File(Datenbank,'r+') ##HDF5-File
group5 = file5[Group]

###########################################################################
#--Berechnung--#
###########################################################################

if Methode == "HDF5_GIS":
    #--Zugriff auf HstBer der Einrichtungen--#
    for i in TabelleHDF5:
        dset = group5[i]
        a = numpy.array(dset)
        arcpy.da.NumPyArrayToTable(a,Pfad_GIS+"/"+i)

else:
    array = arcpy.da.FeatureClassToNumPyArray(FC,Felder)
    group5.create_dataset(Tabelle_E, data=array, dtype=array.dtype)



#--Ende--#
file5.flush()
file5.close()
hh
