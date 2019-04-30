import datetime , json
from tornado import gen
from tornado.queues import Queue
import urllib

import logging
logging.basicConfig(level=logging.INFO)
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
					headers = {'folder':'corporation-contracts','corporation_id':str(char['public']['corporation_id']),'token':char['esi_api']['access_token']}
					url = 'https://esi.evetech.net/latest/corporations/' + str(char['public']['corporation_id']) + '/contracts/?token=' + char['esi_api']['access_token']
					chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
					requests.append(chunk)

				responses = yield self.fe.asyncMultiFetch(requests)
				
				for response in responses:
					if response.code == 200:

						if response.request.headers['folder'] == 'corporation-contracts':
							contracts = json.loads(response.body.decode())
							for i in contracts:
								if i['status'] != 'deleted' :
									i.update({'_id':i['contract_id'],'token':response.request.headers['token'],'corporation_id':response.request.headers['corporation_id']})
									self.db.contracts.update_one({'_id':i['contract_id']},{'$set':i},upsert=True)

						else:
							result[response.request.headers['folder']] = json.loads(response.body.decode())
						
						#if response.request.headers['folder'] == 'location':logger.warning(json.loads(response.body.decode()))
					
					elif response.code == 503:
						return None
					else:
						logger.warning(str(char['esi_api']['CharacterID']) + '->' + str(response.code) + ':' + response.body.decode())

				yield self.db.pilots.update_one({'esi_api.CharacterID':char['esi_api']['CharacterID']},{'$set':result})

		
		else:
			
			logger.warning(response.body)

	@gen.coroutine
	def refreshContract(self,contract=None):

		requests=[]

		if 'token' in contract :			
			headers = {'contract_id':str(contract['contract_id'])}
			url = 'https://esi.evetech.net/latest/corporations/' + str(contract['corporation_id']) +'/contracts/'+str(contract['_id'])+'/items/?token=' + str(contract['token'])
			chunk = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
			requests.append(chunk)
		else:
			logger.warning('QueueWorker.refreshContract:no token')

		responses = yield self.fe.asyncMultiFetch(requests)
				
		for response in responses:
			if response.code == 200:
				i = json.loads(response.body.decode())
				self.db.contracts.update_one({'_id':int(response.request.headers['contract_id'])},{'$set':{'items':i}},upsert=True)

			else:
				logger.info(response.request.headers['contract_id'] + '->' + str(response.code) + ':' + response.body.decode())


class CronWorker(object):
	
	def __init__(self,db=None,fe=None,ws=None,co=None,qe=None):
		
		self.ws = ws
		self.fe = fe
		self.db = db
		self.co = co
		self.qe = qe

	@gen.coroutine
	def refreshSSO(self,oAuth=None):
		
		logger.info('CronWorker.refreshSSO')

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

	@gen.coroutine
	def refresh_api(self):

		logger.info('CronWorker.refresh_api')

		cursor = self.db['pilots'].find({'esi_api':{'$exists':1}},{'esi_api':1,'public':1})
		documentList = yield cursor.to_list(length=1000)
		
		for document in documentList:
			#logger.warning('refresh_api:' + str(document['esi_api']['CharacterID']))
			yield self.qe.refreshCharacter(document)


	@gen.coroutine
	def refresh_contracts(self):

		logger.info('CronWorker.refresh_contracts')

		cursor = self.db['contracts'].find({'items':{'$exists':0}})
		documentList = yield cursor.to_list(length=1000)
		
		for document in documentList:
			yield self.qe.refreshContract(document)


	@gen.coroutine
	def refresh_fleetup(self):

		logger.info('CronWorker.refresh_fleetup')

		AppKey = 'antVcAvocC7H2fhkHhrdbHQ8N'
		ApiCode = 'Wg6sDOS4xUo0UogPyFDn0PjR29JhbZ'
		Group = '76950'

		headers = {}
		url='http://api.fleet-up.com/Api.svc/'+AppKey+'/'+Group+'/'+ApiCode+'/Doctrines/42272'
		request = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }

		response = yield self.fe.asyncFetch(request)

		if response.code == 200:
			doctrines = json.loads(response.body.decode())
			if 'Data' in doctrines:	
				for doctrine in doctrines['Data']:
					
					headers2 = {}
					url2 = 'http://api.fleet-up.com/Api.svc/'+AppKey+'/'+Group+'/'+ApiCode+'/DoctrineFittings/'+str(doctrine['DoctrineId'])+'/true'
					request2 = { 'kwargs':{'method':'GET','headers':headers2} , 'url':url2 }

					response2 = yield self.fe.asyncFetch(request2)
					if response2.code == 200:
						
						fittings = json.loads(response2.body.decode())['Data']

						for fitting in fittings:
							
							fitting={'_id':int(fitting['FittingId']),'FittingId':fitting['FittingId'],'Name':fitting['Name'],'DoctrineId':int(doctrine['DoctrineId']),'DoctrineName':doctrine['Name'],'FolderName':doctrine['FolderName'],'FittingData':fitting['FittingData']}

							headers3 = {}
							url3 = 'http://api.fleet-up.com/Api.svc/'+AppKey+'/'+Group+'/'+ApiCode+'/Fitting/'+str(fitting['_id'])+'/eft'
							request3 = { 'kwargs':{'method':'GET','headers':headers3} , 'url':url3 }

							response3 = yield self.fe.asyncFetch(request3)
							if response3.code == 200:
								fitting['ApiCode'] = ApiCode
								fitting['EFT'] = json.loads(response3.body.decode())['Data']['FittingData']

							self.db.fittings.update_one({'_id':fitting['_id']},{'$set':fitting},upsert=True)
					else:
						logger.info('refresh_fleetup-'+ str(fitting['DoctrineId']) + ':' + str(response.code))

			else:
				logger.warning(doctrines)
				
		else:
			logger.info('refresh_fleetup:' + str(response.code))
	