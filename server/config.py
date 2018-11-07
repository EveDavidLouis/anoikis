import os
import json
import base64

#server
server = dict(
	host 			= os.environ.get('SERVER_HOST','0.0.0.0')
	,port 			= int(os.environ.get('SERVER_PORT',8081))
	,secret 		= os.environ.get('SERVER_SECRET','asecrect')
)
#if os.environ.get('ANOIKIS_SERVICE_HOST'): server['host'] = os.environ.get('ANOIKIS_SERVICE_HOST')
#if os.environ.get('ANOIKIS_SERVICE_PORT'): server['port'] = int(os.environ.get('ANOIKIS_SERVICE_PORT'))

#mongodb
mongodb = dict(
	host 		= os.environ.get('MONGO_HOST','localhost')
	,port 		= int(os.environ.get('MONGO_PORT',27017))
	,user 		= os.environ.get('MONGO_USER','admin')
	,pwd 		= os.environ.get('MONGO_PWD','1234')
	,db 		= os.environ.get('MONGO_DB','test')
)
mongodb['url'] = 'mongodb://'+mongodb['user']+':'+ mongodb['pwd'] +'@'+str(mongodb['host'])+':'+str(mongodb['port']) +'/' + mongodb['db'] 

#tripwire
tripwire = []
if os.environ.get('TRIPWIRE'): 	tripwire = json.loads(os.environ.get('TRIPWIRE'))

#esi_api
esi_api = dict(
	callback = os.environ.get('ESI_API_CALLBACK','')
	,clientId = os.environ.get('ESI_API_CLIENTID','')
	,secretId = os.environ.get('ESI_API_SECRETID','')
	,scope = os.environ.get('ESI_API_SCOPE','')
)
esi_api['code'] = esi_api['clientId']+ ':' + esi_api['secretId']
esi_api['authorization'] = 'Basic ' + str(base64.b64encode(esi_api['code'].encode()),'utf-8')

#esi_login
esi_login = dict(
	callback = os.environ.get('ESI_LOGIN_CALLBACK','')
	,clientId = os.environ.get('ESI_LOGIN_CLIENTID','')
	,secretId = os.environ.get('ESI_LOGIN_SECRETID','')
)
esi_login['code'] = esi_login['clientId']+ ':' + esi_login['secretId']
esi_login['authorization'] = 'Basic ' + str(base64.b64encode(esi_login['code'].encode()),'utf-8')

