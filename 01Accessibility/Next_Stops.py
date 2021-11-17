#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name: Next_Stops
# Purpose: Dieses Tool dient der Verknüpfung von Punkten und Haltestellenbereichen
#
#
# Author:      mape
#
# Created:     02/09/2015
# Copyright:   (c) mape 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


#---Vorbereitung---#
import arcpy
import time
import h5py
import numpy as np

start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben
arcpy.CheckOutExtension("Network")
arcpy.AddMessage("Connceting Places to Stops")
arcpy.AddMessage("Starting calculations")


#--Eingabe-Parameter--#

Start = arcpy.GetParameterAsText(0)
Start_ID = arcpy.GetParameterAsText(1)
Ziel = arcpy.GetParameterAsText(2)
Ziel_ID = arcpy.GetParameterAsText(3)
Datenbank = arcpy.GetParameterAsText(4)
Group = arcpy.GetParameterAsText(5)
Network = arcpy.GetParameterAsText(6)
Kosten = arcpy.GetParameterAsText(7) ##Das Kostenattribut (trad, Meter, etc.)
Anzahl = arcpy.GetParameterAsText(8) ##Menge zu suchender Haltestellen.
Ergebnisse = arcpy.GetParameterAsText(9)
MaxValue = arcpy.GetParameterAsText(10)
BahnFeld = arcpy.GetParameterAsText(11)
Potenzial = arcpy.GetParameterAsText(12)
Modus = ["Bus","Bahn"]
Barrieren = arcpy.GetParameterAsText(13)


#--Generierung weiterer Parameter--#
text = "Datum: "+str(time.localtime()[0:3])+", Start-Punkte: "+Start+", Ziel-Punkte: "+Ziel+", Kosten: "+Kosten+", Bus,Bahn: "+Anzahl+", Maximale Kosten: "+MaxValue ##Für das Ergebnis-Attribut

fm = ""
fm_ziel = ""
Reihen = int(arcpy.GetCount_management(Start).getOutput(0))
for field in arcpy.Describe(Start).fields:
    typ = field.type
    if typ == "OID":
        OID = field.name
    if "SourceOID" in field.name: fm = "mapping" ##No add location when positions are calculated.
for field in arcpy.Describe(Ziel).fields:
    if "SourceOID" in field.name: fm_ziel = "mapping" ##No add location when positions are calculated.

arcpy.AddMessage("Die anzubindenen Punkte enthalten "+str(Reihen)+" Zeilen und die Spalte mit den OIDs lautet: "+OID+"!")

Anzahl_Bus = int(Anzahl.split(",")[0])
Anzahl_Bahn = int(Anzahl.split(",")[1])
if Kosten == "Meter":
    MaxValue = int(MaxValue)*1000 ##um hier auf Kilometer zu kommen wie in der Beschreibung gefordert.

desc = arcpy.Describe(Network) ##ziel ist hier, die Kostenattribute zu erwischen und in eine Liste einzutragen.
attributes = desc.attributes
Kostenattribute = []
for attribute in attributes:
    b = attribute.name
    c = attribute.usageType
    if c == "Cost": ##Nehme Kostenattribute nur auf, wenn Typ = "Cost", also Kosten.
        Kostenattribute.append(b)
    else:
        continue

#--Berechnung für Bus und Bahn--"
Ergebnis_array = [] ##Wird später in HDF5-Tabelle gefüllt
if fm == "mapping": field_mappings = "Name "+Start_ID+" 0; SourceID SourceID_NMIV 0;SourceOID SourceOID_NMIV 0;PosAlong PosAlong_NMIV 0;SideOfEdge SideOfEdge_NMIV 0; Attr_tAkt # #"
if fm_ziel == "mapping": field_mappings_ziel = "Name "+Ziel_ID+" 0; SourceID SourceID_NMIV 0;SourceOID SourceOID_NMIV 0;PosAlong PosAlong_NMIV 0;SideOfEdge SideOfEdge_NMIV 0; Attr_tAkt # #"

for i,e in enumerate(Modus):
    ##Die Idee ist, erst zu allen zu Routen und danach nur die Bahnhalte auszuwählen. Da so doppelte gefunden werden,
    ##müssen diese am Ende wieder gelöscht werden. Ziel: Konflikte mit Halten vermeiden die Bus- und Bahnhalte sind.
    arcpy.AddMessage("Beginne mit der Berechnung für die "+e+"halte.")
    if i == 0: ##if-klausel für die Selection!
        Zeichen = "="
        Anzahl_Modus = Anzahl_Bus
    else:
        Zeichen = ">"
        Anzahl_Modus = Anzahl_Bahn
    if Anzahl_Modus == 0: ##wenn keine Halte zu suchen, dann weiter mit nächstem Modus.
        arcpy.AddMessage("Für "+e+" werden keine Halte berechnet!")
        continue

    #--Erstelle Selection-Layer--#
    ##Layer aus Punktshape "Ziel", Layer-Name ="lyr", Erfüllung der Einschränkung BahnFeld, ACHTUNG: mit der eckigen Klammer!!
    arcpy.MakeFeatureLayer_management(Ziel, "lyr",BahnFeld+" "+Zeichen+" 0")

    #--Erstelle ClosestFacility-Layer--#
    CFLayer = arcpy.MakeODCostMatrixLayer_na(Network,"ClosestBUSStations",Kosten,MaxValue,Anzahl_Modus,Kostenattribute,"","","","","NO_LINES")
    if fm_ziel =="mapping":arcpy.AddLocations_na(CFLayer,"Destinations","lyr",field_mappings_ziel,"","","","","","","","EXCLUDE")
    else: arcpy.AddLocations_na(CFLayer,"Destinations","lyr","Name "+Ziel_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Faehre_NMIV", "NONE"],["Ampeln", "NONE"]],"","","","","EXCLUDE") ##Das sind die Startpunkte; 0 ist der Platzhalter für ein Leerfeld!
    arcpy.AddMessage("Ziele wurden angebunden!")
    if Barrieren == "true":
        Barrieren = "C:\Geodaten\Material.gdb\Linien\Barrieren_Faehren"
        arcpy.AddLocations_na(CFLayer,"Line Barriers",Barrieren)

    #--Beginne mit der Schleifer über die einzelnen Zeilen--#
    for Zeilen in range(0,Reihen,5000): ##Beginne bei 0, bis Reihen in 5.000er Schritten.
        if Reihen>5000: ##Damit keine irreführende Ausgabe auftritt.
            arcpy.AddMessage("Beginne mit der Anbindung und Berechnung der Zeilen "+str(Zeilen)+" bis "+str(Zeilen+5000)+".")
        else:
            arcpy.AddMessage("Beginne mit der Anbindung und Berechnung von "+str(Reihen)+" Zeilen.")

        arcpy.MakeFeatureLayer_management(Start, "startlyr",OID+" >= "+str(Zeilen)+" and "+OID+" < "+str(Zeilen+5000))

        if fm == "mapping":arcpy.AddLocations_na(CFLayer,"Origins","startlyr",field_mappings,"","","","","CLEAR","","","EXCLUDE")
        else: arcpy.AddLocations_na(CFLayer,"Origins","startlyr","Name "+Start_ID+" 0; Attr_tFuss # #","","",[["MRH_Wege", "SHAPE"],["Faehre_NMIV", "NONE"],["Ampeln", "NONE"]],"","CLEAR","","","EXCLUDE") ##EXCLUDE: nur an Netzwerkelemente, die mit Gesamtnetz verbunden sind!
        ##arcpy.AddLocations_na(CFLayer,"Incidents","startlyr","Name "+Start_ID+" 0; Attr_Minutes # #","","","","","CLEAR","","","EXCLUDE")
##        arcpy.management.SaveToLayerFile(CFLayer,"C:\\Geodaten\\CF_Ergebnis"+e,"RELATIVE")
        try:
            arcpy.Solve_na(CFLayer,"SKIP") #SKIP:Not Located wird übersprungen.
            arcpy.AddMessage("--Solver erfolgreich ausgeführt für "+e+"--")
        except: ##Wenn Fehler im Solver, Hinweis auf Zeilen sowie löschen vom start-layer.
            arcpy.AddMessage("FEHLER zwischen den Zeilen "+str(Zeilen)+" bis "+str(Zeilen+5000)+"!!!")
            arcpy.Delete_management("startlyr") ##Delete der Schleife über jeweils 5.000 Startpunkte
            continue

        #--Füge Ergebnisse in Ergbnistabelle ein--#
        arcpy.AddMessage("Füge Ergebnisse in Ergbnistabelle ein.")
        rows = arcpy.SearchCursor("ClosestBUSStations\Lines") ##Setze Coursor zum Abrufen in Layer "Routes"
        row = rows.next()
        while row:
            l = (int(row.NAME.split(" - ")[0]),int(row.NAME.split(" - ")[1]),int(i)) ##die drei standardwerte
            for field in Kostenattribute:
                field = "Total_"+field ##Spaltensyntax im GIS; Name der Spalte im Routenlayer
                a = row.getValue(field)
                l = l+(a,)
            Ergebnis_array.append(l)
            row = rows.next()
        del row,rows
        arcpy.Delete_management("startlyr") ##Delete der Schleife über jeweils 1.000 Startpunkte
        arcpy.AddMessage("Berechnung abgeschlossen nach "+str(int((time.clock() - start_time)/60))+" Minuten.")
        arcpy.AddMessage("Länge: "+str(len(Ergebnis_array)))
    arcpy.Delete_management("lyr") ##erst den Auswahl layer löschen, damit dieser später wieder neu erstellt werden kann (Schleife über Bus/Bahn).
    arcpy.AddMessage(e+"halte erfolgreich berechnet.")
    arcpy.Delete_management(CFLayer)



#--HDF5--#
file5 = h5py.File(Datenbank,'r+') ##HDF5-File
if Group in file5.keys():
    group5 = file5[Group]
    pass #'''So ändern, dass Gruppenname im Tool frei wählbar'''
else:
    group5 = file5.create_group(Group) ##erstelle die Gruppe, da sie noch nicht existiert


#--HDF5-->Ergebnistabelle--#
Spalten = [('Start_ID', 'int32'),('Ziel_Knoten', 'int32'),('Bahn', 'i2')]
for i in Kostenattribute:
    Spalten.append((i.encode('ascii'),'f8')) ##sonst Unicode. Unicode durch dtype nicht lesbar.

#--Strukturdaten HDF5--#
if Potenzial != "":
    Potenzial = Potenzial.split(";")
    Potenzial = (Start_ID.encode('ascii'),) + tuple(Potenzial) ##Um auch die Start_ID im NumpyArray zu haben
    Strukturen = arcpy.da.FeatureClassToNumPyArray(Start,Potenzial)

    #--dtypes hinzufügen--#
    dtypes = Strukturen.dtype
    for i in range(len(Potenzial)-1): ##-1 Um Start_ID nicht mitzuzählen
        Spalten.append((dtypes.names[i+1],dtypes[i+1].name)) ##+1, um die erste Spalte zu überspringen


    #--Werte zu Ergbnis_array hinzufügen--#
    for i in range(len(Ergebnis_array)):
        index = np.where(Strukturen[Start_ID.encode('ascii')]==Ergebnis_array[i][0])[0][0]
        for h in range(len(Strukturen[index])-1):
            w = Strukturen[index][h+1] ##+1, um die erste Spalte zu überspringen
            Ergebnis_array[i] = Ergebnis_array[i]+(w,)

#--Erhebnistabelle erstellen--#
Spalten = np.dtype(Spalten) ##Wandle Spalten-Tuple in dtype um
data = np.array(Ergebnis_array,Spalten)
if Ergebnisse in group5.keys():
        del group5[Ergebnisse]
dset5 = group5.create_dataset(Ergebnisse, data=data, dtype=Spalten)

#--HDF5-Text zu Tabellenbeschreibung--#
dset5.attrs.create("Parameter",str(text))

#Ende
file5.flush()
file5.close()
hh
