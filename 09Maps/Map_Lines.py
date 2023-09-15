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
COL_NAME = ""
TEST_COL = ""


aprx = arcpy.mp.ArcGISProject(PROJECT_NAME)
lyt = aprx.listLayouts()[0]
lyr = aprx.listMaps()[0].listLayers()[0]

val = arcpy.da.FeatureClassToNumPyArray(lyr,[COL_NAME])
uval = np.unique(val)

for i in uval:
    NO = str(i[0])
    print("> exporting line: "+NO)
    query = f"LINE_LIN_2 = '{NO}'"
    lyr.definitionQuery = query
    
    if len(np.unique(arcpy.da.FeatureClassToNumPyArray(lyr,[TEST_COL]))) <2: continue
    
    mf = lyt.listElements('MAPFRAME_ELEMENT')[0]
    mf.camera.setExtent(mf.getLayerExtent(lyr, False, True))
    PATH = glob(os.path.expanduser("~\\*\\Desktop"))[0]
    try: lyt.exportToJPEG(PATH+"\\Routen\\"+NO+".jpg")
    except: print("> ERROR: "+NO)