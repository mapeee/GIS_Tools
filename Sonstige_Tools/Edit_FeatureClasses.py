# -*- coding: cp1252 -*-
#!/usr/bin/python
#
#Marcus September 2017
#für Python 2.7.5
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mape
#
# Created:     13/09/2017
# Copyright:   (c) mape 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

#---Vorbereitung---#
import arcpy

GDB = ["Names_of_GDBs"]

for work in GDB:
    arcpy.env.workspace = "C:\\Default.gdb"  ##Link to GDBs
    fc = arcpy.ListFeatureClasses()
    print(work)

    for i in fc:
        if "Potenzial" in i: continue
#        print i
        if "PuR" in i:continue
        
        f = arcpy.ListFields(i)
        for fields in f:
            if "pkw_" in fields.name:
                with arcpy.da.UpdateCursor(i, [fields.name]) as cursor:
                    for row in cursor:
                        if row[0] == 999: continue                        
                        row[0] = row[0]-5
                        if row[0] <1:row[0] = 1
                        cursor.updateRow(row)
        
    



print "fertig"