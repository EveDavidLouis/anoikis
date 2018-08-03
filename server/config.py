import os
import json
import base64

#server
server = dict(
	host 			= os.environ.get('SERVER_HOST','0.0.0.0')
	,port 			= int(os.environ.get('SERVER_PORT',8081))
	,secret 		= os.environ.get('SERVER_SECRET','asecrect')
)
if os.environ.get('PORT'): server['port'] = int(os.environ.get('PORT'))
if os.environ.get('ANOIKIS_SERVICE_HOST'): server['host'] = int(os.environ.get('ANOIKIS_SERVICE_HOST'))
if os.environ.get('ANOIKIS_SERVICE_PORT'): server['port'] = int(os.environ.get('ANOIKIS_SERVICE_PORT'))

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

#sso
sso = dict(
	callback = os.environ.get('SSO_CALLBACK','')
	,clientId = os.environ.get('SSO_CLIENTID','')
	,secretId = os.environ.get('SSO_SECRETID','')
	,scope = os.environ.get('SSO_SCOPE','')
)
sso['code'] = sso['clientId']+ ':' + sso['secretId']
sso['authorization'] = 'Basic ' + str(base64.b64encode(sso['code'].encode()),'utf-8')