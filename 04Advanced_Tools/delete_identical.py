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

with arcpy.da.UpdateCursor(FC,[Field]) as cursor:
    for row in cursor:
        if row[0] in f:
            cursor.deleteRow()
            continue
        else: f.append(row[0])

arcpy.AddMessage("--finish--")