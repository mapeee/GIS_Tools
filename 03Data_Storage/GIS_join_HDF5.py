# -*- coding: cp1252 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:        GIS_join_HDF5
# Purpose:     Joining HDF5-Fields to existing GIS-Table
# Author:      mape
# Created:     28/03/2022
# Copyright:   (c) mape 2022
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
import h5py
import numpy as np
import pandas as pd

FC = arcpy.GetParameterAsText(0)
FC_join = arcpy.GetParameterAsText(1)
HDF5 = arcpy.GetParameterAsText(2)
Group5 = arcpy.GetParameterAsText(3)
Table5 = arcpy.GetParameterAsText(4)
h5_join = arcpy.GetParameterAsText(5)
h5_Fields = arcpy.GetParameterAsText(6).split(";")
Field_Names = arcpy.GetParameterAsText(7).split(";")

#--HDF5--#
file5 = h5py.File(HDF5,'r+') ##HDF5-File
gr5 = file5[Group5]
dset = gr5[Table5]

#--Adding Fields--#
arcpy.AddMessage("> Adding fields \n")
for i,n in enumerate(h5_Fields):

    if "int" in dset.dtype[n].name: dtype = "LONG"
    else: dtype = "DOUBLE"
    arcpy.management.AddField(FC, Field_Names[i], dtype)

#--Data join--#
h5_Fields.append(h5_join)
Field_Names.append(FC_join)
data_FC = pd.DataFrame(arcpy.da.FeatureClassToNumPyArray(FC,FC_join))
data_h5 = pd.DataFrame(np.array(dset))[h5_Fields]
data_merge = pd.merge(data_FC, data_h5, left_on=FC_join, right_on=h5_join, how="left")

#--Update cursor--#
arcpy.AddMessage("> Adding values \n")
r = 0
with arcpy.da.UpdateCursor(FC, Field_Names) as cursor:
    for row in cursor:
        if pd.isnull(data_merge.iloc[r][1]): pass
        else:
            for i, field in enumerate(row):
                row[i] = data_merge.iloc[r][i+1]
        r+=1
        cursor.updateRow(row)

#--End--#
file5.flush()
file5.close()