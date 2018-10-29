import datetime , json
from tornado import gen
from tornado.queues import Queue

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
	
	def __init__(self,db=None,fe=None,ws=None):
		
		self.ws = ws
		self.fe = fe
		self.db = db
	
	@gen.coroutine
	def run(self):

		# url = "https://esi.evetech.net/latest/characters/95765286/"
		# chunk = { 'kwargs':{'method':'GET'} , 'url':url }
		# response = yield self.fe.asyncFetch(chunk)		
		# if response.code == 200:
		# 	payload = json.loads(response.body.decode())
		# 	logger.info(payload)

		# for i in self.ws.waiters:
		# 	outbound = {'clients':len(self.ws.waiters)}
		# 	i.write_message(json.dumps(outbound))

		collection = self.db['pilots']
		cursor = collection.find({},{'CharacterID':1,'CharacterName':1,'access_token':1})
		document = yield cursor.to_list(length=10000)
		for i in document:
			url = 'https://esi.evetech.net/latest/characters/' + str(i['_id']) + '/location/?token=' + i['access_token'] 
			chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			response = yield self.fe.asyncFetch(chunk)
			if response.code == 200:
				payload = json.loads(response.body.decode())
				logger.info(i['CharacterName'] + ':' + str(payload))
				result = yield self.db.pilots.update_one({'_id':i['_id']},{'$set':payload},upsert=True)
			else:
				logger.warning(json.loads(response.body.decode()))
