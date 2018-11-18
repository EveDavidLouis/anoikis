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

		self.token = channel

		if self.token != '': 

			esi_login = yield db['pilots'].find_one({'access_token':self.token},{'CharacterName':1,'CharacterID':1,'access_token':1}) 	
	
			if esi_login and 'CharacterName' in esi_login: 
				
				self.CharacterName = esi_login['CharacterName']
				self.CharacterID = esi_login['CharacterID']
				self.access_token = esi_login['access_token']

				payload = {}
				payload['CharacterName'] = self.CharacterName
				payload['CharacterID'] = self.CharacterID
				payload['Characters'] = []

				cursor = db['pilots'].find({'owner':self.CharacterID},{'esi_api.CharacterID':1,'esi_api.CharacterName':1})
				charList = yield cursor.to_list(length=10000)
				if charList:
					for char in charList:
						payload['Characters'].append(char)

				outbound = {'endPoint':'home','data':payload}

			else:

				outbound = {'endPoint':'error','data':'pilot not found!'}

		else :

			payload = {'esi_login': self.settings['co'].esi_login ,'state':'login'}
			outbound = {'endPoint':'welcome','data':self.render_string('login.html',data=payload).decode("utf-8") }

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

				yield db.pilots.update_one({'_id':result['CharacterID']},{'$set':result},upsert=True)

				outbound={'endPoint':'esi-login','data':{'name':'_id','value':result['access_token']}}
				self.write_message(json.dumps(outbound))

			if inbound['state'] =='api':

				yield db.pilots.update_one({'_id':result['CharacterID']},{'$set':{'esi_api':result,'owner':self.CharacterID}},upsert=True)
				
				outbound={'endPoint':'esi-api','data':{'CharacterID':result['CharacterID'],'CharacterName':result['CharacterName']}}
				self.write_message(json.dumps(outbound))

		elif 'getCharacter' in inbound:

			esi_api = yield db['pilots'].find_one({'esi_api.CharacterID':inbound['getCharacter'],'$or':[{'admin':1},{'owner':self.CharacterID}]},{'_id':0,'esi_api.CharacterName':1,'esi_api.CharacterID':1,'location':1}) 	
			
			if esi_api:
				outbound = {'endPoint':'character', 'data':esi_api}
			else :
				outbound = {'endPoint':'error', 'data':'forbidden'}
			self.write_message(json.dumps(outbound))

		elif 'getCharacters' in inbound:

			payload = {}
			
			payload_link = {'esi_api': self.settings['co'].esi_api,'state':'api'}
			payload['addCharacter'] = self.render_string('addCharacter.html',data=payload_link).decode("utf-8") 

			payload['characters'] = []

			cursor = db['pilots'].find({'owner':self.CharacterID},{'_id':0,'esi_api.CharacterID':1,'esi_api.CharacterName':1})
			charList = yield cursor.to_list(length=10000)
			if charList:
				for char in charList:
					payload['characters'].append(char['esi_api'])

			outbound = {'endPoint':'characters', 'data':payload}

			self.write_message(json.dumps(outbound))

		else:
			self.write_message(json.dumps(inbound))

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