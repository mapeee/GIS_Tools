# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 11:52:57 2024
"""
import geopandas as gpd
import pandas as pd
import os

import time
start_time = time.time()
from pathlib import Path
f = open(Path.home() / 'python32' / 'python_dir.txt', mode='r')
for i in f: path = i
path = Path.joinpath(Path(path),'GIS_Tools','OSM_Geocoder.txt')
f = path.read_text().split('\n')

#--connections--#
geodata = gpd.read_file(f[0])
addr = pd.read_excel(f[1])

#--values--#
Street = 'NL.ADR-STR-PF'
House = 'NL.ADR-HNR'
ZIP = 'NL.ADR-PLZ'
City = 'NL.ADR-ORT'

#--prepare--#
addr.sort_values(by=[City,ZIP,Street], inplace=True)

def geocoder(_addr_all, _geodata):  
    _list = []
    _city, _zip, _street0 = "_city", "00000", "_street"
    for i in _addr_all.iterrows():
        if i[1][City] != _city:
            _city = i[1][City]
            _data_city = _geodata[_geodata["CITY"] == _city]
        if len(_data_city) == 0:
            _list.append([0, 0, "error", "city missing"])
            continue
        if str(i[1][ZIP]) != _zip:
            _data_zip = _data_city[_data_city["POSTCODE"] == str(i[1][ZIP])]
        if i[1][Street] != _street0 or str(i[1][ZIP]) != _zip:
            _zip = str(i[1][ZIP])
            _street0 = i[1][Street]
            _street = _street0.replace("str.", "straße")
            _street = _street.replace("Str.", "Straße")
            _data_street = _data_zip[_data_zip["STREET"] == _street]
        if len(_data_street) == 0:
            _street = i[1][Street]
            _street = _street.replace("str.", "straße")
            _street = _street.replace("Str.", "Straße")
            _data_street = _data_city[_data_city["STREET"] == _street]
            if len(_data_street) == 0:
                _list.append([0, 0, "error", "street missing"])
                continue
        values = geocode_house(i,_data_street)
        if values[2] == "error":
            _data_street = _data_city[_data_city["STREET"] == _street]
            values = geocode_house(i,_data_street)
        _list.append(values)

    return _list

def geocode_house(_addr, _geodata_street):
    _house = str(_addr[1][House])
    _note = ""
    
    if len(_house) > 9:
        return [0, 0, "error", "house format error"]
    
    if _house not in _geodata_street["HOUSENO"].unique():
        if any(x in _house for x in ["-", " - ", "+", "/"]):
            for delimiter in ["-", " - ", "/", "+"]:#split '- /'
                _house = " ".join(_house.split(delimiter))
            _house = _house.split()[0]
        _house = "".join(c for c in str(_house) if  c.isdecimal()) #remove letters e.g. '7c -> 7'
        if _house not in _geodata_street["HOUSENO"].unique(): #different numbers (+/-10)
            _house = str(max(int(_house)-10,1))
            n = 1
            while n <20:
                _house = str(int(_house) + 1)
                if _house in _geodata_street["HOUSENO"].unique(): break
                if n == 19: return [0, 0, "error", "house missing"]
                n+=1
        _note = _house
    
    _data_house = _geodata_street[_geodata_street["HOUSENO"] == str(_house)]
    
    if str(_addr[1][ZIP]) not in _data_house["POSTCODE"].unique():
        if _note != "": _note = "zip: "+_data_house["POSTCODE"].iloc[0]+", house: "+_note
        else: _note = "zip: "+_data_house["POSTCODE"].iloc[0]
    
    return [_data_house.get_coordinates().iloc[0,0], _data_house.get_coordinates().iloc[0,1], "ok", str(_note)]

a = geocoder(addr,geodata)
addr[["x","y","geocoder","note"]] = a

addr.to_excel(os.path.dirname(f[1])+"\\test2.xlsx")

#--end--#
seconds = int(time.time() - start_time)
print("--finished after ",seconds,"seconds--")