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
	def open(self,channel=''):
		
		db = self.settings['db']

		self.id = uuid.uuid4()

		SocketHandler.waiters.add(self)
		# self.callback = PeriodicCallback(lambda : self.cron(),10000)
		# self.callback.start()

		self.token = channel #self.get_cookie('_id')

		if self.token != '': 

			document = yield db.pilots.find_one({'esi_login.access_token':self.token},{'esi_login':1,'Characters':1}) 	
	
			if document and 'CharacterName' in document['esi_login']: 
				
				self.CharacterName = document['esi_login']['CharacterName']
				self.CharacterID = document['esi_login']['CharacterID']
				self.access_token = document['esi_login']['access_token']

				if not 'Characters' in document: document['Characters'] = []

				payload = {}
				payload['pilot'] = document['esi_login']
				payload['Characters'] = [{'CharacterID':i , 'CharacterName': document['Characters'][i]['CharacterName'] } for i in document['Characters'] ]
				payload['esi_api'] = self.settings['co'].esi_api
				payload['state'] = 'api'

				outbound = {'brand': self.render_string('brand.html',data=payload).decode("utf-8") 
					,'main': self.render_string('addCharacter.html',data=payload).decode("utf-8") 
					}

			else:

				payload = {'esi_login': self.settings['co'].esi_login}
				payload['state'] = 'ERROR'
				
				outbound = {'ERROR': 'token' }

		else :

			payload = {'esi_login': self.settings['co'].esi_login}
			if not 'state' in payload: payload['state'] = 'login'

			outbound = {'login': self.render_string('login.html',data=payload).decode("utf-8") }

		self.write_message(json.dumps(outbound))

	@gen.coroutine
	def on_close(self):

		SocketHandler.waiters.remove(self)

	@gen.coroutine
	def on_message(self,inbound={}):

		inbound = json.loads(inbound)
		
		db = self.settings['db']

		if 'code' in inbound and 'state' in inbound:

			result = yield self.getSSO(inbound['code'],inbound['state'])

			if inbound['state'] =='login':

				yield db.pilots.update_one({'_id':result['CharacterID']},{'$set':{'esi_login':result}},upsert=True)

				outbound={'setCookie':{'name':'_id','value':result['access_token']}}
				self.write_message(json.dumps(outbound))

			if inbound['state'] =='api':

				yield db.pilots.update_one({'esi_login.access_token':self.token},{'$set':{'Characters.'+str(result['CharacterID']):result}},upsert=True)

				outbound={'addCharacter':{'CharacterID':result['CharacterID'],'CharacterName':result['CharacterName']}}
				self.write_message(json.dumps(outbound))

			#if _id and _id != '':
			#	outbound={'setCookie':{'name':'_id','value':_id}}
			#	self.write_message(json.dumps(outbound))
			# else:
			# 	outbound={'eraseCookie':{'name':'_id'}}

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
	def getSSO(self,code=None,state=None):

		db = self.settings['db']
		fe = self.settings['fe']
		co = self.settings['co']

		headers = {}
		
		if state == 'api':
			headers['Authorization'] = co.esi_api['authorization']
		else:
			headers['Authorization'] = co.esi_login['authorization']

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
				return payload

				# logger.warning(state)
				# if state == 'api':
				# 	result = yield db.pilots.update_one({'_id':payload['CharacterID']},{'$set':{str(payload['CharacterID']):payload}},upsert=True)
				# 	return ''
				# else:
				# 	result = yield db.pilots.update_one({'_id':payload['CharacterID']},{'$set':{'esi_login':payload}},upsert=True)
				# 	return payload['access_token']

				