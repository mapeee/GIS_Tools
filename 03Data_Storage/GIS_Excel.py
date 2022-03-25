# -*- coding: cp1252 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:        GIS_HDF5
# Purpose:     Exchange of Data betweeen HDF5 and Excel
# Author:      mape
# Created:     25/03/2022
# Copyright:   (c) mape 2022
# Licence:     CC BY-NC 4.0
#-------------------------------------------------------------------------------

import arcpy
import h5py
import numpy as np
import openpyxl as opxl
import pandas as pd

#--Parameter--#
Database = arcpy.GetParameterAsText(0)
Group = arcpy.GetParameterAsText(1)
dsetHDF5 = arcpy.GetParameterAsText(2).split(";")
Path = arcpy.GetParameterAsText(3)

file5 = h5py.File(Database,'r+')
group5 = file5[Group]
for i in dsetHDF5:
    arcpy.AddMessage("> "+i+"\n")
    data = group5[i]
    a = np.array(data)
    b = pd.DataFrame(a)
    path_xls = Path+"\\"+i+".xlsx"
    b.to_excel(path_xls)

    wb = opxl.load_workbook(path_xls)
    sheet = wb.active
    sheet.cell(1,1,unicode(data.attrs.values()[0], errors='ignore'))
    wb.save(path_xls)

#--End--#
file5.close()