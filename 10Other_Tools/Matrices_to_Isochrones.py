#!/usr/bin/python
# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name: Matrices_to_Isochrones
# Purpose: Transformation and export of PTV VISUM SkimMatrices to HDF5-Dataframe
# Author:      mape
# Created:     19/01/2016 (new Version November 2021)
# Copyright:   (c) mape 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
from datetime import date
import h5py
import math
import numpy as np
import os
import pandas as pd
import win32com.client.dynamic

#--ArcGIS Parameter--#
Network = arcpy.GetParameterAsText(0)
Datafile= arcpy.GetParameterAsText(1)
group5 = arcpy.GetParameterAsText(2)
I_Name = arcpy.GetParameterAsText(3)
max_time = int(arcpy.GetParameterAsText(4))
hours = int(arcpy.GetParameterAsText(5))*60 ##for initial waiting time
Origin_wait_time = bool(arcpy.GetParameterAsText(6)=="true")
shutdown = bool(arcpy.GetParameterAsText(7)=="true")
calculate = bool(arcpy.GetParameterAsText(8)=="true")
cal_scenario = bool(arcpy.GetParameterAsText(9)=="true")
I_zero_case = arcpy.GetParameterAsText(10)

def HDF5(Data):
    result_array = []
    Columns = np.dtype([('FromStop', 'i4'),('ToStop', 'i4'),('Time', 'i4'),('UH', 'i2'),('BH', 'i2')])
    data = np.array(result_array,Columns)
    file5 = h5py.File(Data,'r+')
    gr = file5[group5]
    if I_Name in gr.keys(): del gr[I_Name]
    gr.create_dataset(I_Name, data = data, dtype = Columns, maxshape = (None,))
    file5.flush()
    return file5, gr, gr[I_Name]

def isochrones(V,JRT,NTR,SFQ,Iso):
    StopAreaNo = np.array(V.Net.StopAreas.GetMultiAttValues("No",False)).astype("int")[:,1]
    StopAreaNoActive = np.array(V.Net.StopAreas.GetMultiAttValues("No",True)).astype("int")[:,1]

    for i in range(1,len(StopAreaNo)+1):
        result_array = []
        From = int(StopAreaNo[i-1])
        if From not in StopAreaNoActive: continue

        matJRT = np.array(V.Net.Matrices.ItemByKey(JRT).GetRow(i))
        matNTR = np.array(V.Net.Matrices.ItemByKey(NTR).GetRow(i))
        matSFQ = np.array(V.Net.Matrices.ItemByKey(SFQ).GetRow(i))

        for e,Nr in enumerate(StopAreaNo):
            To = int(Nr)
            TTime = matJRT[e]
            if Origin_wait_time is True:
                try: ##error if BH = 0 or Time = 0 --> Internal Trips
                    SWZ = 0.53*((hours/float(matSFQ[e]))**0.75)
                    if SWZ > 10:SWZ = 10
                    TTime+= SWZ
                except: pass
            TTime = int(round_half_up(TTime)) ##Due to rounding in Python 3
            UH = int(matNTR[e])
            BH = int(matSFQ[e])

            result_array.append((From,To,TTime,UH,BH))

        if len(result_array) == 0: continue
        result_array = np.array(result_array)
        result_array = result_array[result_array[:,2]<max_time]

        #--Data into HDF5 table--#
        oldsize = len(Iso)
        sizer = oldsize + len(result_array)
        Iso.resize((sizer,))
        result_array = list(map(tuple, result_array))
        Iso[oldsize:sizer] = result_array
    file5.flush()

def matrices(VISUM):
    for Matrix in VISUM.Net.Matrices:
        if Matrix.AttValue("ObjectTypeRef") == 'OBJECTTYPEREF_STOPAREA':
            if Matrix.AttValue("Code") == "JRT" and "_Tag" in Matrix.AttValue("Name"): JRT = int(Matrix.AttValue("No")) ##Traveltime
            if Matrix.AttValue("Code") == "NTR" and "_Tag" in Matrix.AttValue("Name"): NTR = int(Matrix.AttValue("No")) ##Transfers
            if Matrix.AttValue("Code") == "SFQ" and "_Tag" in Matrix.AttValue("Name"): SFQ = int(Matrix.AttValue("No")) ##Service frequency
    return JRT, NTR, SFQ

def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n*multiplier + 0.5) / multiplier

def scenario(I_S,I_0,gr5):
    arcpy.AddMessage("> scenario")
    dset_S = gr5[I_S]
    para = dset_S.attrs["Parameter"]

    dset_S = pd.DataFrame(np.array(dset_S))
    dset_0 = pd.DataFrame(np.array(gr5[I_0]))
    dset = dset_S.merge(dset_0,how="left",on=["FromStop","ToStop"])
    dset = dset[(dset.Time_x != dset.Time_y) | (dset.UH_x != dset.UH_y) | (dset.BH_x != dset.BH_y)]
    dset.drop(["Time_y" ,"UH_y" ,"BH_y"], axis=1, inplace=True)
    dset.rename(columns={"Time_x": "Time", "UH_x": "UH", "BH_x": "BH"},inplace=True)

    del gr5[I_S]
    file5.flush()

    Columns = np.dtype([('FromStop', 'i4'),('ToStop', 'i4'),('Time', 'i4'),('UH', 'i2'),('BH', 'i2')])
    result_array = dset.to_records(index=False)
    data = np.array(result_array,Columns)
    dset = gr5.create_dataset(I_S, data = data, dtype = Columns)
    dset.attrs.create("Parameter",para)
    dset.attrs.create("Scenario",str(I_0))
    file5.flush()

def text(dset):
    Text = str(Network.split("\\")[-1])+"; period: "+str(int(hours/60))+"h; Origin wait: "+str(Origin_wait_time)+"; max time: "+\
        str(max_time)+"min; Date: "+str(date.today().strftime("%B %d, %Y"))
    dset.attrs.create("Parameter",Text)
    file5.flush()

def VISUM_open(Network,cal):
    arcpy.AddMessage("> PT-Network: "+Network)
    VISUM = win32com.client.dynamic.Dispatch("Visum.Visum.22")
    VISUM.loadversion(Network)
    if cal_scenario is True: VISUM.Filters.InitAll()
    if cal is True:
        try:
            VISUM.Procedures.Execute()
            arcpy.AddMessage("> skim matrices calculated")
        except: arcpy.AddMessage("> error calculating skim matrix")
    return VISUM

#--caluclate--#
arcpy.AddMessage("> starting")
file5, group5, Iso_file = HDF5(Datafile)
VISUM = VISUM_open(Network,calculate)
JRT, NTR, SFQ = matrices(VISUM)
isochrones(VISUM,JRT,NTR,SFQ,Iso_file)
text(Iso_file)

if cal_scenario is True: scenario(I_Name,I_zero_case,group5)

#--end--#
arcpy.AddMessage("> finished")
file5.close()
VISUM = False
if shutdown is True: os.system("shutdown /s /t 1")