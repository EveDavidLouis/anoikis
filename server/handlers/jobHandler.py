import datetime , json
from tornado import gen
from tornado.queues import Queue
import urllib

import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('cron')

class QueueWorker():

	def __init__(self,db=None,fe=None,ws=None,co=None):
		self.q = Queue(maxsize=256)
		self.db = db
		self.fe = fe
		self.co = co

	@gen.coroutine
	def run(self):

		while True:
			item = yield self.q.get()
			try:
				responses = yield self.fe.asyncMultiFetch(item)
				requests = []
				for response in responses:
					if response.code == 200:
						logger.info(response.body)

					else:
						if 'Refresh_token' in response.request.headers:
							logger.info('refreshing token')
							
							headers = {}
							headers['Authorization'] = self.co.esi_api['authorization']
							headers['Content-Type'] = 'application/x-www-form-urlencoded'
							headers['Host'] = 'login.eveonline.com'
							
							payload = {}
							payload['grant_type'] = 'refresh_token'
							payload['refresh_token'] = response.request.headers['Refresh_token']

							url = 'https://login.eveonline.com/oauth/token/'

							body=urllib.parse.urlencode(payload)

							request = [{ 'kwargs':{'method':'POST' , 'body':body , 'headers':headers } , 'url':url }]
							self.add(request)
						else :
							logger.warning('ERROR')
			except NameError:
				logger.warning(NameError)
			finally:
				self.q.task_done()

	@gen.coroutine
	def add(self,message=None):
		self.q.put(message)

	@gen.coroutine
	def refreshCharacter(self,char=None):

		headers = {}
		headers['Authorization'] = self.co.esi_api['authorization']
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
		headers['Host'] = 'login.eveonline.com'
		
		payload = {}
		payload['grant_type'] = 'refresh_token'
		payload['refresh_token'] = char['esi_api']['refresh_token']

		url = 'https://login.eveonline.com/oauth/token/'

		body=urllib.parse.urlencode(payload)

		request = { 'kwargs':{'method':'POST' , 'body':body , 'headers':headers } , 'url':url }
		response = yield self.fe.asyncFetch(request)

		if response.code == 200:

				char['esi_api'].update(json.loads(response.body.decode()))

				result = {'esi_api':char['esi_api']}

				requests=[]
				
				headers = {'folder':'location'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/location/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'public'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'corporationhistory'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/corporationhistory/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)
				
				headers = {'folder':'bookmarks'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/bookmarks/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'bookmarks-folders'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/bookmarks/folders/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'wallet-journal'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/wallet/journal/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'wallet-transactions'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/wallet/transactions/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'standings'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/standings/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'stats'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/stats/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				headers = {'folder':'industry-jobs'}
				url = 'https://esi.evetech.net/latest/characters/' + str(char['esi_api']['CharacterID']) + '/industry/jobs/?token=' + char['esi_api']['access_token']
				chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
				requests.append(chunk)

				if 'public' in char:
					headers = {'folder':'corporation-contracts'}
					url = 'https://esi.evetech.net/latest/corporations/' + str(char['public']['corporation_id']) + '/contracts/?token=' + char['esi_api']['access_token']
					chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
					requests.append(chunk)

				responses = yield self.fe.asyncMultiFetch(requests)
				
				for response in responses:
					if response.code == 200:

						if response.request.headers['folder'] == 'corporation-contracts':
							contracts = json.loads(response.body.decode())
							for i in contracts:
								i.update({'_id':i['contract_id']})
								self.db.contracts.update_one({'_id':i['contract_id']},{'$set':i},upsert=True)

						else:
							result[response.request.headers['folder']] = json.loads(response.body.decode())
						#if response.request.headers['folder'] == 'location':
						#	logger.warning(json.loads(response.body.decode()))
					elif response.code == 503:
						return None
					else:
						logger.warning(str(char['esi_api']['CharacterID']) + '->' + str(response.code) + ':' + response.body.decode())

				yield self.db.pilots.update_one({'esi_api.CharacterID':char['esi_api']['CharacterID']},{'$set':result})

		
		else:
			
			logger.warning(response.body)

		# esi_api = yield db['pilots'].find_one({'esi_api.CharacterID':CharacterID},{'_id':0,'esi_api.CharacterName':1,'esi_api.Refresh_token':1})	
		
		# if esi_api:
		# 	pass


class CronWorker(object):
	
	def __init__(self,db=None,fe=None,ws=None,co=None,qe=None):
		
		self.ws = ws
		self.fe = fe
		self.db = db
		self.co = co
		self.qe = qe
	
	@gen.coroutine
	def refresh_api(self):

		cursor = self.db['pilots'].find({'esi_api':{'$exists':1}},{'esi_api':1,'public':1})
		documentList = yield cursor.to_list(length=10000)
		
		for document in documentList:
			logger.warning('refresh_api')
			yield self.qe.refreshCharacter(document)

	@gen.coroutine
	def run(self):

		# for i in self.ws.waiters:
		# 	i.write_message({'clients':len(self.ws.waiters)})

		cursor = self.db['pilots'].find({'esi_api':{'$exists':1},'esi_api.error':{'$exists':0}},{'esi_api.CharacterID':1,'esi_api.access_token':1,'esi_api.refresh_token':1})
		documentList = yield cursor.to_list(length=10000)
		
		for document in documentList:
				
			esi_api = document['esi_api']
			payload = {}

			#--------------------------------------------------
			url = 'https://esi.evetech.net/latest/characters/' + str(esi_api['CharacterID']) + '/location/?token=' + esi_api['access_token']
			chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			folder = 'location'

			response = yield self.fe.asyncFetch(chunk)
			if response.code == 200:
				logger.info(folder +'OK')
				payload[folder]=json.loads(response.body.decode())
				result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':payload})

			else:
				error = json.loads(response.body.decode())
				logger.warning(error)
				if 'sso_status' in error and error['sso_status']==401:
					logger.warning('REFRESH TOKEN')
					self.refreshSSO(esi_api)
				else:
					logger.warning(folder +'ERROR')
					logger.warning(json.loads(response.body.decode()))
					#result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':{'esi_api.error':{'code':response.code,'data':json.loads(response.body.decode())}}})
			

			#--------------------------------------------------
			url = 'https://esi.evetech.net/latest/characters/' + str(esi_api['CharacterID']) + '/bookmarks/?token=' + esi_api['access_token']
			chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			folder = 'bookmarks'
			
			response = yield self.fe.asyncFetch(chunk)
			if response.code == 200:
				logger.info(folder +'OK')
				payload[folder]=json.loads(response.body.decode())
				result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':payload})

			else:
				error = json.loads(response.body.decode())
				logger.warning(error)
				if 'sso_status' in error and error['sso_status']==401:
					logger.warning('REFRESH TOKEN')
					self.refreshSSO(esi_api)
				else:
					logger.warning(folder +'ERROR')
					logger.warning(json.loads(response.body.decode()))
					#result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':{'esi_api.error':{'code':response.code,'data':json.loads(response.body.decode())}}})


			#--------------------------------------------------
			url = 'https://esi.evetech.net/latest/characters/' + str(esi_api['CharacterID']) + '/bookmarks/folders/?token=' + esi_api['access_token']
			chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			folder = 'bookmarks_folders'
			
			response = yield self.fe.asyncFetch(chunk)
			if response.code == 200:
				logger.info(folder +'OK')
				payload[folder]=json.loads(response.body.decode())
				result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':payload})

			else:
				error = json.loads(response.body.decode())
				logger.warning(error)
				if 'sso_status' in error and error['sso_status']==401:
					logger.warning('REFRESH TOKEN')
					self.refreshSSO(esi_api)
				else:
					logger.warning(folder +'ERROR')
					logger.warning(json.loads(response.body.decode()))
					#result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':{'esi_api.error':{'code':response.code,'data':json.loads(response.body.decode())}}})
					

			#--------------------------------------------------
			url = 'https://esi.evetech.net/latest/characters/' + str(esi_api['CharacterID']) + '/wallet/journal/?token=' + esi_api['access_token']
			chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			folder = 'wallet_journal'
			
			response = yield self.fe.asyncFetch(chunk)
			if response.code == 200:
				logger.info(folder +'OK')
				payload[folder]=json.loads(response.body.decode())
				result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':payload})

			else:
				error = json.loads(response.body.decode())
				logger.warning(error)
				if 'sso_status' in error and error['sso_status']==401:
					logger.warning('REFRESH TOKEN')
					self.refreshSSO(esi_api)
				else:
					logger.warning(folder +'ERROR')
					logger.warning(json.loads(response.body.decode()))
					#result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':{'esi_api.error':{'code':response.code,'data':json.loads(response.body.decode())}}})




				# logger.warning('refresh_token:' + str(esi_api['CharacterID']))
				# self.refreshSSO(esi_api)

			# url = 'https://esi.evetech.net/latest/characters/' + str(esi_api['CharacterID']) + '/ship/?token=' + esi_api['access_token']
			# chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			
			# response = yield self.fe.asyncFetch(chunk)
			# if response.code == 200:
			# 	payload.update(json.loads(response.body.decode()))
			# else:
			# 	logger.warning(response.code)
			# 	logger.warning(response.body)
			# 	# logger.warning('refresh_token:' + str(esi_api['CharacterID']))
			# 	# self.refreshSSO(esi_api)

			# url = 'https://esi.evetech.net/latest/characters/' + str(esi_api['CharacterID']) + '/standings/?token=' + esi_api['access_token']
			# chunk = { 'kwargs':{'method':'GET'} , 'url':url }
			
			# response = yield self.fe.asyncFetch(chunk)
			# if response.code == 200:
			# 	payload['standings']=json.loads(response.body.decode())
			# else:

			# 	logger.warning(response.code)
			# 	logger.warning(response.body)
			# 	result = yield self.db.pilots.update_one({'esi_api.CharacterID':esi_api['CharacterID']},{'$set':{'esi_api.error':{'code':response.code,'data':json.loads(response.body.decode())}}})

	@gen.coroutine
	def refreshSSO(self,oAuth=None):
		
		headers = {}
		headers['Authorization'] = self.co.esi_api['authorization']
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
		headers['Host'] = 'login.eveonline.com'
		
		payload = {}
		payload['grant_type'] = 'refresh_token'
		payload['refresh_token'] = oAuth['refresh_token']

		url = 'https://login.eveonline.com/oauth/token/'

		body=urllib.parse.urlencode(payload)

		chunk = { 'kwargs':{'method':'POST' , 'body':body , 'headers':headers } , 'url':url }
		response = yield self.fe.asyncFetch(chunk)
		
		if response.code == 200:
			payload = json.loads(response.body.decode())
			result = yield self.db.pilots.update_one({'esi_api.refresh_token':oAuth['refresh_token']},{'$set':{'esi_api.access_token':payload['access_token']}},upsert=True)
			
			return payload['access_token']

		else :
			logger.warning( str(response.code) +':' + str(response.body))
