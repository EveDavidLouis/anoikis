import tornado.websocket
from tornado import gen 

import uuid
import json

from server.utils import utils , fetch , tripwire

import logging
logger = logging.getLogger('socket')

class SocketHandler(tornado.websocket.WebSocketHandler):
	
	waiters = set()
	cache = []
	cache_size = 200

	@gen.coroutine
	def check_origin(self, origin):
		logger.info(str(origin))
		return True

	@gen.coroutine
	def open(self,channel='main'):
		
		db = self.settings['db']

		self.id = uuid.uuid4()
		self.name = str(self.id)

		SocketHandler.waiters.add(self)

	@gen.coroutine
	def on_close(self):
		
		SocketHandler.waiters.remove(self)
		logger.info('close:'+self.name)

	@gen.coroutine
	def on_message(self,inbound={},channel=''):

		inbound = utils.loadJson(inbound)
		outbound = {}
		logger.info(str(self.name)+' --> '+str(inbound))

		if inbound :
			
			if 'p' in inbound:
				outbound['d'] = yield self.getMarket(inbound['p'])
			if 'a' in inbound:
				self.name = inbound['a']
			if 'b' in inbound:
				self.broadcast(inbound['b'])
			if 's' in inbound:
				self.settings['worker'].add({inbound['s']:1})

		else :
			outbound = {'e':str(inbound)}	
		
		self.write_message(outbound)

	@gen.coroutine
	def getMarket(self,itemId = 44992):

		regions = ['10000019', '10000054', '10000069', '10000055', '10000007', '10000014', '10000051', '10000053', '10000012', '10000035', '10000060', '10000001', '10000005', '10000036', '10000043', '10000039', '10000064', '10000027', '10000037', '10000046', '10000056', '10000058', '10000029', '10000067', '10000011', '10000030', '10000025', '10000031', '10000009', '10000017', '10000052', '10000049', '10000065', '10000016', '10000013', '10000042', '10000028', '10000040', '10000062', '10000021', '10000057', '10000059', '10000063', '10000066', '10000048', '10000047', '10000023', '10000050', '10000008', '10000032', '10000044', '10000022', '10000041', '10000020', '10000045', '10000061', '10000038', '10000033', '10000002', '10000034', '10000018', '10000010', '10000004', '10000003', '10000015', '10000068', '10000006']
		requests = [{'kwargs':{},'url':'https://esi.tech.ccp.is/latest/markets/'+region+'/orders/?order_type=sell&type_id='+str(itemId) } for region in regions ]	

		chunkSize = 50
		data = {'itemId':itemId , 'marketSell':[] ,'marketBuy':[]}
		marketData = []
	
		for i in range(0, len(requests), chunkSize):
			
			chunk = requests[i:i + chunkSize]
			responses = yield fetch.asyncMultiFetch(chunk)

			for response in responses:

				for d in json.loads(response.body.decode()):
						marketData.append(d)

		# for d in sorted(marketData, key=lambda k: k['price'], reverse=False):
		# 	data['marketSell'].append({'price':'{:20,.2f}'.format(d['price']).replace(',',' '),'volume':d['volume'],'location':d['location']['name']})

		outbound = {}
		outbound['p'] = sorted(marketData, key=lambda k: k['price'], reverse=False)

		return outbound

	def broadcast(self,inbound={}):
		
		outbound = inbound
		
		for waiter in self.waiters:
			if waiter.id != self.id:
				try:
					waiter.write_message(outbound)
				except:
					logging.error("Error sending message")