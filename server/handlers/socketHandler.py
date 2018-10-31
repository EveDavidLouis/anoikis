from tornado import websocket
from tornado.queues import Queue
from tornado import gen 
from tornado.ioloop import PeriodicCallback

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
	def cron(self):
		outbound = {'id':str(self.id),'ping':1}
		self.write_message(json.dumps(outbound))

	@gen.coroutine
	def open(self,channel='null'):
		
		db = self.settings['db']

		self.id = uuid.uuid4()

		SocketHandler.waiters.add(self)
		# self.callback = PeriodicCallback(lambda : self.cron(),10000)
		# self.callback.start()

		self.refresh_token = channel
		if self.refresh_token == 'null': self.refresh_token = None

		if self.refresh_token : 

			document = yield db.pilots.find_one({'oAuth.refresh_token':self.refresh_token},{'oAuth':1}) 	
	
			if document and 'CharacterName' in document['oAuth']: 
				
				self.CharacterName = document['oAuth']['CharacterName']
				self.CharacterID = document['oAuth']['CharacterID']
				self.access_token = document['oAuth']['access_token']
				
				payload = document['oAuth']

				outbound = {'welcome': {'CharacterName':self.CharacterName,'CharacterID':self.CharacterID}}
				outbound = {'welcome': self.render_string('welcome.html',data=payload).decode("utf-8") }

			else:

				payload = {'sso': self.settings['co'].sso}
				if not 'state' in payload: payload['state'] = 'home'
				
				outbound = {'login': self.render_string('login.html',data=payload).decode("utf-8") }

		else :

			payload = {'sso': self.settings['co'].sso}
			if not 'state' in payload: payload['state'] = 'home'

			outbound = {'login': self.render_string('login.html',data=payload).decode("utf-8") }

		self.write_message(json.dumps(outbound))

	@gen.coroutine
	def on_close(self):

		SocketHandler.waiters.remove(self)

	@gen.coroutine
	def on_message(self,inbound={}):

		inbound = json.loads(inbound)
		
		if 'code' in inbound:
			_id = yield self.getSSO(inbound['code'])
			if _id != '':
				outbound={'setCookie':{'name':'_id','value':_id}}
			# else:
			# 	outbound={'eraseCookie':{'name':'_id'}}

			self.write_message(json.dumps(outbound))

		# outbound={}
		# outbound['id'] = str(self.id)
		# outbound['channel'] = str(self.channel)
		# outbound['inbound'] = inbound

		# if 'c' in inbound:
		# 	self.name = inbound['a']
		# elif 'a' in inbound:
		# 	self.name = inbound['a']
		# elif 'w' in inbound:

		# 	headers = {}
		# 	body = ''

		# 	url = 'https://esi.evetech.net/latest/ui/autopilot/waypoint/'
		# 	url += '?add_to_beginning=' + str(True)
		# 	url += '&clear_other_waypoints=' + str(True)
		# 	url += '&destination_id=' + str(inbound['w']) #str(60009031)
		# 	url += '&token=' + str(self.access_token)
			
		# 	request = {'kwargs':{'method':'POST','body':body,'headers':headers} ,'url':url}
		# 	logger.warning(request)

		# 	response = yield self.settings['fe'].asyncFetch(request)

		# else:
		# 	outbound = [ {'id':str(w.id),'name':w.name} for w in self.waiters]
		# 	outbound = json.dumps(outbound)
		# 	self.broadcast(outbound)

	@gen.coroutine
	def broadcast(self,inbound={}):
		
		outbound = inbound

		for waiter in self.waiters:
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
			
			payload = json.loads(response.body.decode())

			url = 'https://login.eveonline.com/oauth/verify'

			headers['Authorization'] = 'Bearer ' + payload['access_token']
			headers['Host'] = 'login.eveonline.com'

			chunk = { 'kwargs':{'method':'GET', 'headers':headers } , 'url':url }
			response = yield fe.asyncFetch(chunk)
			if response.code == 200:

				payload.update(json.loads(response.body.decode()))
				result = yield db.pilots.update_one({'_id':payload['CharacterID']},{'$set':{'oAuth':payload}},upsert=True)

				return payload['refresh_token']