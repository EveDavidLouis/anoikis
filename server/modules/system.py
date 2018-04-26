from tornado import gen 
from server.utils import csv

import logging
logger = logging.getLogger('system')

@gen.coroutine
def GET(webHandler,payload={}):

	_path = webHandler.getPath()
	_mode = ''
	_system = ''

	if len(_path) > 1 : _system = str(_path[1])
	if len(_path) > 2 : _mode 	= str(_path[2])

	if _system == '' : _system = 'Jita'

	solarMap = webHandler.settings['solarMap']

	result = solarMap.getSystemByName(_system)
	
	if _mode == 'json':
		payload = result
		return {'mode':'json','data':payload}

	elif _mode=='csv':
		if not isinstance(result,list): result = [result]
		payload = csv.toCSV(result,['_id','name','systemClass','spaceType','constellation','region','securityStatus','securityClass','connections','staticGroup','statics','effect','mapped','position','shattered'],',')
		return {'mode':'direct','data':payload}
	
	if result : 
		payload['details'] = result
		payload['speech'] = solarMap.getSpeech(result)
		return {'mode':'render','template':'system.html','data':payload}
	
	else:
		return {'mode':'json','data':None}