x = np.array(np.rec.fromrecords(dataiso.values))
x.dtype.names = tuple(dataiso.dtypes.index.tolist())
arcpy.da.NumPyArrayToTable(x, r'C:\???')