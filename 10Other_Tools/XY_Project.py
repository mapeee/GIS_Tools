# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 10:02:46 2020

@author: marcus
"""

import xlwt
import pandas as pd
from pyproj import Transformer
from pathlib import Path
path = Path.home() / 'python32' / 'python_dir.txt'
f = open(path, mode='r')
for i in f: path = i
path = Path.joinpath(Path(r'C:'+path),'PT_data','VISUM_FAN.txt')
f = path.read_text().split('\n')


##Parameter
input_table = pd.read_excel(r'C:'+f[0], sheet_name=f[1])
X_f = "GK-X"
Y_f = "GK-Y"

in_proj = "epsg:31467"
out_proj = "epsg:25832"
transformer = Transformer.from_crs(in_proj, out_proj, always_xy=True)


##write headings to new excel_file
wb = xlwt.Workbook()
ws = wb.add_sheet(f[7])
results = 'C:'+f[6]

ws.write(0, 0, "FAN_Nr")
ws.write(0, 1, "Name")
ws.write(0, 2, "X_UTM")
ws.write(0, 3, "Y_UTM")

line = 1
for index, row in input_table.iterrows():
    X = str(row[X_f])
    X = X.replace(".","")
    X = X+"00000"
    X = int(X[:7])
    Y = str(row[Y_f])
    Y = Y.replace(".","")
    Y = Y+"00000"
    Y = int(Y[:7])
    x_out, y_out = transformer.transform(X, Y)
    print (x_out, y_out)
    if row["Master"] >0: ws.write(line, 0, row["Master"])
    else: ws.write(line, 0, row["HST-Nr"])
    ws.write(line, 1, row["Name + Ort"])
    ws.write(line, 2, x_out)
    ws.write(line, 3, y_out)
    
    line+=1
    
##output
wb.save(results)