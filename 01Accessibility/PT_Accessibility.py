# -*- coding: cp1252 -*-
#!/usr/bin/python
#Calculate distance and gravity/contour PT Accessibility
#Marcus September 2015; new Version December 2021
#Python 2.7.5

import arcpy
from datetime import date
import gc
import h5py
import numpy as np
import pandas
import time
import win32com.client.dynamic
start_time = time.time()
pandas.options.mode.chained_assignment = None
arcpy.CheckOutExtension("Network")
arcpy.AddMessage("> starting\n")

#--ArcGIS Parameter--#
Modus = arcpy.GetParameterAsText(0).split(";")
Database = arcpy.GetParameterAsText(1)
Group_O = arcpy.GetParameterAsText(2)
Group_I = arcpy.GetParameterAsText(3)
Group_R = arcpy.GetParameterAsText(4)
Table_R = arcpy.GetParameterAsText(5)
Time_limits = arcpy.GetParameterAsText(6).split(";")
Table_O = arcpy.GetParameterAsText(7)
k_O = arcpy.GetParameterAsText(8)
kmh_O = int(arcpy.GetParameterAsText(9))
Table_P = arcpy.GetParameterAsText(10)
k_P = arcpy.GetParameterAsText(11)
kmh_P = int(arcpy.GetParameterAsText(12))
Filter_P = arcpy.GetParameterAsText(13)
Filter_Group_P = arcpy.GetParameterAsText(14)
to_find = int(arcpy.GetParameterAsText(15))
Network_PT = arcpy.GetParameterAsText(16)
Hours = arcpy.GetParameterAsText(17).split(";")
Isochrone_Name = arcpy.GetParameterAsText(18)
Smooth_PT = bool(arcpy.GetParameterAsText(19)=="true")
StructData = arcpy.GetParameterAsText(20).split(";")
Measures = arcpy.GetParameterAsText(21).split(";")
sumfak = arcpy.GetParameterAsText(22).split(";")
potfak = arcpy.GetParameterAsText(23).split(";")
O_Shape = arcpy.GetParameterAsText(24)
P_Shape = arcpy.GetParameterAsText(25)
Network = arcpy.GetParameterAsText(26)
Radius = int(arcpy.GetParameterAsText(27))
Costs = arcpy.GetParameterAsText(28)
Max_Costs = int(arcpy.GetParameterAsText(29))

Node_O = "Stop_NO"
Node_P = "Stop_NO"
ID_O = "Start_ID"
ID_P = "Start_ID"
O_Shape_ID = "ID"
P_Shape_ID = "ID"
Barriers = "" ##Path to Shape
fromStop = "FromStop"
toStop = "ToStop"
PostRun = 24
Day = ("1;1").split(";")


def checkfm(FC, FC_ID):
    for field in arcpy.Describe(FC).fields:
        if "SnapX" in field.name:
            fm = "Name "+FC_ID+" 0; SourceID SourceID_NMIV 0;SourceOID SourceOID_NMIV 0"\
            ";PosAlong PosAlong_NMIV 0;SideOfEdge SideOfEdge_NMIV 0; Attr_Minutes # #"
            return fm

def distance():
    if Filter_Group_P: Groups = np.unique(dsetP[Filter_Group_P])
    else: Groups = [1]
    for i, m in enumerate(Groups):
        if Filter_Group_P:
            dataG = dsetP[dsetP[Filter_Group_P]==m]
            arcpy.AddMessage("> group "+str(i+1)+"/"+str(len(Groups))+" with "+str(len(np.unique(dataG[ID_P])))+" places")
        else:
            dataG = dsetP.copy()
            arcpy.AddMessage("> "+str(len(np.unique(dsetP[ID_P])))+" places")
        dataG.columns = [map(lambda a:a+"_P",dataG.columns)]
        Iso_p = Iso_Slice(dsetO,dsetP,IsoChronen)

        IsoP = pandas.merge(dataG,Iso_p,left_on=Node_P+"_P",right_on=toStop)
        IsoP["Time"] = IsoP[k_P+"_P"]+IsoP["Time"]

        if Smooth_PT is True:
            if to_find == 1: groupstate = fromStop
            else: groupstate = [ID_P+"_P",fromStop]
            IsoP['minTime'] = IsoP.groupby(groupstate)['Time'].transform('min')
            IsoP = IsoP[IsoP["Time"]-IsoP["minTime"]<5]
            IsoP['BH'] = IsoP.groupby(groupstate)['BH'].transform('max')
            IsoP['UH'] = IsoP.groupby(groupstate)['UH'].transform('min')
            IsoP.drop('minTime', axis=1, inplace=True)

        if to_find == 1:
            gb = IsoP.groupby([fromStop])
            IsoP = IsoP.loc[gb["Time"].idxmin()]
        else:
            gb = IsoP.groupby([ID_P+"_P",fromStop])["Time"].idxmin()
            IsoP = IsoP.loc[gb].sort_values([fromStop,"Time"])
            IsoP = IsoP.groupby(fromStop).head(to_find)

        IsoO = pandas.merge(dsetO,IsoP,left_on=Node_O,right_on=fromStop)
        IsoO["Time"] = IsoO[k_O]+IsoO["Time"]

        if "NMT" in Modus and len(proximity)>0:
            if Filter_Group_P:
                Proxy = proximity[proximity[ID_P+"_P"].isin(dataG[ID_P+"_P"])]
                IsoO = IsoO.append(Proxy, ignore_index = True)
            else: IsoO = IsoO.append(proximity, ignore_index = True)

        if Smooth_PT is True:
            IsoO['minTime'] = IsoO.groupby([ID_O,ID_P+"_P"])['Time'].transform('min')
            IsoO = IsoO[IsoO["Time"]-IsoO["minTime"]<5]
            IsoO['BH'] = IsoO.groupby([ID_O,ID_P+"_P"])['BH'].transform('max')
            IsoO['UH'] = IsoO.groupby([ID_O,ID_P+"_P"])['UH'].transform('min')
            IsoO.drop('minTime', axis=1, inplace=True)

        gb = IsoO.groupby([ID_O,ID_P+"_P"])["Time"].idxmin()
        IsoO = IsoO.loc[gb].sort_values([ID_O,"Time"])
        IsoO["tofind"] = IsoO.groupby([ID_O])['Time'].cumcount()+1
        IsoO = IsoO.groupby(ID_O).head(to_find)

        Result = IsoO[["Start_ID","FromStop","Start_ID_P", "ToStop", "Time", k_O, k_P+"_P", "UH", "BH", "tofind"]]
        Result["Group"] = m
        Result.loc[Result["ToStop"]==Result["FromStop"],"UH"] = 111 ##same StopArea == dirct by foot
        Result.loc[Result["ToStop"]==Result["FromStop"],"BH"] = 111
        Result.loc[(Result['UH']==0) & (Result['BH']==0),"UH"] = 111 ##transfers over stopareas in same stop
        Result.loc[(Result['UH']==111) & (Result['BH']==0),"BH"] = 111
        Result = np.array(Result)
        oldsize = len(Results_T)
        sizer = oldsize + len(Result)
        Results_T.resize((sizer,))
        Result = list(map(tuple, Result))
        Results_T[oldsize:sizer] = Result
        file5.flush()

def HDF5():
    file5 = h5py.File(Database,'r+') ##HDF5-File
    group5 = file5[Group_O]
    group5_Iso = file5[Group_I]
    group5_Results = file5[Group_R]
    return file5, group5, group5_Iso, group5_Results

def HDF5_Inputs():
    dsetO = group5[Table_O]
    if "Meter" == k_O:
        dsetO = dsetO[dsetO[k_O]<int((kmh_O/3.6*60)*int(Time_limits[1]))]
        dsetO[k_O] = dsetO[k_O]/(kmh_O/3.6*60) ##replace distance by time
    else: dsetO = dsetO[dsetO[k_O]<int(Time_limits[1])]

    dsetP = group5[Table_P]
    if "Meter" == k_P:
        dsetP = dsetP[dsetP[k_P]<int((kmh_P/3.6*60)*int(Time_limits[2]))]
        dsetP[k_P] = dsetP[k_P]/(kmh_P/3.6*60) ##replace distance by time
    else: dsetP = dsetP[dsetP[k_P]<int(Time_limits[2])]
    if Filter_P: dsetP = dsetP[dsetP[Filter_P]>0]

    dsetO = pandas.DataFrame(dsetO)
    dsetP = pandas.DataFrame(dsetP)
    if "Isochrones" in Modus: return dsetO, dsetP, ""
    IsoChronen = group5_Iso[Isochrone_Name]
    IsoChronen = pandas.DataFrame(np.array(IsoChronen))

    if "Potential" in Modus:
        for i in StructData:
            if i in dsetO.dtypes: dsetO.drop(i, axis=1, inplace=True)

    return dsetO, dsetP, IsoChronen

def HDF5_Results():
    if "Potential" in Modus:
        Columns = [('Orig_ID', 'int32')]
        for i in Measures:
            if i[-4:] == "Expo":
                for e in potfak:
                    e = str(e.split(".")[1])
                    if len(e)==2: e+="0"
                    Columns.append(((i+e).encode('ascii'),'int32'))
            elif i[-3:] == "Sum":
                for e in sumfak: Columns.append(((i+e).encode('ascii'),'int32'))
            else: Columns.append((i.encode('ascii'),'int32'))

    if "Distance" in Modus: Columns = [('Orig_ID', 'int32'),('FromStop','int32'),('Place_ID','int32'),
    ('ToStop','int32'),('Time', 'f8'),('Access', 'f8'),('Egress', 'f8'),('UH','i2'),('BH','i2'),('tofind','i2'),('Group','i2')]

    if Table_R in group5_Results.keys(): del group5_Results[Table_R]
    group5_Results.create_dataset(Table_R, data=np.array([],Columns), dtype=np.dtype(Columns), maxshape = (None,))
    Results_T = group5_Results[Table_R]
    Results_T.attrs.create("Parameter",str(text[0]))
    file5.flush()

    return Results_T

def Isochrones():
    arcpy.AddMessage("> calculate VISUM Isochrones")

    if "Distance" in Modus: Zeitbezug = True

    VISUM = win32com.client.dynamic.Dispatch("Visum.Visum.22")
    VISUM.loadversion(Network_PT)
    VISUM.Filters.InitAll()

    #--Results table--#
    if Isochrone_Name in group5_Iso.keys(): del group5_Iso[Isochrone_Name]
    Columns = np.dtype([('FromStop', 'int32'),('ToStop', 'int32'),('Time', 'f8'),('UH', 'i2'),('BH', 'i2')])
    group5_Iso.create_dataset(Isochrone_Name, data = np.array([],Columns), dtype = Columns, maxshape = (None,))
    file5.flush()
    IsoChronen = group5_Iso[Isochrone_Name]

    #calculate Isochrones for places (distance measures) and orgins (gravity / contour measures).
    if "Distance" in Modus: From_StopArea = np.unique(dsetP[Node_P])
    else: From_StopArea = np.unique(dsetO[Node_O])
    arcpy.AddMessage("> calculate Isochrones for "+str(len(From_StopArea))+" StopAreas")

    VISUM_Isochrones = VISUM.Analysis.Isochrones
    for n,Nr in enumerate(From_StopArea):
        NE = VISUM.CreateNetElements()
        NE.Add(VISUM.Net.StopAreas.ItemByKey(int(Nr)))
        arcpy.AddMessage("> Isochrone "+str(n+1)+" of "+str(len(From_StopArea)))
        VISUM_Isochrones.ExecutePuT(NE,"OV",str(Hours[0])+":00:00",str(Hours[1])+":00:00",int(Day[0]),int(Day[1]),PostRun*60*60,Zeitbezug) ##True == Arrival

        Ziel = np.array(VISUM.Net.StopAreas.GetMultiAttValues("No"))[:,1]
        Zeit = np.array(VISUM.Net.StopAreas.GetMultiAttValues("IsocTimePuT"))[:,1]/60
        UH = np.array(VISUM.Net.StopAreas.GetMultiAttValues("IsocTransfersPuT"))[:,1]

        if "Distance" in Modus: Liste_HB = np.column_stack((Ziel,np.repeat(Nr,len(UH)),Zeit+int(Time_limits[3]),UH,np.repeat(999,len(UH))))
        else: Liste_HB = np.column_stack((np.repeat(Nr,len(UH)),Ziel,Zeit+int(Time_limits[3]),UH,np.repeat(999,len(UH))))

        Liste_HB = Liste_HB[Liste_HB[:,2]<int(Time_limits[0])]

        #--Data into HDF5 table--#
        oldsize = len(IsoChronen)
        sizer = oldsize + len(Liste_HB)
        IsoChronen.resize((sizer,))
        Liste_HB = list(map(tuple, Liste_HB))
        IsoChronen[oldsize:sizer] = Liste_HB
        file5.flush()
        VISUM_Isochrones.Clear()

    IsoChronen.attrs.create("Parameter",str(text[1]))
    file5.flush()
    del VISUM

    arcpy.AddMessage("> finished after: "+str(int(time.time()-start_time)/60)+" minutes\n")
    IsoChronen = pandas.DataFrame(np.array(IsoChronen))
    return IsoChronen

def Iso_Slice(dsetO,dsetP,Iso_I):
    Orig_StopAreas = np.unique(dsetO[Node_O]) ##unique StopAreas at Origins
    Place_StopAreas = np.unique(dsetP[Node_P]) ##unique StopAreas at Places

    if "Distance" in Modus:
        if Filter_Group_P: header = 20 * len(np.unique(dsetP[Filter_Group_P])) * to_find
        else: header = 20 * to_find
    else: header = 10000
    loop_from, loop_range = 0, 1000000
    loops = (len(Iso_I)/loop_range)+1 ## +1 due to rounding

    #disaggregate Isochrones into parts due to the size
    for k in range(loops):
        iso_slice = Iso_I[loop_from:loop_from+loop_range]
        iso_slice = iso_slice[iso_slice["Time"]<=int(Time_limits[0])]

        iso_slice = iso_slice[np.in1d(iso_slice[fromStop].ravel(), Orig_StopAreas)] ##only Isochrones with connected Stops included
        iso_slice = iso_slice[np.in1d(iso_slice[toStop].ravel(), Place_StopAreas)]
        iso_slice = iso_slice.sort_values([fromStop,"Time"])
        iso_slice = iso_slice.groupby(fromStop).head(header).reset_index(drop=True)

        if k==0: Iso_f = iso_slice
        else: Iso_f = pandas.concat([Iso_f,iso_slice])

        loop_from+=loop_range

    return Iso_f

def NMT():
    arcpy.AddMessage("> starting with proximity area ("+str(Radius)+" meter)")
    arcpy.AddMessage("> maximum costs: "+Costs+" = "+str(Max_Costs))
    arcpy.Delete_management("ODMATRIX")
    arcpy.Delete_management("P_Shape")
    arcpy.Delete_management("O_Shape")

    #OD-Matrix
    if Filter_Group_P: NMT_find = 50
    elif "Potential" in Modus: NMT_find = ""
    else: NMT_find = to_find+1
    arcpy.MakeODCostMatrixLayer_na(Network,"ODMATRIX",Costs,Max_Costs,NMT_find,[Costs],"","","","","NO_LINES")
    p = arcpy.na.GetSolverProperties(arcpy.mapping.Layer("ODMATRIX"))
    Restriction_0 = list(p.restrictions) ##activate all restrictions
    p.restrictions = Restriction_0
    del p
    if Barriers != "": arcpy.AddLocations_na("ODMATRIX","Line Barriers",Barriers,"","")

    arcpy.MakeFeatureLayer_management(O_Shape, "O_Shape")
    fm_O = checkfm("O_Shape",O_Shape_ID)
    if Filter_P: arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape",Filter_P+">0")
    else: arcpy.MakeFeatureLayer_management(P_Shape, "P_Shape")
    fm_P = checkfm("P_Shape",P_Shape_ID)

    if "Distance" in Modus: arcpy.SelectLayerByLocation_management("O_Shape","intersect","P_Shape",Radius)
    if "Potential" in Modus: arcpy.SelectLayerByLocation_management("P_Shape","intersect","O_Shape",Radius)

    if fm_O is None:arcpy.AddLocations_na("ODMATRIX","Origins","O_Shape","Name "+O_Shape_ID+\
    " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","","","","EXCLUDE")
    else: arcpy.AddLocations_na("ODMATRIX","Origins","O_Shape",fm_O,"","","","","CLEAR","","","EXCLUDE")

    if fm_P is None: arcpy.AddLocations_na("ODMATRIX","Destinations","P_Shape","Name "+P_Shape_ID+\
    " 0; Attr_Minutes # #","","",[["MRH_Wege", "SHAPE"],["MRH_Luecken", "SHAPE"],["Ampeln", "NONE"],["Faehre_NMIV", "NONE"]],"","","","","EXCLUDE")
    else: arcpy.AddLocations_na("ODMATRIX","Destinations","P_Shape",fm_P,"","","","","CLEAR","","","EXCLUDE")

    arcpy.na.Solve("ODMATRIX","","CONTINUE")

    df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("ODMATRIX\Lines",["Name", "Total_"+Costs]))
    if len(df) == 0: return df

    df[[ID_O,ID_P+"_P"]] = df.Name.str.split(' - ',expand=True,).astype(int)
    df = df.rename(columns = {'Total_'+Costs:'Time'})
    df["UH"], df["BH"], df[k_O], df[k_P+"_P"] = [111,111,0,0]
    df.drop("Name", axis=1, inplace=True)

    if "Potential" in Modus:
        StructData.append(P_Shape_ID)
        Strukturen = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("P_Shape",StructData))
        df = pandas.merge(df,Strukturen,left_on=ID_P+'_P',right_on=P_Shape_ID)
        df.drop(P_Shape_ID, axis=1, inplace=True)
        df = df.groupby([ID_P+'_P',ID_O]).first()
        df = df.reset_index()

    if "Distance" in Modus: df["FromStop"], df["ToStop"] = [0,0]
    if "Potential" in Modus: df.drop([k_O,k_P+"_P"], axis=1, inplace=True)

    #arcpy.management.SaveToLayerFile("ODMATRIX",r'PATH\CF_Ergebnis',"RELATIVE")

    arcpy.AddMessage("> proximity area finished\n")
    return df

def potential():
    arcpy.AddMessage("> calculate potential measures")
    Orig = np.unique(dsetO[ID_O])
    loop_from, loop_range = 0, 100
    loops = (len(Orig)/loop_range)+1
    Iso = Iso_Slice(dsetO,dsetP,IsoChronen)

    for loop in range(loops):
        arcpy.AddMessage("> loop "+str(loop+1)+"/"+str(loops))
        dsetO_l = Orig[loop_from:loop_from+loop_range]
        dsetO_l = dsetO[np.in1d(dsetO[ID_O],dsetO_l)]
        loop_from+=loop_range

        dataiso = pandas.merge(dsetO_l,Iso,left_on=Node_O,right_on=fromStop)
        dataiso.loc[:,"Time"] = dataiso.loc[:,k_O]+dataiso.loc[:,"Time"]
        dataiso = dataiso[dataiso["Time"]<=(int(Time_limits[0]))-3].reset_index(drop=True) ##-3 from maximum time to keep array small

        try:
            dataiso = dataiso.sort_values([ID_O,toStop,"Time"])
            dataiso = dataiso.groupby([ID_O,toStop]).first().reset_index()
            dataiso = pandas.merge(dataiso,dsetP,left_on=toStop,right_on=Node_P)
            dataiso.loc[:,"Time"] = dataiso.loc[:,k_P+"_y"]+dataiso.loc[:,"Time"]

            if "NMT" in Modus:
                proxy = proximity[np.in1d(proximity[ID_O],dataiso[ID_O+"_x"])]
                proxy = proxy.rename(columns = {ID_O:ID_O+'_x',ID_P+'_P':ID_P+'_y'})
                dataiso = dataiso.append(proxy, ignore_index = True)

            dataiso = dataiso[dataiso["Time"]<=(int(Time_limits[0]))].reset_index(drop=True)
            dataiso = dataiso.sort_values([ID_O+"_x",ID_P+"_y","Time"])
            dataiso = dataiso.groupby([ID_O+"_x",ID_P+"_y"]).first().reset_index()

        except:
            arcpy.AddMessage("> error in loop "+str(loop+1))
            continue

        Origins = np.unique(dsetO_l[ID_O])
        for i in Origins:
            Result = [i]
            IsoP = dataiso[dataiso[ID_O+"_x"]==i].reset_index(drop=False)

            #--Berechne die Indikatorwerte--#
            for e in Measures:
                Column = e.split("__")[0] ##to get the name of places

                if e[-3:] == "Sum":
                    for n in sumfak:
                        Indi = IsoP[IsoP["Time"]<=int(n)]
                        Value = Indi[Column].sum()
                        Result.append(Value)

                elif e[-4:] == "Expo":
                    for n in potfak:
                        n = float(n)
                        Value = round(sum(np.exp(IsoP["Time"]*n) * IsoP[Column]))
                        Result.append(Value)

                elif e[-3:-1] == "UH":
                    Indi = IsoP[IsoP["UH"]<int(e[-1:])+1]
                    Value = Indi[Column].sum()
                    Result.append(Value)

                elif e[-6:] == "direct":
                    Indi = IsoP[IsoP["UH"]==111]
                    Value = Indi[Column].sum()
                    Result.append(Value)

                elif e[-3:-1] == "BH":
                    Indi = IsoP[IsoP["BH"]>=int(e[-1:])]
                    Value = Indi[Column].sum()
                    Result.append(Value)

                elif e[-4:-2] == "BH":
                    Indi = IsoP[IsoP["BH"]>=int(e[-2:])]
                    Value = Indi[Column].sum()
                    Result.append(Value)

                else: pass

            Result =[tuple(Result)]
            oldsize = len(Results_T)
            Results_T.resize((oldsize+1,))
            Results_T[oldsize:oldsize+1] = Result
            file5.flush()
        del dataiso
        gc.collect()

def Text():
    text = "Date: "+date.today().strftime("%B %d, %Y")+"; " +str("/".join(Modus))+\
    "; Time_limits: "+str("/".join(Time_limits))+";tofind: "+str(to_find)+\
    "; IsoName: "+str(Isochrone_Name)+"; Smooth PT: "+str(Smooth_PT)+"; Origins: "+str(Table_O)+"; Places: "+str(Table_P)
    if "Potential" in Modus: text = text + "; Measures: "+str("/".join(Measures))
    if "NMT" in Modus: text = text + "; NMT-Radius: "+str(Radius)+"; NMT-Costs: "+str(Max_Costs)
    if "Isochrones" in Modus:
        text_v = text+"; Hours: "+str("/".join(Hours))+"; PostRun: "+str(PostRun)
        return text, text_v
    else: return text, ""

#--preparation--#
text = Text()
file5, group5, group5_Iso, group5_Results = HDF5()
dsetO, dsetP, IsoChronen = HDF5_Inputs()
if "NMT" in Modus: proximity = NMT()
if "Isochrones" in Modus: IsoChronen = Isochrones()
Results_T = HDF5_Results()

#--measures--#
arcpy.AddMessage("> calculate measures\n")
if "Distance" in Modus: distance()
if "Potential" in Modus: potential()

#end
arcpy.AddMessage("> finished after "+str(int(time.time()-start_time))+" seconds")
file5.flush()
file5.close()