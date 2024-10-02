# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 13:45:24 2023
@author: mape
"""

import arcpy
from glob import glob
import numpy as np
import os

PROJECT_NAME = "CURRENT"
COL_NAME = "LINENAME"

aprx = arcpy.mp.ArcGISProject(PROJECT_NAME)
lyt = aprx.listLayouts()[0]
lyr_old = aprx.listMaps()[0].listLayers()[0]
lyr_new = aprx.listMaps()[0].listLayers()[1]
lyr_old.definitionQuery = None
lyr_new.definitionQuery = None

val = arcpy.da.FeatureClassToNumPyArray(lyr_new,[COL_NAME])
uval = np.unique(val)

for i in uval:
    NO = i[0]
    print("> mapping line: "+NO)
    query = COL_NAME + f"='{NO}'"
    lyr_old.definitionQuery = query
    lyr_new.definitionQuery = query

    mf = lyt.listElements('MAPFRAME_ELEMENT')[0]
    mf.camera.setExtent(mf.getLayerExtent(lyr_new, False, True))
    PATH = glob(os.path.expanduser("~\\*\\Desktop"))[0]
    try: lyt.exportToJPEG(PATH+"\\Routen_2024\\"+NO+".jpg")
    except: print("> ERROR: "+NO)