import json

import logging	
logger = logging.getLogger('eve')

from tornado import gen 

class SolarMap:

	def __init__(self,db):
		
		self.db = db

		self.solarMap = {}
		self.solarMapIndex = {}

		self.loadMongo()

	def __getitem__(self,id):
		return self.getSystem(id)

	def getSystem(self,id):
		return self.solarMap[id]

	def getSystemByName(self,name):
		if name == 'All':
			return self.getAllSystems()
		elif name in self.solarMapIndex:
			return self.solarMap[self.solarMapIndex[name]]
		else:
			return None

	def getAllSystems(self):

		return [self.solarMap[i] for i in self.solarMap]

	def getSpeech(self,i):

		speech=[]

		speech.append( 'Welcome to {name}.'.format(**i) )
		
		speech.append('{name} is a {systemClass} system'.format(**i))

		if i['spaceType'] == 'K-Space' : 
			speech.append('It belongs to the {constellation} constellation, within the {region} region'.format(**i))
		
		if 'shattered' in i: 
			speech.append('This is a shattered wormhole')

		if 'effect' in i : 
			speech.append('the wormholehole effect is {effect}'.format(**i))
		
		if 'staticGroup' in i and len(i['staticGroup']) > 0 : 
			if len(i['staticGroup']) == 1 : 
				speech.append('This wormhole has a single {static} static'.format(static=i['staticGroup'][0]))
			else:
				speech.append('This wormhole has {count} statics'.format(count=len(i['staticGroup'])))
				for static in i['staticGroup']:
					speech.append('a {static} static.'.format(static=static))

		if i['name'] == 'Jita' : 
			speech.append('Jita is a special place. If you send me some ISK, i will double it, i promise.')

		if i['name'] == 'Thera' : 
			speech.append('Thera is a special place. This is the most connected system in New Eden.')
			speech.append('Thera is also the home of Signal Cartel.')
			speech.append('Scouts, are mapping all connections informations at www.eve-scout.com')

		return speech

	@gen.coroutine
	def loadMongo(self):
		
		logger.info('loadingMongoSystems')
		result = self.db.systems.find({})
		
		for i in (yield result.to_list(length=99999)):
			self.solarMap[i['id']] = i
			self.solarMapIndex[i['name']] = i['id']

		logger.info('loadedMongoSystems')

class ItemMap:

	def __init__(self,db):
		
		self.db = db

		self.itemMap = {}
		self.itemMapIndex = {}

		self.loadMongo()

	def __getitem__(self,id):
		return self.getItem(id)

	def getItem(self,id):
		return self.itemMap[id]

	def getItemByName(self,name):
		if name in self.itemMapIndex:
			return self.itemMap[self.itemMapIndex[name]]
		else:
			return None

	@gen.coroutine
	def loadMongo(self):
		logger.info('loadingMongoItems')
		result = self.db.ESItypes.find({},{'type_id':1,'name':1})

		for i in (yield result.to_list(length=99999)):
			self.itemMap[i['type_id']] = i
			self.itemMapIndex[i['name']] = i['type_id']

		logger.info('loadedMongoItems')