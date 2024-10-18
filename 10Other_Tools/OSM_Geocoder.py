# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 11:52:57 2024
"""
import os
import time
from pathlib import Path
import geopandas as gpd
import pandas as pd
start_time = time.time()

f = open(Path.home() / 'python32' / 'python_dir.txt', mode='r')
path = list(f)[0]
path = Path.joinpath(Path(path), 'GIS_Tools', 'OSM_Geocoder.txt')
f = path.read_text().split('\n')

# --connections--#
geodata = gpd.read_file(f[0])
addr = pd.read_excel(f[1])

# --values--#
STREET = 'NL.ADR-STR-PF'
HOUSE = 'NL.ADR-HNR'
ZIP = 'NL.ADR-PLZ'
CITY = 'NL.ADR-ORT'

# --prepare--#
addr.sort_values(by=[CITY, ZIP, STREET], inplace=True)


def geodata_prep(_geodata):
    _geodata["HOUSENO"] = _geodata["HOUSENO"].str.replace(' ', '')
    _geodata["HOUSENO"] = _geodata["HOUSENO"].str.replace(';', '/')
    _geodata["HOUSENO"] = _geodata["HOUSENO"].str.lower()
    return _geodata


def geocoder(_addr_all, _geodata):
    """function to find street in city"""
    _city, _zip, _street0 = "_city", "00000", "_street"
    for _i in _addr_all.iterrows():
        if _i[1][CITY] != _city:
            _city = _i[1][CITY]
            _data_city = _geodata[_geodata["CITY"] == _city]
        if len(_data_city) == 0:
            yield [0, 0, "error", "city missing"]
            continue
        if str(_i[1][ZIP]) != _zip:
            _data_zip = _data_city[_data_city["POSTCODE"] == str(_i[1][ZIP])]
        if _i[1][STREET] != _street0 or str(_i[1][ZIP]) != _zip:
            _zip = str(_i[1][ZIP])
            _street0 = _i[1][STREET]
            _street = _street0.replace("str.", "straße")
            _street = _street.replace("Str.", "Straße")
            _data_street = _data_zip[_data_zip["STREET"] == _street]
        if len(_data_street) == 0:
            _street = _i[1][STREET]
            _street = _street.replace("str.", "straße")
            _street = _street.replace("Str.", "Straße")
            _data_street = _data_city[_data_city["STREET"] == _street]
            if len(_data_street) == 0:
                yield [0, 0, "error", "street missing"]
                continue
        values = geocode_house(_i, _data_street)
        if values[2] == "error":
            _data_street = _data_city[_data_city["STREET"] == _street]
            values = geocode_house(_i, _data_street)
        yield values


def geocode_house(_addr, _geodata_street):
    """function to find the house number"""
    _house = str(_addr[1][HOUSE])
    _house = _house.lower().replace(" ", "")
    _note = ""
    if _house == "nan":
        _house = ""
    if len(_house) > 9:
        return [0, 0, "error", "house format error"]
    if _house not in _geodata_street["HOUSENO"].unique():
        if any(x in _house for x in ["-", " - ", "+", "/"]):
            for delimiter in ["-", " - ", "/", "+"]:  # split '- /'
                _house = " ".join(_house.split(delimiter))
            _house = _house.split()[0]
        _house = "".join(c for c in str(_house) if c.isdecimal())  # remove letters e.g. '7c -> 7'
        if _house not in _geodata_street["HOUSENO"].unique():  # different numbers (+/-10)
            if _house == "":
                return [0, 0, "error", "house missing"]
            for n in range(1, 11):
                if str(int(_house) + n) in _geodata_street["HOUSENO"].unique():
                    _house = str(int(_house) + n)
                    break
                if str(max(int(_house) - n, 1)) in _geodata_street["HOUSENO"].unique():
                    _house = str(max(int(_house) - n, 1))
                    break
                if n == 10:
                    return [0, 0, "error", "house missing"]
        _note = _house
    _data_house = _geodata_street[_geodata_street["HOUSENO"] == str(_house)]
    if str(_addr[1][ZIP]) not in _data_house["POSTCODE"].unique():
        if _note != "":
            _note = "zip: "+_data_house["POSTCODE"].iloc[0]+", house: "+_note
        else:
            _note = "zip: "+_data_house["POSTCODE"].iloc[0]
    return [_data_house.get_coordinates().iloc[0, 0], _data_house.get_coordinates().iloc[0, 1], "ok", str(_note)]


geodata = geodata_prep(geodata)
a = list(geocoder(addr, geodata))
addr[["x", "y", "geocoder", "note"]] = a

addr.to_excel(os.path.dirname(f[1])+"\\test2.xlsx")

# --end--#
seconds = int(time.time() - start_time)
print("--finished after ", seconds, "seconds--")
