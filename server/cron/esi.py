from tornado import gen 
from server.utils import fetch

import json
import urllib.parse

import logging
logger = logging.getLogger('cron-esi')

@gen.coroutine
def refreshTokens(db=None,authorization=None):	
	
	requests = []
	
	query={}
	output={'_id':1,'refresh_token':1}

	for document in (yield db.pilots.find(query,output).to_list(length=100)):
		
		headers = {}
		headers['Authorization'] = authorization
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
		headers['Host'] = 'login.eveonline.com'
		headers['_id'] = str(document['_id'])

		body = {}
		body['grant_type'] = 'refresh_token'
		body['refresh_token'] = document['refresh_token']
		body=urllib.parse.urlencode(body)

		url = {'kwargs':{'method':'POST','body':body,'headers':headers},'url':'https://login.eveonline.com/oauth/token/' }
		requests.append(url)

	chunkSize = 50
	data = []
	for i in range(0, len(requests), chunkSize):
		
		chunk = requests[i:i + chunkSize]
		responses = yield fetch.asyncMultiFetch(chunk)

		for response in responses:
			if response.code == 200:
				bearer = json.loads(response.body.decode())
				bearer['CharacterID'] = int(response.request.headers['_id'])
				result = yield db.pilots.update({'_id':bearer['CharacterID']},{'$set':bearer},upsert=True)
			elif response.code == 400:
				_id = int(response.request.headers['_id'])
				result = yield db.pilots.update({'_id':_id},{'$set':{'delete':1}},upsert=True)
			else:
				logger.info(response.error)

	result = yield db.pilots.delete_many({'delete':1})
	logger.info('UPDATE')