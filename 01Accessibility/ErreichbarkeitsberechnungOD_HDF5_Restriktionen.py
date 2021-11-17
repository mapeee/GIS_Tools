# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript zur Berechnung von Erreichbarkeitspotenzialen aus einer GIS OD-Matrix.
#Marcus März 2016
#für Python 2.7.5

"""
Die Idee ist die Folgende:
pass
"""

#---Vorbereitung---#
import arcpy
import time
import h5py
import numpy as np
import pandas

from pathlib import Path
path = Path.home() / 'python32' / 'python_dir.txt'
f = open(path, mode='r')
for i in f: path = i
path = Path.joinpath(Path(r'C:'+path),'Accessibility_Tools','ArcGIS_Tools','OD_HDF5_restr.txt')
f = path.read_text()
f = f.split('\n')

start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben
arcpy.AddMessage("--Dieses Skript ermöglicht die Potenzialberechnung von ausgewählten Standorten.--")
arcpy.AddMessage("--Beginne mit der Berechnung!--")


#--Eingabe-Parameter--#
Datenbank = arcpy.GetParameterAsText(0)
Group = arcpy.GetParameterAsText(1)
Tabelle_E = arcpy.GetParameterAsText(2) ##Name der Ergebnistabelle
Routen = arcpy.GetParameterAsText(3) ##Shape mit den Routen aus der OD-Cost-Matrix
Kosten = arcpy.GetParameterAsText(4)
Layer_E = arcpy.GetParameterAsText(5)
ID_E = arcpy.GetParameterAsText(6)
Layer_S = arcpy.GetParameterAsText(7)
ID_S = arcpy.GetParameterAsText(8)
Strukturen = arcpy.GetParameterAsText(9)

Kostenschranke = arcpy.GetParameterAsText(10)
Verfahren = arcpy.GetParameterAsText(11)
sumfak = arcpy.GetParameterAsText(12)
potfak = arcpy.GetParameterAsText(13)

#--Generierung weiterer Parameter--#
Strukturen = Strukturen.split(";")
Verfahren = Verfahren.split(";")
potfak = potfak.replace(",",";") ##Damit das auch für "," funktioniert.
potfak = potfak.split(";")
sumfak = sumfak.replace(",",";") ##Damit das auch für "," funktioniert.
sumfak = sumfak.split(";")

text = "Datum: "+str(time.localtime()[0:3])+"; Tabelle_E: "+Layer_E+", Tabelle_S: "+Layer_S  ##Für das Ergebnis-Attribut

###########################################################################
#--Verbindung zur HDF-5 Datenbank--#
###########################################################################

#--Datenzugriff--#
file5 = h5py.File(Datenbank,'r+') ##HDF5-File
group5 = file5[Group]

###########################################################################
#--Aufbau der Schleife--#
###########################################################################
Network = "C:"+f[0]+"\Wegenetz\Wegenetz"
ODLayer = "ODLayer"
Radius = 3500
Radius_AP = 7500
Routen = "ODLayer\Lines"
Szenario = ["N","Variante"]
arcpy.MakeFeatureLayer_management("C:"+f[0]+"\Wegenetz\Radschnellwege", "Variante")
arcpy.MakeFeatureLayer_management("C:"+f[0]+"\Raster\MRH_EW_ha", "Raster")
arcpy.MakeFeatureLayer_management("C:"+f[1]+"\MRH_AP_Strab_2011_Merge", "APs","AP>0")

desc = arcpy.Describe(Network)

#--Liste aller Restriktionen--#
l = arcpy.mapping.Layer("OD Cost Matrix")
p = arcpy.na.GetSolverProperties(l)
Restriction_0 = list(p.restrictions) ##erstelle Liste mit allen Restriktionen

for k in desc.attributes:
    for s in Szenario:
        if k.usageType != "Restriction": ##Führe die Berechnungen nur für Restrictionen durch
            continue
        Variante = str(getattr(k,"data1")).split("[")[1][:-1]
        Variante = Variante.split(",")
        Name = k.name

        if Name not in ["K_Ost_Barsbuettel","K_Ost_Glinde","K_Ost_Reinbek"]:
            continue

        if s == "Variante":
            Tabelle_E = "Variante_"+str(Name)
        else:
            Tabelle_E = "Nullfall_"+str(Name)

        arcpy.AddMessage("--Beginne die Berechnung ("+s+") für Route "+str(Name)+"--")

        #--erstellen des OD-Layers--#
        arcpy.na.MakeODCostMatrixLayer(Network,"ODLayer","tAkt_Rad",20,"","tAkt_Rad","","","","","NO_LINES","")


        #--Auswahl der Restriktion--#
        l = arcpy.mapping.Layer(ODLayer)
        p = arcpy.na.GetSolverProperties(l)
        p.restrictions = Restriction_0 ##Erstmal wieder alle Restriktionen einschalten
        if s == "Variante":
            Restriction = p.restrictions ##erstelle Liste mit allen Restriktionen
            try: ##Fals es die nicht gibt / Es nicht geht
                Restriction.remove(Name) ##entfernene aus dieser Liste die betrachtete Restriktion
                if Name == "K_Hafen":
                    Restriction.remove("K_Buxtehude")
                if Name == "K_Finkenwerder":
                    Restriction.remove("K_Buxtehude")
                if Name == "Stade_Harburg":
                    Restriction.remove("K_Buxtehude")
                if Name == "K_Ost_Barsbuettel":
                    Restriction.remove("K86")
                if Name == "K_Ost_Reinbek":
                    Restriction.remove("K86")
                    Restriction.remove("K87")
                    Restriction.remove("K84")
                if Name == "K_Ost_Glinde":
                    Restriction.remove("K86")
                    Restriction.remove("K87")

                p.restrictions = Restriction ##setze diese Liste wieder gleich den Restriktionen
            except:
                continue

        arcpy.SelectLayerByAttribute_management("Variante", "CLEAR_SELECTION") ##Erstmal alle Selections entfernen
        for var in Variante:
            arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = "+var)
            if Name == "K_Hafen":
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 61")
            if Name == "K_Finkenwerder":
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 61")
            if Name == "Stade_Harburg":
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 61")
            if Name == "K_Ost_Glinde":
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 86")
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 87")
            if Name == "K_Ost_Reinbek":
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 86")
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 87")
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 84")
            if Name == "K_Ost_Barsbuettel":
                arcpy.SelectLayerByAttribute_management("Variante","ADD_TO_SELECTION","Variante = 86")

        Bereich = arcpy.SelectLayerByLocation_management("Raster","WITHIN_A_DISTANCE","Variante",Radius)
        Bereich_AP = arcpy.SelectLayerByLocation_management("APs","WITHIN_A_DISTANCE","Variante",Radius_AP)

        arcpy.AddMessage("--Füge die Strukturen hinzu...--")
        arcpy.na.AddLocations(ODLayer,"Destinations",Bereich_AP,"Name ID_StrAb 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"]],"","CLEAR","","","EXCLUDE")
        arcpy.AddMessage("--Füge die Startpunkte hinzu...--")
        arcpy.na.AddLocations(ODLayer,"Origins",Bereich,"Name ID 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"]],"","CLEAR","","","EXCLUDE")
        arcpy.AddMessage("--Starte den SOLVER--")
        arcpy.na.Solve(ODLayer)

        ##continue

        #--Object_ID Origins--#
        ##Durch das neuerliche Adden von Origins wird die ObjectID immer fortgesetzt. Das script geht jedoch davon aus, dass diese immer bei 1 beginnt. Der Versatz zu 1 soll hier ermittelt werden.
        OID_Min = arcpy.da.FeatureClassToNumPyArray(ODLayer+"\Origins","ObjectID")
        OID_Min = np.min(OID_Min["ObjectID"])



    ###########################################################################
    #--Abschluss der Schleife / Beginne die Berechnung--#
    ###########################################################################
        arcpy.AddMessage("--Bereite die Berechnung der Indikatoren vor--")
        #--Erhebnistabelle erstellen--#
        Spalten = [('ID','int32')]

        Indikatoren = 0 ##Um die Anzahl unterschiedlicher Indikatoren zu ermitteln
        for i in Verfahren:
            for e in Strukturen:
                if i=="Reisebudget":
                    for f in sumfak:
                        Spalten.append(((e+"SUM"+str(f)).encode('ascii'),'int32'))
                        Indikatoren = Indikatoren+1
                if i=="Erreichbarkeitspotenzial":
                    for f in potfak:
                        f = f.split(".")[1] ##Um auch dreistellige Potenzialfaktoren zu berücksichtigen
                        f = f+"0"
                        Spalten.append(((e+"EXP"+str(f[:3])).encode('ascii'),'int32'))
                        Indikatoren = Indikatoren+1
                if i=="Closest":
                    Spalten.append(((e+"CLOSE").encode('ascii'),'int32'))
                    Indikatoren = Indikatoren+1

        Spalten = np.dtype(Spalten) ##Wandle Spalten-Tuple in dtype um
        Ergebnis_array = []
        data = np.array(Ergebnis_array,Spalten)
        if Tabelle_E in group5.keys():
            del group5[Tabelle_E] ##Ergebnisliste wird gelöscht falls schon vorhanden
        group5.create_dataset(Tabelle_E, data=data, dtype=Spalten, maxshape = (None,))
        Ergebnis_T = group5[Tabelle_E]
        file5.flush()


        ###########################################################################
        #--Berechnung--#
        ###########################################################################
        """
        Die Vartiante mit den "OD Cost Matrix Layern" wird gewählt, damit nur die Start- und Zielpunkte ausgewählt werden,
        die nach einer etwaigen Raumauswahl zu den Origins und Destinations hinzugefügt wurden.
        """
        #--IDs der Startpunkte--#
        Startpunkte = arcpy.da.FeatureClassToNumPyArray(ODLayer+"\Origins","Name")
        df_E = pandas.DataFrame(Startpunkte)
        df_E["Name"] = df_E["Name"].astype(int)

        Startpunkte = arcpy.da.FeatureClassToNumPyArray(Layer_E,ID_E)
        df_Elayer = pandas.DataFrame(Startpunkte)
        df_Elayer[ID_E] = df_Elayer[ID_E].astype(int)

        df_E = pandas.merge(df_E,df_Elayer,left_on="Name",right_on=ID_E)
        del df_E["Name"]


        #--Angaben der Strukturpunkte--#
        df_S = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(ODLayer+"\Destinations","Name"))
        df_S["Name"] = df_S["Name"].astype(int)

        Spalten = Strukturen
        Spalten.append(ID_S) ##Um anschließend auch die ID abzufragen
        Strukturen = Strukturen[:-1] ##Da auch an die Strukturen der append angehängt wurde...
        Struktur = arcpy.da.FeatureClassToNumPyArray(Layer_S,Spalten)
        df_Slayer = pandas.DataFrame(Struktur)
        df_Slayer[ID_S] = df_Slayer[ID_S].astype(int)

        df_S = pandas.merge(df_S,df_Slayer,left_on="Name",right_on=ID_S)
        del df_S["Name"]


        #--Bauen der Schleifen über die Linien/Routen--#
        OID_Anzahl = len(df_E)
        z = 0
        arcpy.AddMessage("--Insgesamt werden Indikatoren  für: "+str(OID_Anzahl)+" Punkte berechnet--")
        Hunderter = (OID_Anzahl/100)+1 ##+1 um mit ungeraden Werten umzuegehn (Beispiel OID_Anzahl = 201, dann muss auch Nummer 201 noch berücksichtigt werden, wenn Hunderter = 2)
        for h in range(Hunderter):
            arcpy.AddMessage("--Berechne bis Einrichtung "+str((h+1)*100)+" von "+str(OID_Anzahl)+"--")
            Lines = arcpy.da.FeatureClassToNumPyArray(Routen,["Name",Kosten],"OriginID >= "+str((h*100)+OID_Min)+" and OriginID < "+str(((h+1)*100)+OID_Min))
            if h+1 == len(range(Hunderter)):
                Lines = arcpy.da.FeatureClassToNumPyArray(Routen,["Name",Kosten],"OriginID >= "+str((h*100)+OID_Min)) ##Für den letzten Schleifendurchlauf. h+1, da erstes Element = 0
            df = pandas.DataFrame(Lines) ##Erstelle daraus ein Pandas-DatenFrame
            a = pandas.DataFrame(df.Name.str.split(' - ').tolist(), columns = "Start Ziel".split())
            df["Start"] = a["Start"] ##hänge die Spalte Start aus a an.
            df["Ziel"] = a["Ziel"]
            df[["Ziel","Start"]] = df[["Ziel","Start"]].astype(int) ##sonst klappt der join nicht
            del a
            del df["Name"]
            df = df[df[Kosten]<=int(Kostenschranke)]


            #--Join der Startpunkte--#
            df = pandas.merge(df,df_E,left_on="Start",right_on=ID_E)


            #--Join der Strukturdaten--#
            df = pandas.merge(df,df_S,left_on="Ziel",right_on=ID_S)


            ###########################################################################
            #--Berechnung--#
            ###########################################################################
            #--Schleife über alle Startpunkten-IDs--#
            Startpunkte = pandas.unique(df[ID_E])
            for s in Startpunkte:
                z = z+1
                #arcpy.AddMessage("--Berechne Indikatoren für Punkt "+str(z)+" von "+str(OID_Anzahl)+"--") ##+1, da sonst Beginn bei 0
                t1 = time.clock()

                Ergebnis = []
                Ergebnis.append(s)
                df_V = df[df[ID_E]==s]
                if len(df_V) == 0: ##Falles es keine zutreffende Verbindungen gibt
                    for e in range(Indikatoren):
                        Ergebnis.append(0)
                    Ergebnis =[tuple(Ergebnis)]
                    size = len(Ergebnis_T)
                    Ergebnis_T.resize((size+1,))
                    Ergebnis_T[size:(size+1)] = Ergebnis
                    file5.flush()
                    continue

                for i in Verfahren:
                    for e in Strukturen:
                        #--Reisebudget--#
                        if i=="Reisebudget":
                            for n in sumfak:
                                Indi = df_V[df_V[Kosten]<=int(n)]
                                Wert = Indi[e].sum()
                                Ergebnis.append(Wert)

                        #--Potenzialindikator--#
                        if i=="Erreichbarkeitspotenzial":
                            for n in potfak:
                                n = float(n)
                                Wert = round(sum(np.exp(df_V[Kosten]*n) * df_V[e]))
                                Ergebnis.append(Wert)

                        #--Closest--#
                        if i =="Closest":
                            Indi = df_V[df_V[Kosten]<=int(Kostenschranke)]
                            Indi = Indi[Indi[e]>0] ##Wähle nur die Zielezellen aus, wo überhaupt das Ziel vorhanden ist.
                            if len(Indi) == 0: ##wenn keine Einrichtung in Maximalzeit erreicht wird, dann 999
                                Ergebnis.append(int(999))
                                continue
                            Wert = np.min(Indi[Kosten]) ##Wähle dann die minimalen Kosten
                            Ergebnis.append(int(Wert))

                #--Fülle Daten in HDF5-Tabelle--#
                Ergebnis =[tuple(Ergebnis)]
                size = len(Ergebnis_T)
                Ergebnis_T.resize((size+1,))
                Ergebnis_T[size:(size+1)] = Ergebnis
                file5.flush()
                Ergebnis_T.attrs.create("Parameter",str(text))
                ## arcpy.AddMessage("--Berechnung für Punkt "+str(z)+" erfolgreich nach "+str(int(time.clock())-int(t1))+" Sekunden--")
            file5.flush()
            del Lines, df
        del df_E, df_S, Ergebnis_array, Ergebnis_T, Ergebnis
        arcpy.Delete_management(ODLayer)



###########
#--Ende--#
###########
file5.flush()
file5.close()