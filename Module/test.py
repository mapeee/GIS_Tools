# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 14:49:22 2020

@author: marcu
"""

import project
import pandas as pd

from pathlib import Path
path = Path.home() / 'python32' / 'python_dir.txt'
f = open(path, mode='r')
for i in f: path = i
path = Path.joinpath(Path(r'C:'+path),'PT_data','VISUM_FAN.txt')
f = path.read_text()
f = f.split('\n')

df_FAN = pd.read_excel(r'C:'+f[0], sheet_name=f[1])

a = project.project_table(df_FAN,"Master","X","Y","epsg:31467", "epsg:25832")


