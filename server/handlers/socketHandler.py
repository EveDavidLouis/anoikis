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

		_id = self.get_cookie('_id')
		_code = self.get_cookie('_code')
		
		logger.warning(_id)

		if _id : 
			self.refresh_token = _id #.decode('UTF-8')

			logger.info('LOGIN:'+ self.refresh_token)
			document = yield db.pilots.find_one({'refresh_token':self.refresh_token},{'CharacterName':1,'access_token':1}) 	
	
			if document and 'CharacterName' in document: 
				self.name = document['CharacterName']
				self.access_token = document['access_token']
			else:

				self.name = str(self.refresh_token)
		
			outbound = {'welcome': {'id':str(self.id),'name':self.name}}

		elif _code:
			_id = yield self.getSSO(_code)
			if _id != '':
				outbound={'setCookie':{'name':'_id','value':_id}}
			else:
				outbound={'eraseCookie':{'name':'_code'}}
		
		else :
			payload = {'sso': self.settings['co'].sso}
			if not 'state' in payload: payload['state'] = 'home'

			outbound = {'login': self.render_string('login.html',data=payload).decode("utf-8") }

		SocketHandler.waiters.add(self)
		
		self.write_message(json.dumps(outbound))

	@gen.coroutine
	def on_close(self):

		SocketHandler.waiters.remove(self)

	@gen.coroutine
	def on_message(self,inbound={}):

		inbound = json.loads(inbound)
		
		#logger.warning(inbound)

		outbound={}
		outbound['id'] = str(self.id)
		outbound['channel'] = str(self.channel)
		outbound['inbound'] = inbound

		if 'c' in inbound:
			self.name = inbound['a']
		elif 'a' in inbound:
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

	@gen.coroutine
	def getSSO(self,code=None):
		
		db = self.settings['db']
		fe = self.settings['fe']
		co = self.settings['co']

		headers = {}
		headers['Authorization'] = co.sso['authorization']
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
		headers['Host'] = 'login.eveonline.com'
		
		payload = {}
		payload['grant_type'] = 'authorization_code'
		payload['code'] = code

		url = 'https://login.eveonline.com/oauth/token/'

		body=urllib.parse.urlencode(payload)

		chunk = { 'kwargs':{'method':'POST' , 'body':body , 'headers':headers } , 'url':url }
		response = yield fe.asyncFetch(chunk)
		if response.code == 200:
			
			oAuth = json.loads(response.body.decode())

			url = 'https://login.eveonline.com/oauth/verify'

			headers['Authorization'] = 'Bearer ' + oAuth['access_token']
			headers['Host'] = 'login.eveonline.com'

			chunk = { 'kwargs':{'method':'GET', 'headers':headers } , 'url':url }
			response = yield fe.asyncFetch(chunk)
			if response.code == 200:

				oAuth.update(json.loads(response.body.decode()))
				result = yield db.pilots.update_one({'_id':oAuth['CharacterID']},{'$set':oAuth},upsert=True)

				return oAuth['refresh_token']


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