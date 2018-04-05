import json

def loadJson(myjson):
	try:
		json_object = json.loads(myjson)
	except ValueError:
		return None
	return json_object