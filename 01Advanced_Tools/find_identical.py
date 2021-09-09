# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 09:10:59 2020

@author: mape
"""

import arcpy

#--Parameters--#
FC = arcpy.GetParameterAsText(0)
Field = arcpy.GetParameterAsText(1)

#--calculation--#
f = []

arcpy.AddField_management(FC, "IDENT_n", "LONG")

with arcpy.da.UpdateCursor(FC,[Field,"IDENT_n"]) as cursor:
    for row in cursor:
        if row[0] in f: 
            f.append(row[0])
            row[1] = f.count(row[0])
            cursor.updateRow(row)
            continue
        else:
            row[1] = 1
            cursor.updateRow(row)
            f.append(row[0])

arcpy.AddMessage("--finish--")