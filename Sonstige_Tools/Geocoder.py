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
import requests
import time
start_time = time.time()

from pathlib import Path
path = Path.home() / 'python32' / 'python_dir.txt'
f = open(path, mode='r')
for i in f: path = i
path = Path.joinpath(Path(path),'GIS_Tools','Geocoder.txt')
f = path.read_text()
f = f.split('\n')


#--connecting to opencagegeocode--#
key_osm = f[1]
key_bing = f[2]
key_here = f[3]
geocoder_osm = OpenCageGeocode(key_osm)

#--open excel--#
excelfile = f[0]
wbk = openpyxl.load_workbook(excelfile)
wks = wbk.worksheets[0]

#--geocoding--#
for row in range(1,wks.max_row+1):##to prevent 0 as starting number
    if row == 1:continue ##no header
    result_bing = geocoder.bing(wks.cell(row,1).value, key=key_bing)
    try:
        wks.cell(row, 2).value = result_bing.lat
        wks.cell(row, 3).value = result_bing.lng
        wks.cell(row, 4).value = int(result_bing.postal)
        if result_bing.postal in wks.cell(row,1).value: wks.cell(row, 5).value = 0       
        
        else:
            wks.cell(row, 5).value = 1
            result_osm = geocoder_osm.geocode(wks.cell(row,1).value)
            wks.cell(row, 6).value = result_osm[0]["geometry"]["lat"]
            wks.cell(row, 7).value = result_osm[0]["geometry"]["lng"]
                                   
    except: continue
    time.sleep(0.1) ##pause 1.5 seconds
    print(row)

#here (not implemented yet)
# URL = "https://geocode.search.hereapi.com/v1/geocode"
# PARAMS = {'apikey':key_here,'q':wks.cell(row,1).value}
# r = requests.get(url = URL, params = PARAMS)
# data = r.json()
# data['items'][0]['position']['lat']
# data['items'][0]['position']['lng']


#--end--#
wbk.save(excelfile)
wbk.close()

seconds = int(time.time() - start_time)
print("--finished after ",seconds,"seconds--")