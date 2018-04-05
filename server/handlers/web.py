import tornado.web
from tornado import gen 

import urllib.parse
import json
import uuid

from datetime import datetime
 
import server.modules
from server.utils.csv import json_serial

import logging
logger = logging.getLogger('web')

def urlHandler(url=None):

	if url :
		return urllib.parse.unquote(url).split('/')
	else :
		return ['home']

def inputHandler(inputs=None):

	return {k:v[0].decode() for k,v in inputs.items()}

class Session():

	def __init__(self, args={}):	
		for k , v in args.items():
			setattr(self,k,v)

class MainHandler(tornado.web.RequestHandler):

	sessions = {}

	def getRequestTime(self):
		return datetime.fromtimestamp(int(self.request._start_time)).strftime('%Y-%m-%d %H:%M:%S')

	def getRequest(self):

		return dict( (x,getattr(self.request,x)) for x in self.request.__dict__ )

	def getPath(self):
		
		return urlHandler(self.request.path[1:])

	def getInputs(self):
		
		return inputHandler(self.request.query_arguments)

	def getBody(self):
		
		return inputHandler(self.request.body_arguments)

	def getCookies(self):

		return {i:self.getCookie(i) for i in self.cookies}

	def getCookie(self,i='id'):

		cookie = self.get_secure_cookie(i)
		if cookie : cookie = cookie.decode('UTF-8')
		return cookie

	def setCookie(self,name=None,value=None):
		
		self.set_secure_cookie(name,value)
		return True

	def getSessions(self):
		
		return {k:v for k, v in self.session.__dict__.items()}

	def getSession(self,i='uuid'):
		return getattr(self.session,i,None)

	def getSessionId(self):

		_sessionId = self.getCookie('uuid')
		if _sessionId == None or not _sessionId in self.sessions: 
			_sessionId = str(uuid.uuid4())
			
			self.sessions[_sessionId] = Session({'uuid':_sessionId})
			self.setCookie('uuid',_sessionId)

		return _sessionId

	def setSession(self,name,value):
		setattr(self.sessions[self.getSessionId()],name,value)

	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	@gen.coroutine
	def get(self,args):

		module 	= str(self.getPath()[0])

		if module == 'ws': 
			self.finish()
			return

		self.session = self.sessions[self.getSessionId()]

		#if not module == 'sso' and self.getSession('id') == None: module = 'login'
		result = yield getattr(getattr(server.modules,module),'GET')(self,{'session':self.getSessions()})
		
		if result['mode'] == 'render' :			
			self.write(self.render_string(result['template'],data=result['data']))
			self.finish()	
		elif result['mode'] == 'redirect' :	
			self.redirect(result['url'])		
		elif result['mode'] == 'direct' :			
			self.write(result['data'])
			self.finish()	
		elif result['mode'] == 'json' :			
			self.write(json.dumps(result['data'], default=json_serial))
			self.finish()	
		else : 
			self.write(self.render_string('404.html'))
			self.finish()