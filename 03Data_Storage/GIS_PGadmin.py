# -*- coding: cp1252 -*-
##kleines Script, um Daten aus PGadmin in GIS zu speichern
##Marcus November 2013
##für Python 2.6.7

import arcpy
import time
import psycopg2
start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben

##Eingabe-Parameter
Methode = arcpy.GetParameterAsText(0)

GIS = arcpy.GetParameterAsText(1)
TabName = arcpy.GetParameterAsText(2)

FC = arcpy.GetParameterAsText(3)

User = arcpy.GetParameterAsText(4)
Password = arcpy.GetParameterAsText(5)
dbname = arcpy.GetParameterAsText(6)
Schema = arcpy.GetParameterAsText(7)
Tabelle = arcpy.GetParameterAsText(8)

##Kleinschreibung einiger Parameter beachten (in PGadmin)!
User = User.lower()
dbname = dbname.lower()
Schema = Schema.lower()
Tabelle = Tabelle.lower()

##stellt Verbindung zu PGadmin her und greift die SpaltenNamen und Typen ab
pgadmin = psycopg2.connect("dbname='"+dbname+"' user='"+User+"' host='ra.vsl.tu-harburg.de' password='"+Password+"'")
pgcur = pgadmin.cursor()
arcpy.AddMessage("--Verbindung zum Server erfolgreich!--")

if Methode == "PGadmin in GIS":
    arcpy.AddMessage("--Erstelle eine Tabelle aus einer PGadmin-Datei--")
    sql = "Select * from information_schema.columns where table_schema='"+Schema+"' and table_name='"+Tabelle+"'"
    pgcur.execute(sql)
    a = pgcur.fetchall()

    ##Neue Tabelle in GIS erstellen
    if arcpy.Exists(GIS+"/"+TabName):
        arcpy.Delete_management(GIS+"/"+TabName)
        arcpy.AddMessage("--Folgende Tabelle wurde gelöscht: "+TabName+"!--")
    arcpy.CreateTable_management(GIS,TabName)
    arcpy.AddMessage("--Folgende Tabelle wurde angelegt: "+TabName+"!--")

    ##Spalten hinzufügen
    GIS = GIS+"/"+TabName ##Definiere den Pfad auf die neue Tabelle!
    for i in a:
        name = i[3]
        typ = i[7]
        if typ == "USER-DEFINED":
            arcpy.AddMessage("--Spalte "+name+" wird nicht erstellt--")
        else:
            typ = typ.replace("double precision","Double")
            typ = typ.replace("bigint","Integer")
            typ = typ.replace("character varying","String")
            typ = typ.replace("numeric","Integer")
            arcpy.AddField_management(GIS,name,typ)
            arcpy.AddMessage("--Spalte "+name+" hinzugefügt--")

    ##Zeilen aus PGadmin abfangen
    sql = "select * from "+Schema+"."+Tabelle
    pgcur.execute(sql)
    row = pgcur.fetchone()
    ##Werte in GIS überführen
    inrows = arcpy.InsertCursor(GIS)
    t_row = inrows.newRow()
    arcpy.AddMessage("--Einzufügende Zeilen wurden abgefangen und werden nun eingefügt--")
    while row:
        z = 0 ##Zähler um die richtige Zeile bei setValue zu erwischen.
        row = reversed(row)
        row = tuple(row) ##row umdrehen da die beiden Abfragen (Spalten und Zeilen) Spiegelverkehrt sind....
        for i in a:
            name = i[3]
            typ = i[7]
            if typ == "USER-DEFINED":
                z = z+1
                pass
            elif typ == "numeric" or typ == "bigint": ##muss wieder integers erstellen
                try: ##Falls Null-Value
                    t_row.setValue(name, int(row[z])) ##Par1 = Spaltenname, Par2 = Feldwert
                except:
                    t_row.setValue(name, row[z])
                z = z+1 ##muss eingerückt stehen, da row bereits bereinigt wurde!
            else:
                t_row.setValue(name, row[z]) ##Par1 = Spaltenname, Par2 = Feldwert
                z = z+1 ##muss eingerückt stehen, da row bereits bereinigt wurde!
        inrows.insertRow(t_row)
        row = pgcur.fetchone()

if Methode == "GIS in PGadmin":
    arcpy.AddMessage("--Erstelle eine Tabelle aus einer GIS-Datei in PGadmin--")
    try:
        pgcur.execute("DROP TABLE luftverkehr."+TabName)
        arcpy.AddMessage("--"+TabName+" gelöscht!--")
    except:
        arcpy.AddMessage("--Keine Tabelle gelöscht.--")

    ##Fange Spaltennamen aus GIS ab
    desc = arcpy.Describe(FC)
    fields = desc.fields
    feld = ""
    felder = ""
    for field in fields:
        name = field.name
        typ = field.type
        if typ == "OID" or typ == "Geometry": ##Erstens nicht zu gebrauchen, zweitens ungültiges Format
            arcpy.AddMessage("--Spalte "+name+" wird nicht erstellt--")
        else:
            feld = feld+name+" "+typ+", "
            felder = felder+name+", " ##damit Felder aus if-Klausel nicht in row reinrutschen!!
            arcpy.AddMessage("--Spalte "+name+" wurde erstellt--")

    ##Ersetzen der Feldnamen und Feldtypen falls mit PGadmin inkompatibel
    feld = feld.replace("String","text") ##'string' durch 'text' ersetzen
    feld = feld.replace("Double","double precision")
    feld = feld.replace("SmallInteger","smallint")
    feld = feld.replace("ANALYSE","ANALYSE_") ##wegen Analyse=SQL-Befehl in PGadmin!

    ##Erstelle die Tabelle in PGadmin
    sql = "CREATE TABLE luftverkehr."+Tabelle+" ("+feld[:-2]+")"
    pgadmin.commit()
    pgcur.execute(sql)

    ##Füllen der Tabelle mit Werten
    arcpy.AddMessage("--Fülle die neue PGadmin-Tabelle mit den GIS-Daten auf.--")
    rows = arcpy.SearchCursor(FC,"","",felder[:-2]) ##Setzt den Abfrage-Cursor auf die Tabelle!
    row = rows.next()
    while row:
        VALUES = ""
        l = []  ##erzeuge eine neue, leere Liste!
        for field in fields:
            name = field.name
            typ = field.type
            if typ == "OID" or typ == "Geometry":
                pass
            else:
                VALUES = VALUES+"%s, " ##Baue die Klammer "Values(%s, %s, %s,...)
                a = row.getValue(name)
                l.append(a)##baue eine Liste mit den einzutragenden Werten!
        sql = "INSERT INTO luftverkehr."+Tabelle+" VALUES("+VALUES[:-2]+")"
        pgcur.execute(sql,l)
        row = rows.next()

##Verbindungen speichern und schließen
pgadmin.commit()
pgcur.close()  ##pgadmin
pgadmin.close() ##pgadmin

##Ende##
Sekunden = int(time.clock() - start_time)
Minuten = int(Sekunden/60)
Stunden = int(Minuten/60)
arcpy.AddMessage("--Scriptdurchlauf erfolgreich nach",Stunden,"Stunden,",Minuten-(Stunden*60),"Minuten und",Sekunden-(Stunden*60*60+(Minuten-(Stunden*60))*60),"Sekunden!")

