# -*- coding: cp1252 -*-
#!/usr/bin/python
#Skript, mit dem Potenziale von bestimmten Einrichtungen aus berechnet werden.
#Marcus September 2015
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
import h5py
import numpy as np
import win32com.client.dynamic
import math
import pandas
start_time = time.clock() ##Ziel: am Ende die Berechnungsdauer ausgeben
arcpy.AddMessage("--Dieses Skript ermöglicht die Potenzialberechnung von ausgewählten Standorten.--")
arcpy.AddMessage("--Beginne mit der Berechnung!--")


#--Eingabe-Parameter--#
Modus = arcpy.GetParameterAsText(0)
Datenbank = arcpy.GetParameterAsText(1)
Tabelle_A = arcpy.GetParameterAsText(2)
Knoten_A = arcpy.GetParameterAsText(3)
Tabelle_S = arcpy.GetParameterAsText(4)
Knoten_S = arcpy.GetParameterAsText(5)
Strukturgr = arcpy.GetParameterAsText(6)
Netz = arcpy.GetParameterAsText(7)
IsoChronen_Name = arcpy.GetParameterAsText(8)
Berechnung = arcpy.GetParameterAsText(9)
Group = arcpy.GetParameterAsText(10)
ID_A = arcpy.GetParameterAsText(11)
ID_S = arcpy.GetParameterAsText(12)
Tabelle_E = arcpy.GetParameterAsText(13)
k_A = arcpy.GetParameterAsText(14) ##Kostenfeld
k_S = arcpy.GetParameterAsText(15) ##Kostenfeld
kmh_A = int(arcpy.GetParameterAsText(16))
kmh_S = int(arcpy.GetParameterAsText(17))
Nachlauf = int(arcpy.GetParameterAsText(18))##für VISUM-Isochronen
Stunden = arcpy.GetParameterAsText(19)##für VISUM-Isochronen (muss String bleiben)
sumfak = arcpy.GetParameterAsText(20)
potfak = arcpy.GetParameterAsText(21)
Zeitschranke = arcpy.GetParameterAsText(30)
Zeitbezug = arcpy.GetParameterAsText(31)
Filter_S = arcpy.GetParameterAsText(32)
Group_Iso = arcpy.GetParameterAsText(33)
Filter_Gruppe = arcpy.GetParameterAsText(34)


#--Generierung weiterer Parameter--#
if "Erreichbarkeiten" in Modus:
    text = "Datum: "+str(time.localtime()[0:3])+", Modus: " +Modus+"; Zeitschranken: "+Zeitschranke+", IsoName: "+IsoChronen_Name+", Tabelle_A: "+Tabelle_A+", Tabelle_S: "+Tabelle_S+ ", Berechnungen: "+Berechnung ##Für das Ergebnis-Attribut
else:
    text = "Datum: "+str(time.localtime()[0:3])+", Modus: " +Modus+"; Zeitbezug: "+ Zeitbezug+"; Zeitschranken: "+Zeitschranke+", IsoName: "+IsoChronen_Name+", Tabelle_A: "+Tabelle_A+", Tabelle_S: "+Tabelle_S ##Für das Ergebnis-Attribut

if "keine_IsoChronen" not in Modus: ##Für die IsoChronen-Tabelle
    text_v = "Datum: "+str(time.localtime()[0:3])+", Zeitbezug: "+ Zeitbezug+", Zeitschranken: "+Zeitschranke+", Tabelle_A: "+Tabelle_A+", Tabelle_S "+Tabelle_S+", Stunden: "+Stunden+", Nachlauf: "+str(Nachlauf)+", "+Zeitbezug

Modus = Modus.split(";")
Berechnung = Berechnung.split(";")
Strukturgr = Strukturgr.split(";")
potfak = potfak.replace(",",";") ##Damit das auch für "," funktioniert.
potfak = potfak.split(";")
sumfak = sumfak.replace(",",";") ##Damit das auch für "," funktioniert.
sumfak = sumfak.split(";")
Stunden = Stunden.replace(",",";")
Stunden = Stunden.split(";")
Zeitschranke = Zeitschranke.split(";")

#--Überführung Länge in Zeit--#
if kmh_A > 0: ##für die Auswahl der HstBer über Schranke
    Schranke_A = (kmh_A/3.6*60)*int(Zeitschranke[1]) ##Schranke_A = Ernfernung (in Metern) bei x kmh und y Zeitschranke
else:
    Schranke_A = Zeitschranke[1]
if kmh_S > 0: ##für die Auswahl der HstBer über Schranke
    Schranke_S = (kmh_S/3.6*60)*int(Zeitschranke[2])
else:
    Schranke_S = Zeitschranke[2]

#--Anzahl der Einzelindikatoren--#
Indikatoren = len(Berechnung)+((len(potfak)-1)*len(Strukturgr))+((len(sumfak)-1)*len(Strukturgr)) ##-1, da einmal schon in Berechnung drinnen ist



###########################################################################
#--Vorbereitung Anbindungsberechnung--#
###########################################################################
if "Anbindung_aggregiert" in Modus or "Anbindung_disaggregiert" in Modus:
    Modus.append("Anbindung")

if "Anbindung" in Modus:
    Berechnung = ("StartHst","Ziel_ID", "ZielHst", "Reisezeit", "UH", "Anbindungszeit", "Abgangszeit")



###########################################################################
#--Verbindung zur HDF-5 Datenbank--#
###########################################################################
#--Datenzugriff--#
file5 = h5py.File(Datenbank,'r+') ##HDF5-File
group5 = file5[Group]
group5_Iso = file5[Group_Iso]

#--Zugriff auf HstBer der Einrichtungen--#
dsetA = group5[Tabelle_A]
dsetA = dsetA[dsetA[k_A]<int(Schranke_A)]
if kmh_A >0:
    dsetA[k_A] = dsetA[k_A]/(kmh_A/3.6*60) ##Um aus den Metern eine Zeit in Minuten zu machen

#--Zugriff auf HstBer der Strukturen--#
dsetS = group5[Tabelle_S]
dsetS = dsetS[dsetS[k_S]<int(Schranke_S)]
if Filter_S:
    dsetS = dsetS[dsetS[Filter_S]>0] ##Wähle nur die Anbindungen, an denen auch wirklich die gewünschten Strukturen sind.
if kmh_S >0:
    dsetS[k_S] = dsetS[k_S]/(kmh_S/3.6*60) ##Um aus den Metern eine Zeit in Minuten zu machen


###########################################################################
#--Beginne mit der Nahraum-Berechnung für jeden einzelnen Standort--#
###########################################################################
#--Parameter-Import--#
if "NMIV" in Modus:
    Radius = arcpy.GetParameterAsText(22)
    A_Shape = arcpy.GetParameterAsText(23)
    A_Shape_ID = arcpy.GetParameterAsText(24)
    S_Shape = arcpy.GetParameterAsText(25)
    S_Shape_ID = arcpy.GetParameterAsText(26)
    Network = arcpy.GetParameterAsText(27)
    Kosten = arcpy.GetParameterAsText(28)
    Max_Kosten = int(arcpy.GetParameterAsText(29))
    Barrieren = "C:\Geodaten\Material.gdb\Linien\Barrieren_Faehren" ##GIS-Shape um Fähren im Network zu unterbinden
    text = text + " NMIV-Radius: "+str(Radius)+" Minuten: "+str(Max_Kosten)

    """
    Das nachstehende Vorgehen lautet wie folgt:
    1. Wird nur durchgeführt, wenn Radius vorgegeben; sont keine Nahraumberücksichtigung.
    2. Um das Start-Shape werden in einem vorgegebenen Radius alle Ziele selectiert.
    3. Diese Ziele werden dem OD-Layer hinzugefügt.
    4. Alle Startpunkte werden dem Layer hinzugefügt.
    5. Die Berechnung wird für alle durchgeführt. Max_Kosten bezeichnet die maximale Wegedauer oder Wegelänge.
    """

    arcpy.AddMessage("--Beginne mit der Nahraumberechnung--")
    arcpy.AddMessage("--Die Anbindung erfolgt im Umkreis von maximal "+str(Radius)+" Metern--")
    arcpy.AddMessage("--Maximaler Weg: "+Kosten+" = "+str(Max_Kosten)+"!--")

    #--Löschen von Bearbeitungs-Layern--#
    arcpy.Delete_management("ODMATRIX")
    arcpy.Delete_management("intersect")

    #--Layer aus Shape-Files erstellen--#
    arcpy.MakeFeatureLayer_management(A_Shape, "A_Shape")
    arcpy.MakeFeatureLayer_management(S_Shape, "S_Shape")

    #--Nimm nur die Startpunkte die auch in der HDF5-Anbindungstabelle sind--#
    if "Erreichbarkeiten" in Modus:
        """
        Auswahl der Startpunkte wurde auskommentiert da die Sequenz dazu führt, dass nur Startpunkte zu Fuß erreicht werden dürfen, die mindestens
        eine gültige (Zeitschranke) Haltestellenanbindung besitzen!
        """
##        Startpunkte_Shape = dsetA[ID_A]
##        for i in Startpunkte_Shape:
##            arcpy.SelectLayerByAttribute_management ("A_Shape", "ADD_TO_SELECTION", A_Shape_ID+"="+str(i))

        #--Durchführung der OD-Berechnung--#
        Bereich = arcpy.SelectLayerByLocation_management("S_Shape","intersect","A_Shape",Radius)
        ODLayer = arcpy.MakeODCostMatrixLayer_na(Network,"ODMATRIX",Kosten,Max_Kosten,"","","","","","","NO_LINES")
        arcpy.AddLocations_na(ODLayer,"Origins","A_Shape","Name "+A_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"]],"","","","","EXCLUDE")
        arcpy.AddLocations_na(ODLayer,"Destinations",Bereich,"Name "+S_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"]],"","","","","EXCLUDE")
        arcpy.AddLocations_na(ODLayer,"Line Barriers",Barrieren,"","") ##Das sind die Barrieren
        arcpy.na.Solve(ODLayer)

    if "Anbindung" in Modus: ##Unterschied Anbindung <> Erreichbarkeiten: Mal sind A_Shape die wenigen, mal S_Shape die wenigen Punkte.
##        Zielpunkte_Shape = dsetS[ID_S]
##        for i in Zielpunkte_Shape:
##            arcpy.SelectLayerByAttribute_management ("S_Shape", "ADD_TO_SELECTION", S_Shape_ID+"="+str(i))

        #--Durchführung der OD-Berechnung--#
        Bereich = arcpy.SelectLayerByLocation_management("A_Shape","intersect","S_Shape",Radius)
        ODLayer = arcpy.MakeODCostMatrixLayer_na(Network,"ODMATRIX",Kosten,Max_Kosten,"","","","","","","NO_LINES")
        arcpy.AddLocations_na(ODLayer,"Origins",Bereich,"Name "+A_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"]],"","","","","EXCLUDE")
        arcpy.AddLocations_na(ODLayer,"Destinations","S_Shape","Name "+S_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"]],"","","","","EXCLUDE")
        arcpy.AddLocations_na(ODLayer,"Line Barriers",Barrieren,"","") ##Das sind die Barrieren
        arcpy.na.Solve(ODLayer)

    #--Abgreifen der Ergebniswerte--#
    Lines = arcpy.da.FeatureClassToNumPyArray("ODMATRIX\Lines",["Name", "Total_"+Kosten]) ##Erstelle Numpy-Array aus Ergebnis-Routen
    df = pandas.DataFrame(Lines) ##Erstelle daraus ein Pandas-DatenFrame
    a = pandas.DataFrame(df.Name.str.split(' - ').tolist(), columns = "Start Ziel".split())

    if "Erreichbarkeiten" in Modus:
        df[ID_S] = a["Ziel"] ##Hänge Spalte mit den Struktur-IDs an. Name wie später bei Indikatoren
        df[ID_A+"_y"] = a["Start"] ##Hänge Spalte mit den Struktur-IDs an. Name wie später bei Indikatoren
        df[[ID_S,ID_A+"_y"]] = df[[ID_S,ID_A+"_y"]].astype(int) ##Sonst klappt das Mergen später nicht
        df["UH"] = 111 ##UH = 111 bei Anbindung direkt
        df["BH"] = 11111 ##BH = Bedienhäufigkeit ist unendlich
        df["Preis"] = 0 ##Preis = 111 bei Anbindung direkt. Fuß-/Radweg ist umsonst!
        df[k_S+"_x"] = 0 ##Damit später keine 'None'-Spalte entsteht (und dann kosten + None =0)
        df = df.rename(columns = {'Total_'+Kosten:'Kosten'}) ##Ändere den Spaltennamen, für späteren Merge
        del df["Name"]

        #--Hinzufügen der Strukturgroessen--#
        Strukturgr.append(S_Shape_ID)
        Strukturen = arcpy.da.FeatureClassToNumPyArray("S_Shape",Strukturgr)
        Strukturen = pandas.DataFrame(Strukturen)
        df = pandas.merge(df,Strukturen,left_on=ID_S,right_on=S_Shape_ID)
        df = df.rename(columns = {ID_S:ID_S+'_x'})
        df = df.groupby([ID_S+"_x",ID_A+"_y"]).first()
        df = df.reset_index()


    if "Anbindung" in Modus:
        df[ID_S+"_y"] = a["Ziel"] ##Hänge Spalte mit den Struktur-IDs an. Name wie später bei Indikatoren
        df[ID_A+"_x"] = a["Start"] ##Hänge Spalte mit den Struktur-IDs an. Name wie später bei Indikatoren
        df[[ID_S+"_y",ID_A+"_x"]] = df[[ID_S+"_y",ID_A+"_x"]].astype(int) ##Sonst klappt das Mergen später nicht
        df["UH"] = 111 ##UH = 111 bei Anbindung direkt
        df["BH"] = 11111 ##BH = Bedienhäufigkeit ist unendlich
        df["Preis"] = 0 ##Preis = 111 bei Anbindung direkt. Fuß-/Radweg ist umsonst!
        df["ZielHstBer"] = 0
        df["StartHstBer"] = 0
        df[k_S+"_y"] = 0 ##Damit später keine 'None'-Spalte entsteht (und dann kosten + None =0)
        df[k_A+"_x"] = 0 ##Damit später keine 'None'-Spalte entsteht (und dann kosten + None =0)
        df = df.rename(columns = {'Total_'+Kosten:'Kosten'}) ##Ändere den Spaltennamen, für späteren Merge
        del df["Name"]

    #--Speichern des OD-Layers--#
##    arcpy.Delete_management("D:\Geodaten\ODE.lyr")
##    arcpy.management.SaveToLayerFile("ODMATRIX","D:\Geodaten\ODE","RELATIVE")

    arcpy.AddMessage("--Nahraumberechnung erfolgreich!--")

###########################################################################
#--VISUM-IsoChronenberechnung--#
###########################################################################
if "keine_IsoChronen" not in Modus:
    #--VISUM Version und Szenario--#
    arcpy.AddMessage("--Binde VISUM ein und lade Version--")
    VISUM = win32com.client.dynamic.Dispatch("Visum.Visum.15")
    ##import VISUM_Modul ##eigenes Modul  ##Szenrien sind für die aktuelle VISUM-Version nicht verfügbar
    ##VISUM_Modul.LOAD(Netz,Szenario,VISUM) ##Netz,Szenrario,VISUM-Instanz
    VISUM.loadversion(Netz) ##Netz,Szenrario,VISUM-Instanz
    ##VISUM.Filters.InitAll()

    #--Erstelle die IsoChronen-Tabelle--#
    Liste_HB = []
    if "Anbindung" in Modus and Zeitbezug == "Ankunft": ##Die Isochronen werden bei der Anbindung immer von den Strukturen/Zielen gerechnet. Wenn es sich um die Ankunftszeit handelt, ist der Abfahrtsort jedoch das Raster/der Startpunkt..
        Spalten = [('StartHstBer', 'int32'),('Kosten', '<f8'),('UH', 'i2'),('ZielHstBer', 'int32')]
    else:
        Spalten = [('ZielHstBer', 'int32'),('Kosten', '<f8'),('UH', 'i2'),('StartHstBer', 'int32')]
    if IsoChronen_Name in group5_Iso.keys():
        del group5_Iso[IsoChronen_Name]
    Spalten = np.dtype(Spalten) ##Wandle Spalten-Tuple in dtype um
    data = np.array(Liste_HB,Spalten)
    group5_Iso.create_dataset(IsoChronen_Name, data = data, dtype = Spalten, maxshape = (None,))
    file5.flush()
    IsoChronen = group5_Iso[IsoChronen_Name]


    #--IsoChronen ausgehend von Startpunkten(A)--#
    if "Anbindung" in Modus:
        HstBerA = np.unique(dsetS[Knoten_S]) ##Bei Anbindungen qusi "gedreht"
    else:
        HstBerA = np.unique(dsetA[Knoten_A])

    arcpy.AddMessage("--Insgesamt werden: "+str(len(HstBerA))+" IsoChronen berechnet--")
    for n,Nr in enumerate(HstBerA):
        Liste_HB = []
        NE = VISUM.CreateNetElements()
        NE.Add(VISUM.Net.StopAreas.ItemByKey(int(Nr)))
        Isochrones = VISUM.Analysis.Isochrones
        Isochrones.Clear()
        arcpy.AddMessage("--Berechne IsoChrone "+str(n+1)+" von "+str(len(HstBerA))+"--") ##+1, da sonst Beginn bei 0
        Isochrones.ExecutePuT(NE,"X",str(Stunden[0])+":00:00",str(Stunden[1])+":00:00",1,1,Nachlauf*60*60,bool(Zeitbezug == "Ankunft"))##bool: Ankunfts- oder Abfahrtszeit, True = Ankunft
        Ziel = list(np.array(VISUM.Net.StopAreas.GetMultiAttValues("No"))[:,1]) ##Nimmt Nummer UND Zeilennummer (beginnend bei 1)
        Zeit = list(np.array(VISUM.Net.StopAreas.GetMultiAttValues("IsocTimePuT"))[:,1]/60) ##nimmt nur Die Zeit / um aus Sekunden minuten zu machen
        UH = list(np.array(VISUM.Net.StopAreas.GetMultiAttValues("IsocTransfersPuT"))[:,1])
        for i in range(len(Ziel)):
            Liste_HB.append((Ziel[i],Zeit[i],UH[i],Nr))
        Liste_HB = np.array(Liste_HB)
        Liste_HB = Liste_HB[Liste_HB[:,1]<int(Zeitschranke[0])] ##wähle nur die Zeilen, die Zeitschranke erfüllen.

        #--Fülle Daten in HDF5-Tabelle--#
        oldsize = len(IsoChronen)
        sizer = oldsize + len(Liste_HB) ##Neue Länge der Liste (bisherige Länge + Läne VISUM-IsoChronen
        IsoChronen.resize((sizer,))
        Liste_HB = list(map(tuple, Liste_HB))
        IsoChronen[oldsize:sizer] = Liste_HB
        file5.flush()
        Isochrones.Clear()

    IsoChronen.attrs.create("Parameter",str(text_v))
    file5.flush()
    del IsoChronen
    del VISUM
    arcpy.AddMessage("--Berechnung der IsoChronen abgeschlossen nach "+str(int((time.clock() - start_time)/60))+" Minuten--")



###########################################################################
#--HDF5 --> Erstelle Ergebnistabelle--#
###########################################################################
#--HDF5-->Spalten für Ergebnistabelle--#
Ergebnis_array = []
Spalten = [('Start_ID', '<f8')]
"""
1. Für jede Berechnungsart soll eine Spalte angelegt werden.
2. Bei der Berechnung von gewichteten Potenzialen soll außerdem der Gewichtungsfaktor angehängt werden.
"""
for i in Berechnung:
    if i[-4:] == "Expo": ##wenn Expo in den letzten vier Stellen, dann zusätzlich auch Potenzial-Faktor.
        for e in potfak:
            e = str(e.split(".")[1])
            if len(e)==2:
                e+="0"
            Spalten.append(((i+e).encode('ascii'),'int32'))

    elif i[-3:] == "Sum": ##wenn Sum in den letzten drei Stellen, dann zusätzlich auch Maximalzeit anhängen.
        for e in sumfak:
            Spalten.append(((i+e).encode('ascii'),'int32'))

    else:
        Spalten.append((i.encode('ascii'),'int32'))

#--Erhebnistabelle erstellen--#
Spalten = np.dtype(Spalten) ##Wandle Spalten-Tuple in dtype um
data = np.array(Ergebnis_array,Spalten)
if Tabelle_E in group5.keys():
    del group5[Tabelle_E] ##Ergebnisliste wird gelöscht falls schon vorhanden
group5.create_dataset(Tabelle_E, data=data, dtype=Spalten, maxshape = (None,))
Ergebnis_T = group5[Tabelle_E]
file5.flush()


###########################################################################
#--Berechnung der Indikatoren (Vorbereitung)--#
###########################################################################
dataS = pandas.DataFrame(dsetS)
IsoChronen = group5_Iso[IsoChronen_Name]
try:
    Iso = IsoChronen[IsoChronen["Kosten"]<(int(Zeitschranke[0])-5)]
except:
    Iso = IsoChronen
    arcpy.AddMessage("!!!! Zeitschranke fehlt!!!!")

###########################################################################
#--Berechnung der Indikatoren (Durchführung)--#
###########################################################################
arcpy.AddMessage("--Beginne mit der Indikatorberechnung--")

    ###########################################################################
    #--Anbindungen--#
    ###########################################################################

if "Anbindung_aggregiert" in Modus:

    if Filter_Gruppe:
        Gruppen = np.unique(dsetS[Filter_Gruppe]) ##Liste aller Gruppen-Codes
    else:
        Gruppen = [1] ##Um ohne Filter dennoch ein iterierbares Objekt zu erhalten

    dataA = pandas.DataFrame(dsetA)

    if Zeitbezug == "Ankunft": ##Wenn der Zeitbezug Ankunft ist, dann sind die Strukturen/Ziele auch die ZielHstber. Bei Abfahrt, sind es die StartHstBereiche.
        Bezug1 = "ZielHstBer"
        Bezug2 = "StartHstBer"
    else:
        Bezug1 = "StartHstBer"
        Bezug2 = "ZielHstBer"

    for i, m in enumerate(Gruppen):

        if Filter_Gruppe:
            dataG = dataS[dataS[Filter_Gruppe]==m] ##wähle nur die Strukturen aus, die in der entsprechenden Gruppe sind

            try:
                Iso_p = IsoChronen[np.in1d(Iso[Bezug1],dataG[Knoten_S])] ##ZielHstBer, da die IsoChronen 'gedreht' berechnet wurden.

            except:

                """
                Da es aufgrund der großen Isochronen immer wieder zu Speicherüberlastungen kommt, wird hier ein anderes Verfahrne gewählt.
                Ziel ist es, aus der riesigen Isochronen-Tabelle nur die Verbindungen zu Filtern, die die Reisezeit zur jeder Haltestelle an den Rasterzellen minimieren.
                1. Erstellen einer Liste mit allen HstBer, die an den Rasterzellen (Startpunkten) vorkommen.
                2. Erstelle Liste mit allen HstBereichen die an Zielen vorkommen. Für jeden Raster-HstBereich soll der HstBereich der Strukturen gefunden werden, der die Reisezeit minimiert.
                3. Für jede dieser HstBer soll die geringste Reisezeit gefunden werden.
                4. Der Abgangs-HstBer ist egal, da ja aggregierte Anbindungen berechnet werden.
                """
                #1. Erstelle Liste mit allen HastBereichen an Rasterzellen. Platzhalter sind für Reisezeit, UH sowie HstBereich an Struktur.
                Raster_HstBer = np.unique(dsetA["Ziel_Knoten"]) ##Array mit allen HstBer an den Rasterzelle
                iso_neu = []
                for i in Raster_HstBer:
                    iso_neu.append((i,999,999,999))
                iso_neu = np.array(iso_neu)

                #2. Erzeuge Liste mit allen HstBereichen die an Strukturen vorkommen.
                HstBer_Ziele = dsetS[dsetS[Filter_Gruppe]==m] ##Nimm nur die Ziele, die für diese Gruppe relevant sind
                HstBer_Ziele = np.unique(HstBer_Ziele["Ziel_Knoten"]) ##Erzeuge Liste mit eindueitgen HstBereichen der Strukturen

                #3. Iteration durch alle HstBereich der Strukturen bzw. Ziele.
                for i in HstBer_Ziele:
                    Ziele = Iso[Iso[Bezug1]==i] ##Auswahl jener Isochronen, die an einem HstBereich der Strukturen beginnen (Zeitbezug: Abfahrt) bzw. enden.
                    for e in Ziele:
                        try: ##Falls es zu diesem Rast-HstBer keine Verbindung gibt, gehts nicht.
                            Verbindung = np.where(iso_neu[:,0]==e[Bezug2])[0][0]
                        except:
                            continue
                        if iso_neu[Verbindung][1]>e[1]:
                            iso_neu[Verbindung][1] = e[1]
                            iso_neu[Verbindung][2] = e[2]
                            iso_neu[Verbindung][3] = e[3]


                Iso_p = list(map(tuple, iso_neu))
                Iso_p = np.array(Iso_p,IsoChronen.dtype)
                """
                Hier endet der neu eingefügte Block zur Steigerung der Performance
                """

            dataiso = pandas.DataFrame(Iso_p)
            arcpy.AddMessage("--Beginne mit der Berechnung aggregierter Anbindungen für Gruppe "+str(m)+" mit "+str(len(np.unique(dataG[ID_S])))+" Strukturgrößen--")
            IsoS = pandas.merge(dataG,dataiso,left_on=Knoten_S,right_on=Bezug1)

        else:
            dataG = dataS ##wähle nur die Strukturen aus, die in der entsprechenden Gruppe sind

            try:
                Iso_p = IsoChronen[np.in1d(Iso[Bezug1],dsetS[Knoten_S])] ##ZielHstBer, da die IsoChronen 'gedreht' berechnet wurden!
            except:

                """
                Da es aufgrund der großen Isochronen immer wieder zu Speicherüberlastungen kommt, wird hier ein anderes Verfahrne gewählt.
                Ziel ist es, aus der riesigen Isochronen-Tabelle nur die Verbindungen zu Filtern, die die Reisezeit zur jeder Haltestelle an den Rasterzellen minimieren.
                1. Erstellen einer Liste mit allen HstBer, die an den Rasterzellen (Startpunkten) vorkommen.
                2. Erstelle Liste mit allen HstBereichen die an Zielen vorkommen. Für jeden Raster-HstBereich soll der HstBereich der Strukturen gefunden werden, der die Reisezeit minimiert.
                3. Für jede dieser HstBer soll die geringste Reisezeit gefunden werden.
                4. Der Abgangs-HstBer ist egal, da ja aggregierte Anbindungen berechnet werden.
                """
                #1. Erstelle Liste mit allen HastBereichen an Rasterzellen. Platzhalter sind für Reisezeit, UH sowie HstBereich an Struktur.
                Raster_HstBer = np.unique(dsetA["Ziel_Knoten"]) ##Array mit allen HstBer an den Rasterzelle
                iso_neu = []
                for i in Raster_HstBer:
                    iso_neu.append((i,999,999,999))
                iso_neu = np.array(iso_neu)

                #2. Erzeuge Liste mit allen HstBereichen die an Strukturen vorkommen.
                HstBer_Ziele = np.unique(dsetS["Ziel_Knoten"]) ##Erzeuge Liste mit eindueitgen HstBereichen der Strukturen

                #3. Iteration durch alle HstBereich der Strukturen bzw. Ziele.
                for i in HstBer_Ziele:
                    Ziele = Iso[Iso[Bezug1]==i] ##Auswahl jener Isochronen, die an einem HstBereich der Strukturen beginnen (Zeitbezug: Abfahrt) bzw. enden.
                    for e in Ziele:
                        try: ##Falls es zu diesem Rast-HstBer keine Verbindung gibt, gehts nicht.
                            Verbindung = np.where(iso_neu[:,0]==e[Bezug2])[0][0]
                        except:
                            continue
                        if iso_neu[Verbindung][1]>e[1]:
                            iso_neu[Verbindung][1] = e[1]
                            iso_neu[Verbindung][2] = e[2]
                            iso_neu[Verbindung][3] = e[3]


                Iso_p = list(map(tuple, iso_neu))
                Iso_p = np.array(Iso_p,IsoChronen.dtype)
                """
                Hier endet der neu eingefügte Block zur Steigerung der Performance
                """

            arcpy.AddMessage("--Beginne mit der Berechnung aggregierter Anbindungen für "+str(len(np.unique(dsetS[ID_S])))+" Strukturgrößen--")
            dataiso = pandas.DataFrame(Iso_p)
            IsoS = pandas.merge(dataG,dataiso,left_on=Knoten_S,right_on=Bezug1)



        IsoS["Kosten"] = IsoS[k_S]+IsoS["Kosten"]
        gb = IsoS.groupby(Bezug2) ##Group über HstBer
        IsoS = IsoS.iloc[gb["Kosten"].idxmin()] ##Index der Minimalen Kostenwerte; Dann slicing über diese IDs

        IsoA = pandas.merge(dataA,IsoS,left_on=Knoten_A,right_on=Bezug2)

        if "NMIV" in Modus:
            if Filter_Gruppe:
                Nahbereich = df[df[ID_S+"_y"].isin(dataG[ID_S])] ##Wähle nur die Nahbereiche für diese Einrichtung aus
                IsoA = IsoA.append(Nahbereich, ignore_index = True)
            else:
                IsoA = IsoA.append(df, ignore_index = True)

        IsoA["Kosten"] = IsoA[k_A+"_x"]+IsoA["Kosten"]
        gb = IsoA.groupby(ID_A+"_x")["Kosten"].idxmin()
        IsoA = IsoA.iloc[gb]


        #--Befülle HDF5-Ergebnistabelle--#
        """
        Wenn der Zeitbezug Abfahrt (nicht Ankunft) ist, dann bezieht sich dies auf die Abfahrt an der Struktur. Entsprechend sind die Rasterzellen dann die Zielpunkte.
        Entsprechend müssen hier die Spalten jeweils vertauscht werden.
        """
        if Zeitbezug == "Ankunft":
            Ergebnis = IsoA[["Start_ID_x","StartHstBer","Start_ID_y", "ZielHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y"]]
        else:
            Ergebnis = IsoA[["Start_ID_y","ZielHstBer","Start_ID_x", "StartHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y"]]
        Ergebnis.loc[Ergebnis["ZielHstBer"]==Ergebnis["StartHstBer"],"UH"] = 111 ##Wenn StarHstBer = ZielHstBer bedeutet das einen Direktweg, damit UH = 111
        Ergebnis = np.array(Ergebnis)
        Ergebnis = list(map(tuple, Ergebnis))
        size = len(Ergebnis_T)
        sizer = size+len(Ergebnis)
        Ergebnis_T.resize((sizer,))
        Ergebnis_T[size:sizer] = Ergebnis
        file5.flush()


if "Anbindung_disaggregiert" in Modus:
    arcpy.AddMessage("--Beginne mit der Berechnung disaggregierter Anbindungen für "+str(len(dsetS))+" Punkte--")
    Einrichtungen = np.unique(dsetS[ID_S])

    if Zeitbezug == "Ankunft": ##Wenn der Zeitbezug Ankunft ist, dann sind die Strukturen/Ziele auch die ZielHstber. Bei Abfahrt, sind es die StartHstBereiche.
        Bezug1 = "ZielHstBer"
        Bezug2 = "StartHstBer"
    else:
        Bezug1 = "StartHstBer"
        Bezug2 = "ZielHstBer"

    for i, m in enumerate(Einrichtungen):
        t1 = time.clock()
        arcpy.AddMessage("--Berechne Anbindungen für Struktur "+str(i+1)+" von "+str(len(Einrichtungen))+"--") ##+1, da sonst Beginn bei 0
        Anb = dsetS[dsetS[ID_S]==m] ##Nur Anbindung von entsprechender Einrichtung
        Iso = IsoChronen[np.in1d(IsoChronen[Bezug1],Anb[Knoten_S])] ##StartHstBer, da die IsoChronen 'gedreht' berechnet wurden!
        Iso = Iso[Iso["Kosten"]<(int(Zeitschranke[0])-5)]
        dataA = pandas.DataFrame(dsetA)
        dataiso = pandas.DataFrame(Iso)
        IsoS = pandas.merge(dataS,dataiso,left_on=Knoten_S,right_on=Bezug1)
        IsoS["Kosten"] = IsoS[k_S]+IsoS["Kosten"]
        gb = IsoS.groupby(Bezug2) ##Group über ZielHstBer
        IsoS = IsoS.iloc[gb["Kosten"].idxmin()] ##Index der Minimalen Kostenwerte; Dann slicing über diese IDs

        IsoA = pandas.merge(dataA,IsoS,left_on=Knoten_A,right_on=Bezug2)

        if "NMIV" in Modus:
            Nahbereich = df[df[ID_S+"_y"]==m] ##Wähle nur die Nahbereiche für diese Einrichtung aus
            IsoA = IsoA.append(Nahbereich, ignore_index = True)

        IsoA["Kosten"] = IsoA[k_A+"_x"]+IsoA["Kosten"]
        gb = IsoA.groupby(ID_A+"_x")["Kosten"].idxmin()
        IsoA = IsoA.iloc[gb]


        #--Befülle HDF5-Ergebnistabelle--#
        """
        Wenn der Zeitbezug Abfahrt (nicht Ankunft) ist, dann bezieht sich dies auf die Abfahrt an der Struktur. Entsprechend sind die Rasterzellen dann die Zielpunkte.
        Entsprechend müssen hier die Spalten jeweils vertauscht werden.
        """
        if Zeitbezug == "Ankunft":
            Ergebnis = IsoA[["Start_ID_x","StartHstBer","Start_ID_y", "ZielHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y"]]
        else:
            Ergebnis = IsoA[["Start_ID_y","ZielHstBer","Start_ID_x", "StartHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y"]]
        Ergebnis.loc[Ergebnis["ZielHstBer"]==Ergebnis["StartHstBer"],"UH"] = 111 ##Wenn StarHstBer = ZielHstBer bedeutet das einen Direktweg, damit UH = 111
        Ergebnis = np.array(Ergebnis)
        Ergebnis = list(map(tuple, Ergebnis))
        size = len(Ergebnis_T)
        sizer = size+len(Ergebnis)
        Ergebnis_T.resize((sizer,))
        Ergebnis_T[size:sizer] = Ergebnis
        file5.flush()
        arcpy.AddMessage("--Berechnung für Struktur "+str(m+1)+" erfolgreich nach "+str(int(time.clock())-int(t1))+" Sekunden--")


    ###########################################################################
    #--Erreichbarkeiten--#
    ###########################################################################

if "Erreichbarkeiten" in Modus:
    IsoChronen = IsoChronen[IsoChronen["Kosten"]<(int(Zeitschranke[0])-5)]##Nur die Isochronen, die unter der Gesamtreisezeit minus Puffer liegen
    Einrichtungen = np.unique(dsetA[ID_A]) ##Eindeutige Einrichtungen / Startpunkte
    arcpy.AddMessage("--Insgesamt werden Indikatoren  für: "+str(len(Einrichtungen))+" Punkte berechnet--")
    for m,i in enumerate(Einrichtungen):
        t1 = time.clock()
        arcpy.AddMessage("--Berechne Indikatoren für Punkt "+str(m+1)+" von "+str(len(Einrichtungen))+"--") ##+1, da sonst Beginn bei 0
        Ergebnis = []
        Ergebnis.append(i)
        Anb = dsetA[dsetA[ID_A]==i] ##Nur Anbindung von entsprechender Einrichtung
        Iso = IsoChronen[np.in1d(IsoChronen["StartHstBer"],Anb[Knoten_A])] ##Wähle Isochronen, die in den Anbindungsknoten dabei sind.
        dataA = pandas.DataFrame(Anb)
        dataiso = pandas.DataFrame(Iso)
        IsoA = pandas.merge(dataA,dataiso,left_on=Knoten_A,right_on="StartHstBer")

        if len(IsoA) == 0: ##Falls keine Anbindung bedingung erfüllt
            for e in range(Indikatoren):
                Ergebnis.append(0)
            Ergebnis =[tuple(Ergebnis)]
            size = len(Ergebnis_T)
            Ergebnis_T.resize((size+1,))
            Ergebnis_T[size:(size+1)] = Ergebnis
            file5.flush()
            continue

        IsoA["Kosten"] = IsoA[k_A]+IsoA["Kosten"] ##Gesamtzeit inkl. Anbindungszeit
        gb = IsoA.groupby("ZielHstBer") ##Group über ZielHstBer
        IsoA = IsoA.iloc[gb["Kosten"].idxmin()] ##Index der Minimalen Kostenwerte; Dann slicing über diese IDs

        #--Anbindung der Struktur-Anbindung--#
        IsoS = pandas.merge(dataS,IsoA,left_on=Knoten_S,right_on="ZielHstBer")
        if "NMIV" in Modus:
            Nahbereich = df[df[ID_A+"_y"]==i] ##Wähle nur die Nahbereiche für diese Einrichtung aus
            IsoS = IsoS.append(Nahbereich, ignore_index = True) ##Neuer Index, da nach dem append Doppellung entstehen

        IsoS["Kosten"] = IsoS[k_S+"_x"]+IsoS["Kosten"] ##_x wird erzeugt, wenn Spaltenköpfe gleichen Namen

        if len(IsoS) == 0: ##Falls keine Anbindung bedingung erfüllt
            for e in range(Indikatoren):
                Ergebnis.append(0)
            Ergebnis =[tuple(Ergebnis)]
            size = len(Ergebnis_T)
            Ergebnis_T.resize((size+1,))
            Ergebnis_T[size:(size+1)] = Ergebnis
            file5.flush()
            continue

        gb = IsoS.groupby(ID_S+"_x")["Kosten"].idxmin() ##Gruppiere über die Struktur IDs
        IsoS = IsoS.iloc[gb]
        IsoS = IsoS[IsoS["Kosten"]<=int(Zeitschranke[0])] ##Um Gesamtreisezeit zu berücksichtigen!!

        #--Berechne die Indikatorwerte--#
        for e in Berechnung:
            Column = e.split("__")[0] ##Um wieder den eigentlichen Namen der Strukturspalte zu erhalten!!

            if e[-3:] == "Sum":
                for n in sumfak:
                    Indi = IsoS[IsoS["Kosten"]<=int(n)]
                    Wert = Indi[Column].sum()
                    Ergebnis.append(Wert)

            elif e[-4:] == "Expo":
                for n in potfak:
                    n = float(n)
                    Wert = round(sum(np.exp(IsoS["Kosten"]*n) * IsoS[Column]))
                    Ergebnis.append(Wert)

            elif e[-3:] == "UH0":
                Indi = IsoS[IsoS["UH"]==0]
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-3:] == "UH1":
                Indi = IsoS[IsoS["UH"]<2]
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-6:] == "direkt":
                Indi = IsoS[IsoS["UH"]==111]
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-3:] == "BH3":
                Indi = IsoS[IsoS["BH"]>=3]
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-4:] == "BH10":
                Indi = IsoS[IsoS["BH"]>=10]
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-4:] == "BH20":
                Indi = IsoS[IsoS["BH"]>=20]
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-4:] == "P310":
                Indi = IsoS[IsoS["Preis"] <=3]
                Indi = Indi[Indi["Preis"] >0] ##Falls es Null-Preise gibt. Null = Kein Preissystem hinterlegt
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-4:] == "P500":
                Indi = IsoS[IsoS["Preis"]<=5]
                Indi = Indi[Indi["Preis"] >0] ##Falls es Null-Preise gibt. Null = Kein Preissystem hinterlegt
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            elif e[-4:] == "P690":
                Indi = IsoS[IsoS["Preis"]<=7]
                Indi = Indi[Indi["Preis"] >0] ##Falls es Null-Preise gibt. Null = Kein Preissystem hinterlegt
                Wert = Indi[Column].sum()
                Ergebnis.append(Wert)

            else:
                pass


        #--Fülle Daten in HDF5-Tabelle--#
        Ergebnis =[tuple(Ergebnis)]
        size = len(Ergebnis_T)
        Ergebnis_T.resize((size+1,))
        Ergebnis_T[size:(size+1)] = Ergebnis
        file5.flush()
        arcpy.AddMessage("--Berechnung für Punkt "+str(m+1)+" erfolgreich nach "+str(int(time.clock())-int(t1))+" Sekunden--")


#--HDF5-Text zu Tabellenbeschreibung--#
Ergebnis_T.attrs.create("Parameter",str(text))


###########
#--Ende--#
###########
file5.flush()
file5.close()
hh