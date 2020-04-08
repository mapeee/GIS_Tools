# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript, um unterschiedliche Zeileneinträge in unterschiedliche Spalten zu verwandeln. Es geht darum, dass einer ID mehrere Zeilen zugeordnet sind.
#Die Werte in mehreren Zeilen in einer Spalte sollen in mehrere Spalten überführt werden.
#Marcus März 2015
#für Python 2.6.7

"""
Die Idee ist die Folgende:
1.
"""

#---Vorbereitung---#
import arcpy
import time
start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben
arcpy.AddMessage("--Dieses Skript ermöglicht die Umwandlung in Spalten aus mehreren Zeilen.--")
arcpy.AddMessage("--Beginne mit der Berechnung!--")

#--Eingabe-Parameter--#
Spalten_fc = arcpy.GetParameterAsText(0)
Spalten_join = arcpy.GetParameterAsText(1)
Spalten_felder = arcpy.GetParameterAsText(2)
Zeilen_fc = arcpy.GetParameterAsText(3)
Zeilen_join = arcpy.GetParameterAsText(4)
Zeilen_spalte = arcpy.GetParameterAsText(5)

#--Generierung weiterer Parameter--#
Spalten_felder = Spalten_felder.split(";")

###########################################################################
#--Beginne mit der Berechnung--#
###########################################################################
rows = arcpy.UpdateCursor(Spalten_fc) ##Update-Cursor auf die FeatureClass mit den zu füllenden Spalten.
row = rows.next()
while row: ##Schleife über FC mit den zu füllenden Spalten.
    n = 0 ##Zähler um eine Schleife über die Spalten zu legen.
    ID_Spalte = row.getValue(Spalten_join) ##Ausgabe der ID zu jeder Zeile der Spalten-FC.
    for Zeilen_n in arcpy.da.SearchCursor(Zeilen_fc,Zeilen_spalte,Zeilen_join+"="+str(ID_Spalte)): ##Wählt aus der Zeilen-FC alle Werte in der gesuchten Spalte aus, die der Spalten-ID entspricht.
        row.setValue(Spalten_felder[n],Zeilen_n[0])
        n = n+1

    rows.updateRow(row)
    row = rows.next()

###########
#--Ende--#
###########
arcpy.AddMessage("--Berechnung erfolgreich!--")