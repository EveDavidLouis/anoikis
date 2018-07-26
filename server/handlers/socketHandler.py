from tornado import websocket
from tornado.queues import Queue
from tornado import gen 

import uuid, json , urllib
import base64

import logging
logger = logging.getLogger('socket')

class SocketHandler(websocket.WebSocketHandler):
	
	waiters = set()
	cache = []
	cache_size = 200

	@gen.coroutine
	def check_origin(self, origin):
		return True

	@gen.coroutine
	def open(self,channel=None):
		
		db = self.settings['db']

		self.id = uuid.uuid4()
		self.channel = str(channel)

		cookie = self.get_secure_cookie('_id')
	
		if cookie : 
			self.refresh_token = cookie.decode('UTF-8')
			document = yield db.pilots.find_one({'refresh_token':self.refresh_token},{'CharacterName':1,'access_token':1}) 	
	
			if document and 'CharacterName' in document: 
				self.name = document['CharacterName']
				self.access_token = document['access_token']
			else:
				self.name = str(self.token)
		else : 
			self.name = str(self.id)

		logger.info('LOGIN:'+ self.name)
		
		SocketHandler.waiters.add(self)

		outbound = {'inbound':[ {'id':str(w.id),'name':w.name} for w in self.waiters]}
		outbound = json.dumps(outbound)
		
		for waiter in self.waiters:
			waiter.write_message(outbound)

	@gen.coroutine
	def on_close(self):
		logger.info('LOGIN:'+self.name)
		SocketHandler.waiters.remove(self)

		outbound = {'inbound':[ {'id':str(w.id),'name':w.name} for w in self.waiters]}
		outbound = json.dumps(outbound)
		
		for waiter in self.waiters:
			waiter.write_message(outbound)

	@gen.coroutine
	def on_message(self,inbound={}):

		inbound = json.loads(inbound)
		
		#logger.warning(inbound)

		outbound={}
		outbound['id'] = str(self.id)
		outbound['name'] = str(self.name)
		outbound['channel'] = str(self.channel)
		outbound['inbound'] = inbound

		if 'a' in inbound:
			self.name = inbound['a']
		elif 'w' in inbound:

			headers = {}
			body = ''

			url = 'https://esi.evetech.net/latest/ui/autopilot/waypoint/'
			url += '?add_to_beginning=' + str(True)
			url += '&clear_other_waypoints=' + str(True)
			url += '&destination_id=' + str(inbound['w']) #str(60009031)
			url += '&token=' + str(self.access_token)
			
			request = {'kwargs':{'method':'POST','body':body,'headers':headers} ,'url':url}
			logger.warning(request)

			response = yield self.settings['fe'].asyncFetch(request)

		else:
			outbound = [ {'id':str(w.id),'name':w.name} for w in self.waiters]
			outbound = json.dumps(outbound)
			self.broadcast(outbound)

	@gen.coroutine
	def broadcast(self,inbound={}):
		
		outbound = inbound

		for waiter in self.waiters:
			logger.info(waiter.name + ':' + waiter.channel)
			if not waiter.id == self.id:
				try:
					waiter.write_message(outbound)
				except:
					logging.error("Error sending message")

class SocketWorker():

	def __init__(self, url='ws://0.0.0.0:8081/ws'):
		self.socketServer = url
		self.q = Queue(maxsize=256)

	@gen.coroutine
	def run(self):
		
		self.client = yield websocket.websocket_connect(self.socketServer)
		a = {'a':'SERVER'}
		self.client.write_message(json.dumps(a))

		while True:
			item = yield self.q.get()
			try:
				logger.info('working on ' + str(item))
				#self.client.write_message(json.dumps(item))
			except:
				self.client.write_message(str(item))
			finally:
				self.q.task_done()

	@gen.coroutine
	def send(self,message=None):
		self.q.put(message)