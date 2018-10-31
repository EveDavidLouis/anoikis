import datetime , json
from tornado import gen
from tornado.queues import Queue
import urllib

import logging
logging.basicConfig(level=logging.INFO)
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

		for i in self.ws.waiters:
			i.write_message({'clients':len(self.ws.waiters)})

		collection = self.db['pilots']
		cursor = collection.find({},{'oAuth':1})
		document = yield cursor.to_list(length=10000)
		for i in document:

			url = 'https://esi.evetech.net/latest/characters/' + str(i['_id']) + '/location/?token=' + i['oAuth']['access_token'] 
			chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			response = yield self.fe.asyncFetch(chunk)
			if response.code == 200:
				payload = json.loads(response.body.decode())
				#logger.info( i['oAuth']['CharacterName'] + ':' + str(payload) )
				result = yield self.db.pilots.update_one({'_id':i['_id']},{'$set':{'SSOlocation':payload}},upsert=True)
			else:
				self.refreshSSO(oAuth=i['oAuth'])

	@gen.coroutine
	def refreshSSO(self,oAuth=None):
		
		headers = {}
		headers['Authorization'] = self.co.sso['authorization']
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
			#logger.info( oAuth['CharacterName'] + ':' + payload['access_token'])
			result = yield self.db.pilots.update_one({'oAuth.refresh_token':oAuth['refresh_token']},{'$set':{'oAuth.access_token':payload['access_token']}},upsert=True)
			return payload['access_token']

		else :
			logger.warning( oAuth['CharacterName'] + ':' + str(response.code) +':' + str(response.body))
