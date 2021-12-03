# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript, mit dem der Datenaustausch mit HDF5-Datenbanken gelingt.
#Marcus September 2015; new Version December 2021
#für Python 2.7.5

#---Vorbereitung---#
import sys
import arcpy
import time
import h5py
import numpy as np


#--Parameter--#
Methode = arcpy.GetParameterAsText(0)
FC = arcpy.GetParameterAsText(1)
Felder = arcpy.GetParameterAsText(2)
Felder = Felder.split(";")
Database = arcpy.GetParameterAsText(3)
Tabelle_E = arcpy.GetParameterAsText(4)
TabelleHDF5 = arcpy.GetParameterAsText(5).split(";")
Group = arcpy.GetParameterAsText(6)
Path_GIS = arcpy.GetParameterAsText(7)

#--calculation--#
file5 = h5py.File(Database,'r+')
group5 = file5[Group]

if Methode == "HDF5_to_GIS":
    for i in TabelleHDF5:
        a = np.array(group5[i])
        try:arcpy.da.NumPyArrayToTable(a,Path_GIS+"/"+i)
        except:
            arcpy.Delete_management(Path_GIS+"/"+i)
            arcpy.da.NumPyArrayToTable(a,Path_GIS+"/"+i)

else: group5.create_dataset(Tabelle_E, data=arcpy.da.FeatureClassToNumPyArray(FC,Felder), dtype=array.dtype)

#--End--#
file5.flush()
file5.close()