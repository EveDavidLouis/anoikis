from tornado import gen 
from server.utils.fetch import AsyncClient

import json
import urllib.parse
from http import cookies

class Tripwire:

	urlSignatures = 'https://tripwire.eve-apps.com/refresh.php'
	urlOptions = 'https://tripwire.eve-apps.com/options.php'
	urlLogin = 'https://tripwire.eve-apps.com/login.php'

	def __init__(self,tripwireUsername=None,tripwirePassword=None,maskList={}):
		self.maskList = maskList
		self.tripwireUsername = tripwireUsername
		self.tripwirePassword = tripwirePassword

		self.tripwireOptions = {}

		self.session = AsyncClient()
		self.cookies = {}

	def setCookies(self,header=None):
		http_cookie = cookies.SimpleCookie()
		http_cookie.load(header)
		for i in http_cookie:
			self.cookies[i] = http_cookie[i].value

	def getCookies(self,header=None):
		return urllib.parse.urlencode(self.cookies).replace('&',';')

	@gen.coroutine
	def login(self):

		headers = {}
		body = urllib.parse.urlencode({'mode':'login','username': self.tripwireUsername, 'password': self.tripwirePassword})
		request = { 'kwargs':{'method':'POST','headers':headers,'body':body} , 'url':self.urlLogin}
		response = yield self.session.asyncFetch(request)
		
		self.setCookies(response.headers['set-cookie'])

	@gen.coroutine
	def getOptions(self):

		headers = {}
		headers['cookie'] = self.getCookies()
		request = { 'kwargs':{'method':'GET','headers':headers} , 'url':self.urlOptions+'?mode=get'}
		response = yield self.session.asyncFetch(request)
		
		result = response.body.decode()

		if result == '':
			yield self.login()
			headers = {}
			headers['cookie'] = self.getCookies()
			request = { 'kwargs':{'method':'GET','headers':headers} , 'url':self.urlOptions+'?mode=get'}
			response = yield self.session.asyncFetch(request)
			result = response.body.decode()		
			return json.loads(result)['options']
		else:
			return json.loads(result)['options']

	@gen.coroutine
	def getActiveChain(self):
		
		body = {'mode':'init','systemID':'30000142','systemName':'Jita'}
		body = urllib.parse.urlencode(body)

		headers = {}
		headers['cookie'] = self.getCookies()

		request = { 'kwargs':{'method':'POST','headers':headers , 'body':body} , 'url':self.urlSignatures}
		response = yield self.session.asyncFetch(request)
		result = response.body.decode()		

		return json.loads(result)['chain']['map']

	@gen.coroutine
	def setActiveMask(self,mask):

		self.tripwireOptions['masks']['active'] = mask
			
		body = {'mode':'set','options':json.dumps(self.tripwireOptions)}
		body = urllib.parse.urlencode(body)
		
		headers = {}
		headers['cookie'] = self.getCookies()

		request = { 'kwargs':{'method':'POST','headers':headers , 'body':body} , 'url':self.urlOptions}
		response = yield self.session.asyncFetch(request)
		result = response.body.decode()		

	@gen.coroutine
	def getAll(self):

		payload = {}

		self.tripwireOptions = yield self.getOptions()
		initialMask = self.tripwireOptions['masks']['active']

		for mask in self.maskList:
		 	if mask != initialMask:
		 		yield self.setActiveMask(mask)
		 		payload[mask] = yield self.getActiveChain()

		self.setActiveMask(initialMask)
		payload[initialMask] = yield self.getActiveChain()

		return payload