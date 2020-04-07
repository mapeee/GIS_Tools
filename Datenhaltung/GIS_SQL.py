# -*- coding: cp1252 -*-
#!/usr/bin/python
##kleines Script, um Daten aus GIS in SQL-Tabelle zu speichern
##Marcus Oktober 2013
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
Methode = arcpy.GetParameterAsText(0)
GIS = arcpy.GetParameterAsText(1)
Feld = arcpy.GetParameterAsText(2)
Feld = Feld.split(";") ##überführt den String in eine Liste mit dem Trennzeichen ";".
Datenbank = arcpy.GetParameterAsText(3)
TabName_neu = arcpy.GetParameterAsText(4)
TabName = arcpy.GetParameterAsText(5)
TabName = TabName.split(";")
SQL_GIS = arcpy.GetParameterAsText(6)
arcpy.AddMessage("Berechnung: "+Methode)

##stellt Verbindung zu SQL-Datenbank her
##Datenbank = "V:\Studentische Hilfskraefte_Portal\MarCus\Projekte\SpitzenCluster\Erreichbarkeitsanalyse\SC_Erreichbarkeitsanalyse.db3"
conn = sqlite3.connect(Datenbank)
c = conn.cursor()

if Methode == "GIS_SQL":
    ##Fange Spaltennamen aus GIS ab
    c.execute("Drop Table if Exists %s" %TabName_neu)
    desc = arcpy.Describe(GIS)
    fields = desc.fields
    sql = ""
    felder = ""
    arcpy.AddMessage("Lege SQL-Tabelle an.")
    for field in fields:
        name = field.name
        typ = field.type
        for Feld_n in Feld: ##vergleicht jeweils, ob der Name auch zu den ausgewählten gehört.
            if Feld_n == name: ##hier ist der Vergleich
                if typ == "Geometry": ##Erstens nicht zu gebrauchen, zweitens ungültiges Format
                    arcpy.AddMessage("Spalte "+name+" wurde nicht erstellt.")
                elif typ == "OID": ##damit OIDs erhalten bleiben.
                    typ = "integer"
                    arcpy.AddMessage("Spalte "+Feld_n+" wurde erstellt.")
                    sql = sql+name+" "+typ+", "
                    felder = felder+name+", " ##damit 'Shape' nicht in row reinrutscht!!
                else:
                    arcpy.AddMessage("Spalte "+Feld_n+" wurde erstellt.")
                    sql = sql+name+" "+typ+", "
                    felder = felder+name+", " ##damit 'Shape' nicht in row reinrutscht!!
            else:
                pass
    sql = "CREATE TABLE "+TabName_neu+" ("+sql[:-2]+")"
    c.execute(sql)

    ##Füllen der Tabelle mit Werten
    arcpy.AddMessage("Fülle die neue SQL-Tabelle mit den GIS-Daten auf.")
    rows = arcpy.SearchCursor(GIS,"","",felder[:-2]) ##Setzt den Abfrage-Cursor auf die Tabelle!
    row = rows.next()
    while row:
        VALUES = ""
        l = []  ##erzeuge eine neue, leere Liste!
        for field in fields:
            name = field.name
            typ = field.type
            for Feld_n in Feld: ##vergleicht jeweils, ob der Name auch zu den ausgewählten gehört.
                if Feld_n == name: ##hier ist der Vergleich
                    if typ == "Geometry":
                        pass
                    else:
                        VALUES = VALUES+"?,"
                        a = row.getValue(name)
                        l.append(a)
                else:
                    pass
        sql = "INSERT INTO "+TabName_neu+" VALUES("+VALUES[:-1]+")"
        c.execute(sql,l)
        row = rows.next()

    ##Verbindungen speichern und schließen
    conn.commit() ##sqlite3

else:

    for TabNAME in TabName:
        ##Fange die Spaltennamen und Attribute aus Starttabelle ab
        sql = "PRAGMA table_info( "+TabNAME+" )"
        c.execute(sql)
        a = c.fetchall()

        ##Neue Tabelle in GIS erstellen
        if arcpy.Exists(SQL_GIS+"/"+TabNAME):
            arcpy.Delete_management(SQL_GIS+"/"+TabNAME)
            arcpy.AddMessage("Folgende Tabelle wurde geloescht: "+TabNAME+"!")
        arcpy.CreateTable_management(SQL_GIS,TabNAME)
        arcpy.AddMessage("Folgende Tabelle wurde angelegt: "+TabNAME+"!")

        ##Spalten hinzufügen
        GIS = SQL_GIS+"/"+TabNAME ##Definiere den Pfad auf die neue Tabelle!
        def addfield(Par1,Par2,Par3): ##Definiere die Funktion 'addfield' mit drei Parametern
            arcpy.AddField_management(Par1, Par2, Par3) ##Par1=Pfad, Par2=Name, Par3=Typ

        ##Spaltentypen identifizieren.
        sql = "SELECT * From "+TabNAME
        c.execute(sql)
        b = c.fetchone()
        for i in a: ##Ziel ist hier die Typerkennung bei Leerfeldern in der Pragma-Tabelle!
            if i[2] == "":
                if type(b[i[0]])== int:
                    z = "integer"
                elif type(b[i[0]]) == float:
                    z = "double"
                else:
                    z = "text"
            else:
                z = i[2] ##teilweise andere Bennung in SQL
                z = z.replace("NUM","text")
                z = z.replace("INT","integer")
                z = z.replace("INTEGER","integer")
                z = z.replace("REAL","double")
            if i[1] == "Start_ID": #Für Sonderfall in IVM-Projekt!!!
                z = "double"
            addfield(GIS,i[1],z)
            arcpy.AddMessage("Spalte "+str(i[1])+" hinzugefügt.")
        del b

        ##Werte in GIS überführen
        inrows = arcpy.InsertCursor(GIS) ##Setze Cursor zum Einfügen in die Ergebnistabelle
        t_row = inrows.newRow() ##erstellt ein leeres Zeilenobjekt
        sql = "SELECT * From "+TabNAME
        c.execute(sql)
        row = c.fetchone() ##rufe erste Zeile ab
        def addvalue(Par1,Par2): ##definierte Funktion zum Feld hinzufügen
            t_row.setValue(Par1, Par2) ##Par1 = Spaltenname, Par2 = Feldwert
        arcpy.AddMessage("Feldwerte werden hinzugefügt!")

        while row: ##für jede Zeile
            for i in a: ##Spalten aus SQL-PRAGMA
                f = i[1] ##Spaltenname
                z = row[i[0]] ##Holt den Wert aus row[xy] und und Spalte mit der Nummer i[0] aus a.
                addvalue(f,z)
            inrows.insertRow(t_row)
            row = c.fetchone()

        del row, t_row, inrows
        ##Verbindungen speichern und schließen
        conn.commit() ##sqlite3
hh
##Ende
