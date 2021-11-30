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
import arcpy
import time
import h5py
import numpy as np
import win32com.client.dynamic
import pandas
import gc
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
##22 bis 29 NMIV
##22 bis 29 NMIV
Zeitschranke = arcpy.GetParameterAsText(30)
Zeitbezug = arcpy.GetParameterAsText(31)
Filter_S = arcpy.GetParameterAsText(32)
Group_Iso = arcpy.GetParameterAsText(33)
Filter_Gruppe = arcpy.GetParameterAsText(34)
Group_Erg = arcpy.GetParameterAsText(35)
Tag = arcpy.GetParameterAsText(36)

#--Generierung weiterer Parameter--#
if "Erreichbarkeiten" in Modus:
    text = "Datum: "+str(time.localtime()[0:3])+", Modus: " +Modus+"; Zeitschranken: "+Zeitschranke+", IsoName: "+IsoChronen_Name+", Tabelle_A: "+Tabelle_A+", Tabelle_S: "+Tabelle_S+ ", Berechnungen: "+Berechnung ##Für das Ergebnis-Attribut
else:
    text = "Datum: "+str(time.localtime()[0:3])+", Modus: " +Modus+"; Zeitbezug: "+ Zeitbezug+"; Zeitschranken: "+Zeitschranke+", IsoName: "+IsoChronen_Name+", Tabelle_A: "+Tabelle_A+", Tabelle_S: "+Tabelle_S ##Für das Ergebnis-Attribut
if "OEV" not in Modus: text = "Datum: "+str(time.localtime()[0:3])+", Modus: " +Modus+", Tabelle_A: "+Tabelle_A+", Tabelle_S: "+Tabelle_S

if "keine_IsoChronen" not in Modus and "OEV" in Modus: ##Für die IsoChronen-Tabelle
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
Tag = Tag.split(";")

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
#--Funktionen--#
###########################################################################
def Iso_Auswahl (dset_A,Knoten__A,dset_S,Knoten__S,Bezug_1,Bezug_2,Iso_I,Kosten_maximal,Modus_):

    #1. Auswahl jener HstBer die überhaupt in den Rasterzellen und Zielen vertreten sind
    Raster_HstBer = np.unique(dset_A[Knoten__A]) ##Array mit allen HstBer an den Rasterzelle
    Ziele_HstBer = np.unique(dset_S[Knoten__S]) ##Erzeuge Liste mit eindueitgen HstBereichen der Strukturen

    if True in map(lambda element_: 'Anbindung' in element_, Modus_):
        header = 20
    else:
        header = 10000
    schleifenstart = 0
    schleifenziel = 1000000 ##eine Million
    schleifenumfang = 1000000 ##eine Million
    schleifen = (len(Iso_I)/schleifenziel)+1 ##Da abgerundet wird und dann oft schleifen = 0

    #2. IsoChronen werden aufgrund der Größe in Schichten bzw. Schleifen zerlegt
    for k in range(schleifen):
        iso_schleife = Iso_I[schleifenstart:schleifenziel]
        iso_schleife = iso_schleife[np.in1d(iso_schleife[Bezug_1].ravel(), Ziele_HstBer)] ##Wähle nur die IsoChronen, wo auch die ZielHstBer enthalten sind.
        iso_schleife = iso_schleife[np.in1d(iso_schleife[Bezug_2].ravel(), Raster_HstBer)] ##Wähle nur die IsoChronen, wo auch die RastHstBer enthalten sind.
        iso_schleife = np.array(iso_schleife)
        iso_schleife = pandas.DataFrame(iso_schleife)
        iso_schleife = iso_schleife[iso_schleife["Kosten"]<=int(Kosten_maximal)] ##Wähle nur die Verbindungen von den Raster-HstBer, die innerhalb der Zeitschranke liegen.
        iso_schleife = iso_schleife.sort_values([Bezug2,"Kosten"]) ##Erst sortieren
        iso_schleife = iso_schleife.groupby(Bezug2).head(header).reset_index(drop=True) ##Dann jeweils die ersten zwanzig auswählen

        if k==0: Iso_f = iso_schleife
        else: Iso_f = pandas.concat([Iso_f,iso_schleife])

        schleifenstart+=schleifenumfang
        schleifenziel+=schleifenumfang

    return Iso_f ##Pandas Dataframe


###########################################################################
#--Vorbereitung Anbindungsberechnung--#
###########################################################################
if True in map(lambda element: 'Anbindung' in element, Modus):
    Modus.append("Anbindung")
    Berechnung = ("StartHst","Ziel_ID", "ZielHst", "Reisezeit", "UH", "Anbindungszeit", "Abgangszeit","BH")



###########################################################################
#--Verbindung zur HDF-5 Datenbank--#
###########################################################################
#--Datenzugriff--#
file5 = h5py.File(Datenbank,'r+') ##HDF5-File
group5 = file5[Group]
group5_Iso = file5[Group_Iso]
group5_Ergebnisse = file5[Group_Erg]

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
    Barrieren = "" ##GIS-Shape um Fähren im Network zu unterbinden
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
    arcpy.Delete_management("S_Shape")
    arcpy.Delete_management("A_Shaoe")

    #--Layer aus Shape-Files erstellen--#
    arcpy.MakeFeatureLayer_management(A_Shape, "A_Shape")
    if Filter_S: arcpy.MakeFeatureLayer_management(S_Shape, "S_Shape",Filter_S+">0") ##Wenn Filter, dann nur die Strukturen, wo das entsprechende Feld größer 0 ist.
    else: arcpy.MakeFeatureLayer_management(S_Shape, "S_Shape")

    #--Nimm nur die Startpunkte die auch in der HDF5-Anbindungstabelle sind--#
    if "Erreichbarkeiten" in Modus:
        """
        Auswahl der Startpunkte wurde auskommentiert, da die Sequenz dazu führt, dass nur Startpunkte zu Fuß erreicht werden dürfen, die mindestens
        eine gültige (Zeitschranke) Haltestellenanbindung besitzen!
        """
##        Startpunkte_Shape = dsetA[ID_A]
##        for i in Startpunkte_Shape:
##            arcpy.SelectLayerByAttribute_management ("A_Shape", "ADD_TO_SELECTION", A_Shape_ID+"="+str(i))

        #--Durchführung der OD-Berechnung--#
        Bereich = arcpy.SelectLayerByLocation_management("S_Shape","intersect","A_Shape",Radius)
        tofind = 50
        ODLayer = arcpy.MakeODCostMatrixLayer_na(Network,"ODMATRIX",Kosten,Max_Kosten,tofind,[Kosten,"Meter","tAkt_Rad"],"","","","","NO_LINES")
        l = arcpy.mapping.Layer("ODMATRIX")
        p = arcpy.na.GetSolverProperties(l)
        Restriction_0 = list(p.restrictions) ##erstelle Liste mit allen Restriktionen
        p.restrictions = Restriction_0
        del l,p
        arcpy.AddLocations_na(ODLayer,"Origins","A_Shape","Name "+A_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"],["Knoten", "NONE"],["MRH_Rand", "SHAPE"]],"","","","","EXCLUDE")
        arcpy.AddLocations_na(ODLayer,"Destinations",Bereich,"Name "+S_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"],["Knoten", "NONE"],["MRH_Rand", "SHAPE"]],"","","","","EXCLUDE")
        arcpy.AddLocations_na(ODLayer,"Line Barriers",Barrieren,"","") ##Das sind die Barrieren
        arcpy.na.Solve(ODLayer)

    if "Anbindung" in Modus: ##Unterschied Anbindung <> Erreichbarkeiten: Mal sind A_Shape die wenigen, mal S_Shape die wenigen Punkte.
##        Zielpunkte_Shape = dsetS[ID_S]
##        for i in Zielpunkte_Shape:
##            arcpy.SelectLayerByAttribute_management ("S_Shape", "ADD_TO_SELECTION", S_Shape_ID+"="+str(i))
        if Filter_Gruppe or "Anbindung_disaggregiert" in Modus: tofind = 50 ##Sonst wird das mit der Gruppe nix
        else: tofind = 2
        #--Durchführung der OD-Berechnung--#
        Bereich = arcpy.SelectLayerByLocation_management("A_Shape","intersect","S_Shape",Radius)
        ODLayer = arcpy.MakeODCostMatrixLayer_na(Network,"ODMATRIX",Kosten,Max_Kosten,tofind,[Kosten,"Meter","tRad"],"","","","","NO_LINES")
        arcpy.AddLocations_na(ODLayer,"Destinations","S_Shape","Name "+S_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"],["Knoten", "NONE"],["MRH_Rand", "SHAPE"]],"","","","","EXCLUDE")
        r = []
        desc = arcpy.Describe(Network)
        attributes = desc.attributes
        for i in attributes:
            if i.usageType =='Restriction':
                r.append(i.name)
        l = arcpy.mapping.Layer("ODMATRIX")
        p = arcpy.na.GetSolverProperties(l)
        p.restrictions = r
        del l,p,r
        arcpy.AddLocations_na(ODLayer,"Origins",Bereich,"Name "+A_Shape_ID+" 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["Radschnellwege", "NONE"],["Ampeln", "NONE"],["Knoten", "NONE"],["MRH_Rand", "SHAPE"]],"","","","","EXCLUDE")
        arcpy.AddLocations_na(ODLayer,"Line Barriers",Barrieren,"","") ##Das sind die Barrieren
        ##arcpy.management.SaveToLayerFile("ODMATRIX","C:\Geodaten\ODE","RELATIVE")
        arcpy.na.Solve(ODLayer)

    #--Abgreifen der Ergebniswerte--#
    if "OEV" in Modus:
        Lines = arcpy.da.FeatureClassToNumPyArray("ODMATRIX\Lines",["Name", "Total_"+Kosten]) ##Erstelle Numpy-Array aus Ergebnis-Routen
        df = pandas.DataFrame(Lines) ##Erstelle daraus ein Pandas-DatenFrame
        a = pandas.DataFrame(df.Name.str.split(' - ').tolist(), columns = "Start Ziel".split())
    else:
        #--Abgreifen der Ergebniswerte--#
        schleifen = (int(arcpy.GetCount_management("A_Shape").getOutput(0))/50000)+1
        schleifenstart = 0
        schleifenziel = 50000
        schleifenumfang = 50000
        for h in range(schleifen):
            Lines = arcpy.da.FeatureClassToNumPyArray("ODMATRIX\Lines",["Name", "Total_"+Kosten, "Total_Meter", "Total_tFuss"],"OriginID >="+str(schleifenstart)+"and OriginID <"+str(schleifenziel),skip_nulls=True) ##Erstelle Numpy-Array aus Ergebnis-Routen
            if len(Lines)==0:continue
            if h ==0: df = pandas.DataFrame(Lines)
            else: df = pandas.concat([df,pandas.DataFrame(Lines)])
            schleifenstart+=schleifenumfang
            schleifenziel+=schleifenumfang
        a = pandas.DataFrame(df.Name.str.split(' - ').tolist(), columns = "Start Ziel".split())
        df = pandas.DataFrame.reset_index(df) ##wichtig!!!!!


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
        arcpy.AddMessage(Strukturgr)
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

    if "OEV" not in Modus:
        arcpy.AddMessage("--Erstelle Ergebnis-Tabelle für den NMIV/IV--")
        #--HDF5-->Spalten für Ergebnistabelle--#
        Ergebnis_array = []
        Spalten = [('Start_ID', 'int32'),('Ziel_ID', 'int32'),('Reisezeit', 'int32'),('Meter', 'int32'),('tAktRad', 'int32')]
        #--Erhebnistabelle erstellen--#
        Spalten = np.dtype(Spalten) ##Wandle Spalten-Tuple in dtype um
        data = np.array(Ergebnis_array,Spalten)
        if Tabelle_E in group5_Ergebnisse.keys():
            del group5_Ergebnisse[Tabelle_E] ##Ergebnisliste wird gelöscht falls schon vorhanden
        group5_Ergebnisse.create_dataset(Tabelle_E, data=data, dtype=Spalten, maxshape = (None,))
        Ergebnis_T = group5_Ergebnisse[Tabelle_E]
        file5.flush()

        #--Bereite Ergebnis-Tabelle vor--#
        if "Anbindung_aggregiert" in Modus:
            gb = df.groupby(ID_A+"_x")["Kosten"].idxmin()
            df = df.iloc[gb]
        df = df[[ID_A+"_x",ID_S+"_y","Kosten","Total_Meter", "Total_tAkt_Rad"]]
        Ergebnis = np.array(df)
        Ergebnis = list(map(tuple, Ergebnis))
        size = len(Ergebnis_T)
        sizer = size+len(Ergebnis)
        Ergebnis_T.resize((sizer,))
        Ergebnis_T[size:sizer] = Ergebnis
        Ergebnis_T.attrs.create("Parameter",str(text))
        file5.flush()
        file5.close()
        

###########################################################################
#--VISUM-IsoChronenberechnung--#
###########################################################################
if "keine_IsoChronen" not in Modus and "OEV" in Modus:
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
        Spalten = [('StartHstBer', 'int32'),('Kosten', '<f8'),('UH', 'i2'),('ZielHstBer', 'int32'),('BH', 'i2')]
    else:
        Spalten = [('ZielHstBer', 'int32'),('Kosten', '<f8'),('UH', 'i2'),('StartHstBer', 'int32'),('BH', 'i2')]
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
        Isochrones.ExecutePuT(NE,"X",str(Stunden[0])+":00:00",str(Stunden[1])+":00:00",int(Tag[0]),int(Tag[1]),Nachlauf*60*60,bool(Zeitbezug == "Ankunft"))##bool: Ankunfts- oder Abfahrtszeit, True = Ankunft
        Ziel = list(np.array(VISUM.Net.StopAreas.GetMultiAttValues("No"))[:,1]) ##Nimmt Nummer UND Zeilennummer (beginnend bei 1)
        Zeit = list(np.array(VISUM.Net.StopAreas.GetMultiAttValues("IsocTimePuT"))[:,1]/60) ##nimmt nur Die Zeit / um aus Sekunden minuten zu machen
        UH = list(np.array(VISUM.Net.StopAreas.GetMultiAttValues("IsocTransfersPuT"))[:,1])
        for i in range(len(Ziel)):
            Liste_HB.append((Ziel[i],Zeit[i]+int(Zeitschranke[3]),UH[i],Nr,999)) ##999 da keine Bedienhäufigkeit berechnet wird. Also Platzhalter.
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
if Tabelle_E in group5_Ergebnisse.keys():
    del group5_Ergebnisse[Tabelle_E] ##Ergebnisliste wird gelöscht falls schon vorhanden
group5_Ergebnisse.create_dataset(Tabelle_E, data=data, dtype=Spalten, maxshape = (None,))
Ergebnis_T = group5_Ergebnisse[Tabelle_E]
file5.flush()


###########################################################################
#--Berechnung der Indikatoren (Vorbereitung)--#
###########################################################################
dataS = pandas.DataFrame(dsetS)
if "OEV" not in Modus: ##Wenn kein OEV berücksichtigt wird, dann nimm nur eine IsoChrone und mache diese auf 999, damit sie nicht genommen wird.
    IsoChronen = group5_Iso[group5_Iso.keys()[0]] ##wenn IsoChrone nicht vorhanden, nimm einfach die erste
    IsoChronen = IsoChronen[0:2]
    IsoChronen["Kosten"] = 999

else:IsoChronen = group5_Iso[IsoChronen_Name]

if "keine_IsoChronen" in Modus:
    text = text.split(IsoChronen_Name)
    text = text[0]+IsoChronen_Name+" ("+IsoChronen.attrs.values()[0]+")"+text[1]

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

    if Zeitbezug == "Ankunft" or Zeitbezug == "Matrize_Abfahrt": ##Wenn der Zeitbezug Ankunft ist, dann sind die Strukturen/Ziele auch die ZielHstber. Bei Abfahrt, sind es die StartHstBereiche.
        Bezug1 = "ZielHstBer"
        Bezug2 = "StartHstBer"
    else:
        Bezug1 = "StartHstBer"
        Bezug2 = "ZielHstBer"

    for i, m in enumerate(Gruppen):

        if Filter_Gruppe:
            dataG = dataS[dataS[Filter_Gruppe]==m] ##wähle nur die Strukturen aus, die in der entsprechenden Gruppe sind
            Gruppen_Auswahl = dsetS[dsetS[Filter_Gruppe]==m]
            Iso_p = Iso_Auswahl(dsetA,Knoten_A,Gruppen_Auswahl,Knoten_S,Bezug1,Bezug2,IsoChronen,Zeitschranke[0],Modus)
            arcpy.AddMessage("--Beginne mit der Berechnung aggregierter Anbindungen für Gruppe "+str(m)+" mit "+str(len(np.unique(dataG[ID_S])))+" Strukturgrößen--")
            IsoS = pandas.merge(dataG,Iso_p,left_on=Knoten_S,right_on=Bezug1)

        else:
            dataG = dataS ##wähle nur die Strukturen aus, die in der entsprechenden Gruppe sind
            Iso_p = Iso_Auswahl(dsetA,Knoten_A,dsetS,Knoten_S,Bezug1,Bezug2,IsoChronen,Zeitschranke[0],Modus)
            arcpy.AddMessage("--Beginne mit der Berechnung aggregierter Anbindungen für "+str(len(np.unique(dsetS[ID_S])))+" Strukturgrößen--")
            IsoS = pandas.merge(dataG,Iso_p,left_on=Knoten_S,right_on=Bezug1)


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
        if Zeitbezug == "Ankunft" or "Matrize_Abfahrt":
            Ergebnis = IsoA[["Start_ID_x","StartHstBer","Start_ID_y", "ZielHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y","BH"]]
        else:
            Ergebnis = IsoA[["Start_ID_y","ZielHstBer","Start_ID_x", "StartHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y","BH"]]
        Ergebnis.loc[Ergebnis["ZielHstBer"]==Ergebnis["StartHstBer"],"UH"] = 111 ##Wenn StarHstBer = ZielHstBer bedeutet das einen Direktweg, damit UH = 111
        Ergebnis.loc[Ergebnis["ZielHstBer"]==Ergebnis["StartHstBer"],"BH"] = 111 ##Wenn StarHstBer = ZielHstBer bedeutet das einen Direktweg, damit BH = 111
        Ergebnis = np.array(Ergebnis)
        Ergebnis = list(map(tuple, Ergebnis))
        size = len(Ergebnis_T)
        sizer = size+len(Ergebnis)
        Ergebnis_T.resize((sizer,))
        Ergebnis_T[size:sizer] = Ergebnis
        file5.flush()


if "Anbindung_disaggregiert" in Modus:
    arcpy.AddMessage("--Beginne mit der Berechnung disaggregierter Anbindungen für "+str(len(np.unique(dsetS[ID_S])))+" Punkte--")
    Einrichtungen = np.unique(dsetS[ID_S])

    if Zeitbezug == "Ankunft" or Zeitbezug == "Matrize_Abfahrt": ##Wenn der Zeitbezug Ankunft ist, dann sind die Strukturen/Ziele auch die ZielHstber. Bei Abfahrt, sind es die StartHstBereiche.
        Bezug1 = "ZielHstBer"
        Bezug2 = "StartHstBer"
    else:
        Bezug1 = "StartHstBer"
        Bezug2 = "ZielHstBer"

    for i, m in enumerate(Einrichtungen):
        t1 = time.clock()
        arcpy.AddMessage("--Berechne Anbindungen für Struktur "+str(i+1)+" von "+str(len(Einrichtungen))+"--") ##+1, da sonst Beginn bei 0
        Anb = dsetS[dsetS[ID_S]==m] ##Nur Anbindung von entsprechender Einrichtung
        Iso_p = Iso_Auswahl(dsetA,Knoten_A,Anb,Knoten_S,Bezug1,Bezug2,IsoChronen,Zeitschranke[0],Modus)
        dataS_diss = dataS[dataS[Filter_Gruppe]==m]        
        dataA = pandas.DataFrame(dsetA)
        IsoS = pandas.merge(dataS_diss,Iso_p,left_on=Knoten_S,right_on=Bezug1)
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
            Ergebnis = IsoA[["Start_ID_x","StartHstBer","Start_ID_y", "ZielHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y","BH"]]
        else:
            Ergebnis = IsoA[["Start_ID_y","ZielHstBer","Start_ID_x", "StartHstBer", "Kosten", "UH", k_A+"_x", k_S+"_y","BH"]]
        Ergebnis.loc[Ergebnis["ZielHstBer"]==Ergebnis["StartHstBer"],"UH"] = 111 ##Wenn StarHstBer = ZielHstBer bedeutet das einen Direktweg, damit UH = 111
        Ergebnis.loc[Ergebnis["ZielHstBer"]==Ergebnis["StartHstBer"],"BH"] = 111 ##Wenn StarHstBer = ZielHstBer bedeutet das einen Direktweg, damit BH = 111
        Ergebnis = np.array(Ergebnis)
        Ergebnis = list(map(tuple, Ergebnis))
        size = len(Ergebnis_T)
        sizer = size+len(Ergebnis)
        Ergebnis_T.resize((sizer,))
        Ergebnis_T[size:sizer] = Ergebnis
        file5.flush()
        arcpy.AddMessage("--Berechnung für Struktur "+str(i+1)+" erfolgreich nach "+str(int(time.clock())-int(t1))+" Sekunden--")


###########################################################################
#--Erreichbarkeiten--#
###########################################################################
"""
2. Auswahl der zu betrachtenden Isochronen über die Funktion
3. Merge der Startpunkte an diese Isochronen. Anschl. Addition von Kosten (Reisezeit) und Anbindungszeit
4. Anschließend wird für jede Start_ID die minimale Reisezeit zu jeder Zielhaltestelle ermittelt.
5. Merge der Zielpunkte an diese Isochronen. Anschl. Addition von Kosten (Reisezeit) und Abgangszeit
6. Anschließend wird für jede Start_ID die minimale Reisezeit zu jeder Ziel_ID ermittelt.
"""


if "Erreichbarkeiten" in Modus:
    if Zeitbezug == "Ankunft" or Zeitbezug == "Matrize_Abfahrt": ##Wenn der Zeitbezug Ankunft ist, dann sind die Strukturen/Ziele auch die ZielHstber. Bei Abfahrt, sind es die StartHstBereiche.
        Bezug1 = "ZielHstBer"
        Bezug2 = "StartHstBer"
    else:
        Bezug1 = "StartHstBer"
        Bezug2 = "ZielHstBer"

    #0.
    a = np.unique(dsetA["Start_ID"])
    schleifenstart = 0
    schleifenziel = 100 ##eine Million
    schleifenumfang = 100 ##eine Million
    schleifen = (len(a)/schleifenziel)+1 ##Da abgerundet wird und dann oft schleifen = 0
    #1.
    Iso = Iso_Auswahl(dsetA,Knoten_A,dsetS,Knoten_S,Bezug1,Bezug2,IsoChronen,Zeitschranke[0],Modus)
    del IsoChronen, dsetS, group5_Iso, group5, group5_Ergebnisse
    gc.collect()
    #2.
    for schleife in range(schleifen):
        arcpy.AddMessage("--Beginne mit Schleife "+str(schleife+1)+" von "+str(schleifen)+"--")
        dsetA_s = a[schleifenstart:schleifenziel]
        dsetA_s = dsetA[np.in1d(dsetA["Start_ID"],dsetA_s)]
        schleifenstart+=schleifenumfang
        schleifenziel+=schleifenumfang

        #3.
        dataA = pandas.DataFrame(dsetA_s)
        dataiso = pandas.merge(dataA,Iso,left_on=Knoten_A,right_on="StartHstBer")
        dataiso.loc[:,"Kosten"] = dataiso.loc[:,k_A]+dataiso.loc[:,"Kosten"] ##mit .loc, da von pandas so vorgegeben
        dataiso = dataiso[dataiso["Kosten"]<=(int(Zeitschranke[0]))-4] ##-4 um den array hier schonmal klein zu halten. Später kommt ja noch die Abgangszeit dazu.
        dataiso = dataiso.reset_index(drop=True)
        #4.
        try:
            gb = dataiso.groupby([ID_A,"ZielHstBer"]) ##Group über ZielHstBer
            dataiso = dataiso.iloc[gb["Kosten"].idxmin()] ##Index der Minimalen Kostenwerte; Dann slicing über diese IDs
            dataiso = dataiso.reset_index(drop=True)
            #5.
            dataS_in = dataS.loc[dataS["Ziel_Knoten"].isin(dataiso["ZielHstBer"])] ##Erstmal nur die Anbindungen auswählen, die anschließend überhaupt gemerged werden.
            dataiso = pandas.merge(dataiso,dataS_in,left_on="ZielHstBer",right_on="Ziel_Knoten")
            gc.collect()
            dataiso.loc[:,"Kosten"] = dataiso.loc[:,k_S+"_y"]+dataiso.loc[:,"Kosten"]
            #6.
            gb = dataiso.groupby([ID_A+"_x",ID_S+"_y"])
            dataiso = dataiso.iloc[gb["Kosten"].idxmin()] ##Index der Minimalen Kostenwerte; Dann slicing über diese IDs
            Einrichtungen = np.unique(dsetA_s[ID_A])
            arcpy.AddMessage("--Insgesamt werden Indikatoren  für: "+str(len(Einrichtungen))+" Punkte berechnet--")
        except:
            try:
                dataiso = dataiso[::2] ##wähle nur die gerade Indexe aus
                dataiso = dataiso.reset_index(drop=True)
                gb = dataiso.groupby([ID_A,"ZielHstBer"]) ##Group über ZielHstBer
                dataiso = dataiso.iloc[gb["Kosten"].idxmin()] ##Index der Minimalen Kostenwerte; Dann slicing über diese IDs
                dataiso = dataiso.reset_index(drop=True)
                #5.
                dataS_in = dataS.loc[dataS["Ziel_Knoten"].isin(dataiso["ZielHstBer"])] ##Erstmal nur die Anbindungen auswählen, die anschließend überhaupt gemerged werden.
                dataiso = pandas.merge(dataiso,dataS_in,left_on="ZielHstBer",right_on="Ziel_Knoten")
                gc.collect()
                dataiso.loc[:,"Kosten"] = dataiso.loc[:,k_S+"_y"]+dataiso.loc[:,"Kosten"]
                #6.
                gb = dataiso.groupby([ID_A+"_x",ID_S+"_y"])
                dataiso = dataiso.iloc[gb["Kosten"].idxmin()] ##Index der Minimalen Kostenwerte; Dann slicing über diese IDs
                Einrichtungen = np.unique(dsetA_s[ID_A])
                arcpy.AddMessage("--Insgesamt werden Indikatoren  für: "+str(len(Einrichtungen))+" (gerade)Punkte berechnet--")
            except:
                arcpy.AddMessage("--Fehler in Schleife "+str(schleife+1)+"--")
                continue
        for i in Einrichtungen:
            t1 = time.clock()
            ##arcpy.AddMessage("--Berechne Indikatoren für ID "+str(i)+"--") ##+1, da sonst Beginn bei 0
            Ergebnis = []
            Ergebnis.append(i)
            IsoS = dataiso[dataiso[ID_A+"_x"]==i]
            IsoS = IsoS.reset_index(drop=False)

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

                elif e[-3:] == "UH2":
                    Indi = IsoS[IsoS["UH"]<3]
                    Wert = Indi[Column].sum()
                    Ergebnis.append(Wert)

                elif e[-3:] == "UH3":
                    Indi = IsoS[IsoS["UH"]<4]
                    Wert = Indi[Column].sum()
                    Ergebnis.append(Wert)

                elif e[-3:] == "UH4":
                    Indi = IsoS[IsoS["UH"]<5]
                    Wert = Indi[Column].sum()
                    Ergebnis.append(Wert)

                elif e[-6:] == "direkt":
                    Indi = IsoS[IsoS["UH"]==111]
                    Wert = Indi[Column].sum()
                    Ergebnis.append(Wert)

                elif e[-3:] == "BH2":
                    Indi = IsoS[IsoS["BH"]>=2]
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
            arcpy.AddMessage("--Berechnung für ID "+str(i)+" erfolgreich nach "+str(int(time.clock())-int(t1))+" Sekunden--")
        del dataiso
        gc.collect()


#--HDF5-Text zu Tabellenbeschreibung--#
Ergebnis_T.attrs.create("Parameter",str(text))


###########
#--Ende--#
###########
file5.flush()
file5.close()
hh