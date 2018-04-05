from tornado import gen 

import json

def json_serial(obj):
	"""JSON serializer for objects not serializable by default json code"""

	if isinstance(obj, (datetime, date)):
		return str(obj)
	raise TypeError ("Type %s is so not serializable..." % type(obj))

def toCSV(data=[],headers=[],separator=','):

	row = []
	for i in headers:
		row.append(i)
	csv = separator.join(row)
	csv+= "\n"

	for line in data:
		row = []

		for header in headers:
			if header in line : row.append(json.dumps(line[header]).replace('"', '').replace(',', '')) 
			else: row.append('')
		
		csv+= separator.join(row)
		csv+= "\r\n"

	return csv