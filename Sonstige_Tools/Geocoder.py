#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mape
#
# Created:     23/11/2017
# Copyright:   (c) mape 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from opencage.geocoder import OpenCageGeocode
import geocoder
import openpyxl
import time
from pathlib import Path
path = Path.home() / 'python32' / 'python_dir.txt'
f = open(path, mode='r')
for i in f: path = i
path = Path.joinpath(Path(r'C:'+path),'GIS_Tools','Geocoder.txt')
f = path.read_text()
f = f.split('\n')

excelfile = "C:"+f[0]


#--connecting to opencagegeocode--#
key_osm = f[1]
key_bing = f[2]
geocoder_osm = OpenCageGeocode(key_osm)

#--open excel--#
wbk = openpyxl.load_workbook(excelfile)
wks = wbk.worksheets[0]
number_r = len(wks.rows) ##number of rows
number_c = 4 ##number of columns

#--loop over adresses--#
for r in range(1,number_r+1):##to prevent 0 as starting number
    if r==1:continue ##dont need header
    query = ""
    for c in range(1,number_c+1):
        if c==1:continue ##dont need the name
        #query
        try:query = query+" "+wks.cell(row=r, column=c).value
        except:query = query+" "+str(wks.cell(row=r, column=c).value)

    #--geocode--#
##    result_osm = geocoder_osm.geocode(query)
    result_bing = geocoder.bing(query, key=key_bing)

    try:
##        wks.cell(row=r, column=5).value = result_osm[0]["geometry"]["lat"]
##        wks.cell(row=r, column=6).value = result_osm[0]["geometry"]["lng"]
        wks.cell(row=r, column=5).value = result_bing.lat
        wks.cell(row=r, column=6).value = result_bing.lng
        wks.cell(row=r, column=7).value = result_bing.postal
    except: continue
    time.sleep(1.1) ##pause 1.5 seconds
    print(r)

#--end--#
wbk.save(excelfile)
print("fertig")