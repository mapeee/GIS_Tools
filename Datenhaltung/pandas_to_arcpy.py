x = np.array(np.rec.fromrecords(dataiso.values))
names = dataiso.dtypes.index.tolist()
x.dtype.names = tuple(names)
arcpy.da.NumPyArrayToTable(x, r'C:\???\Material.gdb\dataiso3')