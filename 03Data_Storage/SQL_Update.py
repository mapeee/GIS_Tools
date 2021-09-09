# -*- coding: cp1252 -*-
#!/usr/bin/python
##kleines Script, um Daten aus GIS in eine bestehende SQL-Tabelle zu importieren.
##Marcus Februar 2014
##für Python 2.6.7

import arcpy
import time
import sys

try: ##greift vermutlich auf falsche Version (64-bit) zurück, darum neue Pfadsetzung.
    import sqlite3
except:
    sys.path = ['C:\\Python26\\Lib', 'C:\\Python26\\DLLs', 'C:\\Python26\\Lib\\lib-tk']
    import sqlite3

start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben

##Eingabe-Parameter
Shape = arcpy.GetParameterAsText(0)
ID = arcpy.GetParameterAsText(1)
Felder = arcpy.GetParameterAsText(2)
Datenbank = arcpy.GetParameterAsText(3)
Ergebnisse = arcpy.GetParameterAsText(4)
ID_SQL = arcpy.GetParameterAsText(5)

##--Füge Daten aus Strukturdaten/Potenzialen ein--##
sys.path = ['V:\\Studentische Hilfskraefte_Portal\\MarCus\\IT\\Python\\06Module'] ##der PFad zu GISQL
import GISQL
GISQL.Update_SQL(Felder,Shape,ID,Ergebnisse,Datenbank,ID_SQL)


hh
##End
arcpy.AddMessage("--Scriptdurchlauf erfolgreich nach--")
