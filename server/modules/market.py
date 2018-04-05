from tornado import gen 
from server.utils.fetch import asyncMultiFetch

import json

import logging	
logger = logging.getLogger('market')

@gen.coroutine
def GET(webHandler,payload={}):

	_path = webHandler.getPath()

	mode = ''
	itemId = ''

	if len(_path) > 1: itemId 	= int(_path[1])
	if len(_path) > 2: mode 	= str(_path[2])

	if itemId == '' : itemId = 44992

	payload['itemName'] = webHandler.settings['itemMap'].getItem(itemId)['name']

	regions = ['10000019', '10000054', '10000069', '10000055', '10000007', '10000014', '10000051', '10000053', '10000012', '10000035', '10000060', '10000001', '10000005', '10000036', '10000043', '10000039', '10000064', '10000027', '10000037', '10000046', '10000056', '10000058', '10000029', '10000067', '10000011', '10000030', '10000025', '10000031', '10000009', '10000017', '10000052', '10000049', '10000065', '10000016', '10000013', '10000042', '10000028', '10000040', '10000062', '10000021', '10000057', '10000059', '10000063', '10000066', '10000048', '10000047', '10000023', '10000050', '10000008', '10000032', '10000044', '10000022', '10000041', '10000020', '10000045', '10000061', '10000038', '10000033', '10000002', '10000034', '10000018', '10000010', '10000004', '10000003', '10000015', '10000068', '10000006']
	#regions = ['10000002']

	data = {'itemId':itemId , 'marketSell':[] ,'marketBuy':[]}
	shortData = {'itemId':itemId,'itemName':payload['itemName'],'sellPrice':None,'sellVolume':0,'buyPrice':None,'buyVolume':0}

	chunkSize = 50

	#SELL
	requests = [{'kwargs':{},'url':'https://crest-tq.eveonline.com/market/'+region+'/orders/sell/?type=https://crest-tq.eveonline.com/inventory/types/'+str(itemId)+'/' } for region in regions ]	

	marketData = []
	
	for i in range(0, len(requests), chunkSize):
		chunk = requests[i:i + chunkSize]
		responses = yield asyncMultiFetch(chunk)

		for response in responses:
			for d in json.loads(response.body.decode())['items']:
					marketData.append(d)

	for d in sorted(marketData, key=lambda k: k['price'], reverse=False):
		if shortData['sellPrice'] == None or d['price'] < shortData['sellPrice'] : shortData['sellPrice'] = d['price']
		shortData['sellVolume'] = shortData['sellVolume'] + d['volume']
		data['marketSell'].append({'price':'{:20,.2f}'.format(d['price']).replace(',',' '),'volume':d['volume'],'location':d['location']['name']})

	#BUY
	requests = [{'kwargs':{},'url':'https://crest-tq.eveonline.com/market/'+region+'/orders/buy/?type=https://crest-tq.eveonline.com/inventory/types/'+str(itemId)+'/' } for region in regions ]	

	marketData = []
	for i in range(0, len(requests), chunkSize):
		
		chunk = requests[i:i + chunkSize]

		responses = yield asyncMultiFetch(chunk)

		for response in responses:
			for d in json.loads(response.body.decode())['items']:
					marketData.append(d)

	for d in sorted(marketData, key=lambda k: k['price'], reverse=True):
		if shortData['buyPrice']  == None or d['price'] > shortData['buyPrice'] : shortData['buyPrice'] = d['price']
		shortData['buyVolume'] = shortData['buyVolume'] + d['volume']
		data['marketBuy'].append({'price':'{:20,.2f}'.format(d['price']).replace(',',' '),'volume':d['volume'],'location':d['location']['name']})

	payload.update(data)

	if mode == 'json':
		return {'mode':'json','data':shortData}
	else :
		return {'mode':'render','template':'market.html','data':payload}
