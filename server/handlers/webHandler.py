from tornado import gen , web
import json , urllib

from server import esi , tripwire

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('webHandler')

def inputHandler(inputs=None):

	return {k:v[0].decode() for k,v in inputs.items()}

class LoginHandler(web.RequestHandler):
	@gen.coroutine
	def get(self):
		
		payload = {'sso': self.settings['co'].sso}
		if not 'state' in payload: payload['state'] = 'home'
		
		self.write(self.render_string('login.html',data=payload))
		self.finish()

class LogoutHandler(web.RequestHandler):
	@gen.coroutine
	def get(self):	
		self.clear_all_cookies()
		return self.redirect('/')

class TripwireHandler(web.RequestHandler):
	@gen.coroutine
	def get(self):	

		for i in self.settings['co'].tripwire:
			char = tripwire.Tripwire(tripwireUsername=i['tripwireUsername'],tripwirePassword=i['tripwirePassword'],maskList=i['maskList'])
			yield char.login()
			result = yield char.getAll()
			
			payload = set()
			for mask in result:
				for sig in result[mask]:
					payload.add(result[mask][sig]['systemID'])
					#set.add(result[mask][sig]['systemID'])

			self.write(json.dumps(list(payload)))

		self.finish()

class SsoHandler(web.RequestHandler):
	@gen.coroutine
	def get(self):

		inputs = inputHandler(self.request.query_arguments)
		
		db = self.settings['db']
		fe = self.settings['fe']
		co = self.settings['co']

		headers = {}
		headers['Authorization'] = co.sso['authorization']
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
		headers['Host'] = 'login.eveonline.com'
		
		payload = {}
		payload['grant_type'] = 'authorization_code'
		payload['code'] = inputs['code']

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
				
				self.set_secure_cookie('_id',oAuth['refresh_token'])
				result = yield db.pilots.update_one({'_id':oAuth['CharacterID']},{'$set':oAuth},upsert=True)
				return self.redirect('/' + inputs['state'])

			else:
				self.redirect('/login')
		else :
			self.redirect('/login')

class MainHandler(web.RequestHandler):
	@gen.coroutine
	def get(self,args):

		_id = self.get_secure_cookie('_id')
		_db = self.settings['db']

		if _id : 
		
			self.name = _id.decode('UTF-8')
			document = yield _db.pilots.find_one({'refresh_token':self.name},{'CharacterID':1,'CharacterName':1}) 	
	
			if document and 'CharacterName' in document: 
				
				self.write(self.render_string('main.html',data=document))
				self.finish()

			else:
				
				self.redirect('/login')
		
		else:
		
			self.redirect('/login')

class MarketHandler(web.RequestHandler):
	@gen.coroutine
	def get(self,args):
		
		if not args: args = 44992

		response = yield esi.getMarket(typeId=args)
		
		self.write(self.render_string('market.html',data=response))
		self.finish()

class TestMongo(web.RequestHandler):
	@gen.coroutine
	def get(self,args):

		collection = self.settings['db']['systems']
		document = yield collection.find_one({})

		payload = {}
		payload['document'] = document

		self.write(payload)
		self.finish()	

class TestFetch(web.RequestHandler):
	@gen.coroutine
	def get(self,args):
		region_id = 10000002
		typeId = 33472
		fetcher = self.settings['fe']
		request = {'kwargs':{},'url':'https://esi.evetech.net/latest/markets/'+str(region_id)+'/orders/?order_type=sell&type_id='+str(typeId)}
		response = yield fetcher.asyncFetch(request)
		if response.code == 200:
				response = json.loads(response.body)
				for i in response:
					self.write(str(i))
					self.write('<br>')
		else:
			self.write('oups')
		self.finish()