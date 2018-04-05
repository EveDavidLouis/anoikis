from tornado import gen 

from server.utils.fetch import asyncFetch
from server.config import config

import json
import urllib.parse

import logging
logger = logging.getLogger('sso')

@gen.coroutine
def GET(webHandler,payload={}):

	inputs = webHandler.getInputs()
	
	db = webHandler.settings['db']

	headers = {}
	headers['Authorization'] = config.sso['authorization']
	headers['Content-Type'] = 'application/x-www-form-urlencoded'
	headers['Host'] = 'login.eveonline.com'
	
	payload = {}
	payload['grant_type'] = 'authorization_code'
	payload['code'] = inputs['code']

	url = 'https://login.eveonline.com/oauth/token/'

	body=urllib.parse.urlencode(payload)

	chunk = { 'kwargs':{'method':'POST' , 'body':body , 'headers':headers } , 'url':url }
	response = yield asyncFetch(chunk)

	oAuth = json.loads(response.body.decode())

	url = 'https://login.eveonline.com/oauth/verify'

	headers['Authorization'] = 'Bearer ' + oAuth['access_token']
	headers['Host'] = 'login.eveonline.com'

	chunk = { 'kwargs':{'method':'GET', 'headers':headers } , 'url':url }
	response = yield asyncFetch(chunk)

	bearer = json.loads(response.body.decode())
	
	oAuth.update(bearer)
	webHandler.setSession('oAuth',oAuth)
	webHandler.setSession('id',oAuth['CharacterID'])

	result = yield db.pilots.update_one({'_id':oAuth['CharacterID']},{'$set':oAuth},upsert=True)

	return {'mode':'redirect','url': '/' + inputs['state'] }
