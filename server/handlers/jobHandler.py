import datetime , json
from tornado import gen
from tornado.queues import Queue
import urllib

import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('cron')

class QueueWorker():

	def __init__(self,db=None,fe=None,ws=None):
		self.q = Queue(maxsize=256)
		self.db = db

	@gen.coroutine
	def run(self):

		while True:
			item = yield self.q.get()
			try:
				logger.info('working on ' + str(item))
			except:
				pass
			finally:
				self.q.task_done()

	@gen.coroutine
	def add(self,message=None):
		self.q.put(message)

class CronWorker(object):
	
	def __init__(self,db=None,fe=None,ws=None,co=None):
		
		self.ws = ws
		self.fe = fe
		self.db = db
		self.co = co
	
	@gen.coroutine
	def run(self):

		# for i in self.ws.waiters:
		# 	i.write_message({'clients':len(self.ws.waiters)})

		cursor = self.db['pilots'].find({'esi_api':{'$exists':1}},{'esi_api.CharacterID':1,'esi_api.access_token':1,'esi_api.refresh_token':1})
		documentList = yield cursor.to_list(length=10000)

		for document in documentList:
				
				esi_api = document['esi_api']

				url = 'https://esi.evetech.net/latest/characters/' + str(esi_api['CharacterID']) + '/location/?token=' + esi_api['access_token']
				chunk = { 'kwargs':{'method':'GET'} , 'url':url }
				
				response = yield self.fe.asyncFetch(chunk)
				if response.code == 200:
					payload = json.loads(response.body.decode())
					result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':{'location':payload}})
				else:
					logger.warning('refresh_token:' + str(esi_api['CharacterID']))
					self.refreshSSO(esi_api)

	@gen.coroutine
	def refreshSSO(self,oAuth=None):
		
		headers = {}
		headers['Authorization'] = self.co.esi_api['authorization']
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
		headers['Host'] = 'login.eveonline.com'
		
		payload = {}
		payload['grant_type'] = 'refresh_token'
		payload['refresh_token'] = oAuth['refresh_token']

		url = 'https://login.eveonline.com/oauth/token/'

		body=urllib.parse.urlencode(payload)

		chunk = { 'kwargs':{'method':'POST' , 'body':body , 'headers':headers } , 'url':url }
		response = yield self.fe.asyncFetch(chunk)
		
		if response.code == 200:
			payload = json.loads(response.body.decode())
			result = yield self.db.pilots.update_one({'esi_api.refresh_token':oAuth['refresh_token']},{'$set':{'esi_api.access_token':payload['access_token']}},upsert=True)
			
			return payload['access_token']

		else :
			logger.warning( oAuth['CharacterName'] + ':' + str(response.code) +':' + str(response.body))
