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
		outbound = {'ping':1}
		self.write_message(json.dumps(outbound))

	@gen.coroutine
	def open(self,channel=''):
		
		db = self.settings['db']

		self.id = uuid.uuid4()

		SocketHandler.waiters.add(self)

		#ping
		self.callback = PeriodicCallback(lambda : self.cron(),30*1000)
		self.callback.start()

		self.token = channel

		if self.token != '': 

			result = yield db['pilots'].find_one({'esi_login.access_token':self.token},{'group':1,'esi_login.CharacterName':1,'esi_login.CharacterID':1,'esi_login.access_token':1}) 	

			if result and 'CharacterName' in result['esi_login']: 
				
				self.CharacterName = result['esi_login']['CharacterName']
				self.CharacterID = result['esi_login']['CharacterID']
				self.access_token = result['esi_login']['access_token']
				if 'group' in result:
					self.group = result['group']
				else: 
					self.group = 'guest'
				
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

		self.callback.stop()
		SocketHandler.waiters.remove(self)

	@gen.coroutine
	def on_message(self,inbound={}):

		inbound = json.loads(inbound)
		
		db = self.settings['db']
		qe = self.settings['qe']

		if 'code' in inbound and 'state' in inbound:

			result = yield self.getSSO(inbound['code'],inbound['state'])

			if inbound['state'] =='login':

				yield db.pilots.update_one({'_id':result['CharacterID']},{'$set':{'esi_login':result}},upsert=True)

				outbound={'endPoint':'esi-login','data':{'name':'_id','value':result['access_token']}}
				self.write_message(json.dumps(outbound))

			if inbound['state'] =='api':

				yield db.pilots.update_one({'_id':result['CharacterID']},{'$set':{'esi_api':result,'owner':self.CharacterID}},upsert=True)
				
				cursor = db['pilots'].find({'_id':result['CharacterID'],'esi_api':{'$exists':1} },{'esi_api':1,'public':1})
				documentList = yield cursor.to_list(length=1000)
		
				for document in documentList:
					yield qe.refreshCharacter(document)

				outbound={'endPoint':'esi-api','data':{'CharacterID':result['CharacterID'],'CharacterName':result['CharacterName']}}
				self.write_message(json.dumps(outbound))

		elif 'getCharacter' in inbound:

			if self.group == 'admin':
				query = {'esi_api.CharacterID':inbound['getCharacter']}
			else :
				query = {'esi_api.CharacterID':inbound['getCharacter'],'owner':self.CharacterID}
			
			esi_api = yield db['pilots'].find_one(query,{'_id':0,'esi_api.CharacterName':1,'esi_api.CharacterID':1,'corporationhistory':1,'stats':1,'standings':1,'wallet-journal':1,'wallet-transactions':1,'owner':1,'location':1,'bookmarks':1,'bookmarks-folders':1}) 	
			
			if esi_api:
				outbound = {'endPoint':'character', 'data':esi_api}
			else :
				outbound = {'error':' getCharacter forbidden'}

			self.write_message(json.dumps(outbound))

		elif 'getCharacters' in inbound:

			payload = {}
			
			esi_api = self.settings['co'].esi_api
			#payload['addCharacter'] = self.render_string('addCharacter.html',data=payload_link).decode("utf-8") 
			payload['url'] = 'https://login.eveonline.com/oauth/authorize/?response_type=code&redirect_uri=%s&scope=%s&client_id=%s&state=api' % (esi_api['callback'] ,esi_api['scope'],esi_api['clientId'])

			payload['list'] = []

			if inbound['getCharacters'] == 'members' :
				query = {'owner':self.CharacterID} #need to control if admin
				
			else :
				query = {'owner':self.CharacterID}

				if self.group == 'admin':
					query = {'esi_api':{'$exists':1}}
	
			cursor = db['pilots'].find(query,{'_id':0,'esi_api.CharacterID':1,'esi_api.CharacterName':1})
			charList = yield cursor.to_list(length=10000)
			if charList:
				for char in charList:
					payload['list'].append(char['esi_api'])

			outbound = {'endPoint':'characters', 'data':payload}

			self.write_message(json.dumps(outbound))

		else:
			self.write_message(json.dumps(inbound))

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