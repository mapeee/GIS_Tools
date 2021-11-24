# -*- coding: cp1252 -*-
#!/usr/bin/python
#Calculate accessibility value from Line-Layer in ArcGIS
#Marcus März 2016 (new Version November 2021)
#für Python 2.7.5
#-------------------------------------------------------------------------------

import arcpy
import time
import h5py
import numpy as np
import pandas
start_time = time.time()

#--GIS Parameters--#
Datenbank = arcpy.GetParameterAsText(0)
Group = arcpy.GetParameterAsText(1)
Table_results = arcpy.GetParameterAsText(2)
Routen = arcpy.GetParameterAsText(3)
Costs = arcpy.GetParameterAsText(4)
Layer_E = arcpy.GetParameterAsText(5)
ID_E = arcpy.GetParameterAsText(6)
Layer_S = arcpy.GetParameterAsText(7)
ID_S = arcpy.GetParameterAsText(8)
Places = arcpy.GetParameterAsText(9)
Max_costs = arcpy.GetParameterAsText(10)
Measures = arcpy.GetParameterAsText(11)
sumfak = arcpy.GetParameterAsText(12)
potfak = arcpy.GetParameterAsText(13)
Places = Places.split(";")
Measures = Measures.split(";")
potfak = potfak.replace(",",";")
potfak = potfak.split(";")
sumfak = sumfak.replace(",",";")
sumfak = sumfak.split(";")


def df_org_desti():
    #--IDs from Origins--#
    df_E = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("OD Cost Matrix\Origins","Name"))
    df_E["Name"] = df_E["Name"].astype(int)
    df_E = df_E.rename(columns={"Name": ID_E})

    #--IDs and weight of places--#
    df_S = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray("OD Cost Matrix\Destinations","Name"))
    df_S["Name"] = df_S["Name"].astype(int)
    df_S = df_S.rename(columns={"Name": ID_S})
    if ID_S not in Places: df_Slayer = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(Layer_S,Places+[ID_S])) ##for contour and gravity measure
    else: df_Slayer = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(Layer_S,Places))
    df_Slayer[ID_S] = df_Slayer[ID_S].astype(int)
    df_S = pandas.merge(df_S,df_Slayer)
    return df_E, df_S

def HDF5():
    f5 = h5py.File(Datenbank,'r+') ##HDF5-File
    gr = f5[Group]
    Ergebnis_array = []
    data = np.array(Ergebnis_array,Spalten_ind)
    if Table_results in gr.keys(): del gr[Table_results]
    gr.create_dataset(Table_results, data=data, dtype=Spalten_ind, maxshape = (None,))
    result_t = gr[Table_results]
    f5.flush()
    return f5, result_t

def indicators():
    global Spalten_ind
    Spalten_ind = [('ID','int32')]
    Indi = 0 ##amount of different indicators
    for i in Measures:
        for e in Places:
            if i=="Contour":
                for f in sumfak:
                    Spalten_ind.append(((e+"CON"+str(f)).encode('ascii'),'int32'))
                    Indi = Indi+1
            if i=="Gravity":
                for f in potfak:
                    f = f.split(".")[1]
                    f+="0"
                    Spalten_ind.append(((e+"EXP"+str(f[:3])).encode('ascii'),'int32'))
                    Indi = Indi+1
            if i=="Distance":
                Spalten_ind.append(((e+"NEXT").encode('ascii'),'int32'))
                Spalten_ind.append(((e+"_"+Costs.replace("Total_","")).encode('ascii'),'<f8'))
                Indi = Indi+1
    Spalten_ind = np.dtype(Spalten_ind)
    return Indi

def save_to_HDF5(RESULT,results_all):
    RESULT =[tuple(RESULT)]
    size = len(results_all)
    results_all.resize((size+1,))
    results_all[size:(size+1)] = RESULT
    file5.flush()
    return results_all


###############
#--beginning / preparing--#
###############
arcpy.AddMessage("> starting")

Indi_n = indicators()
file5, results = HDF5()
df_E, df_S = df_org_desti()

#--Loop for rows / routes--#
OID_count = len(df_E)
arcpy.AddMessage("> "+str(OID_count)+" Origins")
Loops = (OID_count/100)+1 ##+1 for uneven numbers

for h in range(Loops):
    arcpy.AddMessage("> places up to "+str((h+1)*100)+" from "+str(OID_count))
    df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(Routen,["Name",Costs],"OriginID >= "+\
    str(h*100)+" and OriginID < "+str((h+1)*100)))
    df[["Orig", "Place"]] = df['Name'].str.split(' - ', 1, expand=True).astype(int)
    del df["Name"]
    df = df[df[Costs]<=int(Max_costs)]

    #--Join Origins / Places--#
    df = pandas.merge(df,df_E,left_on="Orig",right_on=ID_E)
    df = pandas.merge(df,df_S,left_on="Place",right_on=ID_S)
    if ID_E == ID_S: df = df.rename(columns={ID_E+"_x": ID_E})

    #--calculate indicator values--#
    for origin in pandas.unique(df[ID_E]):
        origin_RESULT = []
        origin_RESULT.append(origin)
        df_Routes = df[df[ID_E]==origin]
        if len(df_Routes) == 0: ##no (fitting under max costs) route from this origin
            for e in range(Indi_n): origin_RESULT.append(0)
            results = save_to_HDF5(origin_RESULT, results)
            continue

        for i in Measures:
            for s in Places:
                if i=="Contour":
                    for n in sumfak:
                        Indi = df_Routes[df_Routes[Costs]<=int(n)]
                        Value = Indi[s].sum()
                        origin_RESULT.append(Value)

                if i=="Gravity":
                    for n in potfak:
                        n = float(n)
                        Value = round(sum(np.exp(df_Routes[Costs]*n) * df_Routes[s]))
                        origin_RESULT.append(Value)

                if i =="Distance":
                    Indi = df_Routes[df_Routes[s]>0]
                    Indi = Indi.reset_index()
                    Value = Indi.iloc[Indi[Costs].idxmin()]
                    origin_RESULT = origin_RESULT + [Value["ID_y"],Value[Costs]]

        #--Data into HDF5 table--#
        results = save_to_HDF5(origin_RESULT, results)

###########
#--End--#
###########
text = "Date: "+str(time.localtime()[0:3])+"; Origins: "+Layer_E+", Places: "+Layer_S
results.attrs.create("Parameter",str(text))
file5.flush()
file5.close()
arcpy.AddMessage("> finished after "+str(int(time.time()-start_time))+" seconds")