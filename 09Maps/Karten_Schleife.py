#-------------------------------------------------------------------------------
# Name:        Skript, um aus Struktur-Gruppen einzelne Files zu machen.
# Purpose:
#
# Author:      mape
#
# Created:     19/05/2016
# Copyright:   (c) mape 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy

from pathlib import Path
path = Path.home() / 'python32' / 'python_dir.txt'
f = open(path, mode='r')
for i in f: path = i
path = Path.joinpath(Path(r'C:'+path),'GIS_Tools','Karten_Schleife.txt')
f = path.read_text()
f = f.split('\n')

#--Input--#
Pfad_GIS = "C:"+f[0]
GIS_Layer = "C:"+f[1]


Gruppen = \
[[[1],"SH_E_LZO_500","Laendlicher Zentralort"],\
[[2],"SH_E_MZ_500","Mittelzentrum"],\
[[3],"SH_E_OZ_500","Oberzentrum"],\
[[4],"SH_E_eO_500","Stadtrandkern 1. Ordnung"],\
[[5],"SH_E_zO_500","Stadtrandkern 2. Ordnung"],\
[[6],"SH_E_UZ_500","Unterzentrum"],\
[[7],"SH_E_UZ_MZ_500","Unterzentrum Teilfkt. Mittelzentrum"]]
Modi = ["minpkw","minfuss","minrad","minoev"]

###########################################################################
#--Berechnung--#
###########################################################################
for i in Gruppen:
    print(i)

    ##MXD Reisezeit##
    mxd = arcpy.mapping.MapDocument(r"V:"+f[2])
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    addLayer = arcpy.mapping.Layer("C:"+f[3]+i[1])
    arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")
    layer = arcpy.mapping.ListLayers(mxd, "*", df)
    layer[0].definitionQuery = "Gruppe = "+str(i[0][0])
    layer[0].name = i[2]
    layer[10].visible = True
    
    for vm in Modi:
        if vm == "minpkw":            
            arcpy.ApplySymbologyFromLayer_management(layer[10],layer[6])
            layer[3].name = "Reisezeit mit dem Pkw in Minuten"
            arcpy.mapping.ExportToPDF(mxd, r"C:"+f[6]+i[1]+"_pkw.pdf")
            
        if vm == "minrad":            
            arcpy.ApplySymbologyFromLayer_management(layer[10],layer[8])
            layer[3].name = "Reisezeit mit dem Fahrrad in Minuten"
            arcpy.mapping.ExportToPDF(mxd, r"C:"+f[6]+i[1]+"_Rad.pdf")
            
        if vm == "minfuss":            
            arcpy.ApplySymbologyFromLayer_management(layer[10],layer[7])
            layer[3].name = "Gehzeit in Minuten"
            arcpy.mapping.ExportToPDF(mxd, r"C:"+f[6]+i[1]+"_fuss.pdf")
            
        if vm == "minoev":            
            arcpy.ApplySymbologyFromLayer_management(layer[10],layer[9])
            layer[3].name = "Reisezeit mit dem ÖPNV in Minuten"
            arcpy.mapping.ExportToPDF(mxd, r"C:"+f[6]+i[1]+"_oev.pdf")
    
    arcpy.mapping.RemoveLayer(df, layer[10])  
    del mxd
    
    ##MXD Umstiege##
    mxd = arcpy.mapping.MapDocument(r"V:"+f[4])
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    addLayer = arcpy.mapping.Layer("C:"+f[5]+i[1])
    arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")
    layer = arcpy.mapping.ListLayers(mxd, "*", df)
    layer[0].definitionQuery = "Gruppe = "+str(i[0][0])
    layer[0].name = i[2]
    layer[6].visible = True
        
    arcpy.ApplySymbologyFromLayer_management(layer[6],layer[3])
    arcpy.mapping.ExportToPDF(mxd, r"C:"+f[6]+i[1]+"_uh.pdf")
    arcpy.mapping.RemoveLayer(df, layer[6])
    
    del mxd
