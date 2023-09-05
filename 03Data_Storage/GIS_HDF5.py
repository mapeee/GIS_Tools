# -*- coding: cp1252 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:        GIS_HDF5
# Purpose:     Exchange of Data betweeen HDF5 and ESRI GeoDatabase
# Author:      mape
# Created:     02/09/2015 (new Version 2021)
# Copyright:   (c) mape 2015
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
import h5py
import numpy as np

#--Parameter--#
Methode = arcpy.GetParameterAsText(0)
FC = arcpy.GetParameterAsText(1)
Felder = arcpy.GetParameterAsText(2)
Felder = Felder.split(";")
Database = arcpy.GetParameterAsText(3)
Tabelle_E = arcpy.GetParameterAsText(4)
Group = arcpy.GetParameterAsText(5)
TabelleHDF5 = arcpy.GetParameterAsText(6).split(";")
Path_GIS = arcpy.GetParameterAsText(7)

#--calculation--#
file5 = h5py.File(Database,'r+')
group5 = file5[Group]

if Methode == "HDF5_to_GIS":
    for i in TabelleHDF5:
        a = np.array(group5[i])
        arcpy.da.NumPyArrayToTable(a,Path_GIS+"/"+i)
else:
    data_FC = arcpy.da.FeatureClassToNumPyArray(FC,Felder)
    group5.create_dataset(Tabelle_E, data=data_FC, dtype=data_FC.dtype)

#--End--#
file5.flush()
file5.close()