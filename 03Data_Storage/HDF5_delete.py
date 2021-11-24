# -*- coding: cp1252 -*-
#!/usr/bin/python
#Oktober 2015
#für Python 2.7.5

#---Vorbereitung---#
import sys
import arcpy
import h5py

#--Eingabe-Parameter--#
Datenbank = arcpy.GetParameterAsText(0)
Group5 = arcpy.GetParameterAsText(1)
TabelleHDF5 = arcpy.GetParameterAsText(2)
TabelleHDF5 = TabelleHDF5.split(";")

#--connecting--#
file5 = h5py.File(Datenbank,'r+') ##HDF5-File
group5 = file5[Group5]

for i in TabelleHDF5: del group5[i]

#--end--#
file5.flush()
file5.close()