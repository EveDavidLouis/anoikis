import os
import json
import base64

tripwire = []

server = dict(
	host = '0.0.0.0'
	,port = 8081
	,autoreload = True
)

sso = dict(
	callback = os.environ.get('SSO_CALLBACK')
	,clientId = os.environ.get('SSO_CLIENTID')
	,secretId = os.environ.get('SSO_SECRETID')
	,scope = os.environ.get('SSO_SCOPE')
)

mongodb = dict(
	host = 'localhost'
	,port = 27017
	,db = 'eve-online'
)

if os.environ.get('MONGO_DB_SERVICE_HOST'):

	mongodb = dict(
		host = os.environ['MONGO_DB_SERVICE_HOST']
		,port = int(os.environ['MONGO_DB_SERVICE_PORT'])
		,db = 'eve-online'
	)

	server['autoreload'] = False


if os.environ.get('SERVER_PORT'): 			server['port'] 			= int(os.environ.get('SERVER_PORT'))
if os.environ.get('SERVER_AUTORELOAD'): 	server['autoreload'] 	= os.environ.get('SERVER_AUTORELOAD')

if os.environ.get('TRIPWIRE'): 				tripwire 				= json.loads(os.environ.get('TRIPWIRE'))

#sso computed
sso['code'] = sso['clientId']+ ':' + sso['secretId']
sso['authorization'] = 'Basic ' + str(base64.b64encode(sso['code'].encode()),'utf-8')