# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript, mit dem zwei Tabellen verglichen werden können
#Marcus Mai 2016
#für Python 2.7.5

"""
Die Idee ist die Folgende:
pass
"""

#---Vorbereitung---#
import sys
sys.path.append('c:\\Program Files (x86)\\ArcGIS\\Desktop10.2\\bin')
sys.path.append('c:\\program files (x86)\\arcgis\\desktop10.2\\arcpy')
import arcpy
import time
import numpy as np
import math

start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben
arcpy.AddMessage("--Dieses Skript ermöglicht den Vergleich von zwei Attributtabellen--")
arcpy.AddMessage("--Beginne mit der Berechnung!--")

#--Parameter--#
T_A = arcpy.GetParameterAsText(0)
ID_A = arcpy.GetParameterAsText(1)
Felder = arcpy.GetParameterAsText(2)
T_B = arcpy.GetParameterAsText(3)
ID_B = arcpy.GetParameterAsText(4)
Pfad_GIS = arcpy.GetParameterAsText(5)
T_E = arcpy.GetParameterAsText(6)

Felder = Felder.split(";")


#--Berechnung--#
T_A = arcpy.da.TableToNumPyArray(T_A,[f.name for f in arcpy.ListFields(T_A)])
T_B = arcpy.da.TableToNumPyArray(T_B,[f.name for f in arcpy.ListFields(T_B)])

Liste_E = []

for R_A in T_A:
    ID = R_A[ID_A]

    try: ##Falls die ID in der Zieltabelle nicht vorhanden ist.
        R_B = T_B[T_B[ID_B]==ID][0]

        Liste_R = (ID,)
        for i in Felder:
            #--absolut
            Liste_R = Liste_R + ((R_A[i]-R_B[i]),)

            #--relativ
            try:
                Liste_R = Liste_R + (((float(R_A[i])/float(R_B[i]))-1)*100,)
            except: ##Falls Division durch 0
                Liste_R = Liste_R + (0,)

    except:
        Liste_R = (ID,)
        for i in Felder:
            #--absolut
            Liste_R = Liste_R + ((99999),)
            #--relativ
            Liste_R = Liste_R + (99999,)

    Liste_E.append(Liste_R)

#--Erstelle die Ergebnistabelle--#
Spalten = [('ID', 'int32')]
for i in Felder:
    Spalten.append(((i+"abs").encode('ascii'), 'int32')) ##Muss von unicode in ascii umgewandelt werden, da die Spalten sonst nicht erzeugt werden!!!
    Spalten.append(((i+"rel").encode('ascii'), '<f8'))


Spalten = np.dtype(Spalten) ##Wandle Spalten-Tuple in dtype um
data = np.array(Liste_E,Spalten)


#--Speichern der Ergebnisse--#
arcpy.da.NumPyArrayToTable(data,Pfad_GIS+"/"+T_E)

#--Ende--#
arcpy.AddMessage("--Fertig--")