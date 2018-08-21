from tornado import gen
from server.handlers import fetchHandler
import json , urllib, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('esi')

@gen.coroutine
def getMarket(region_id=None,typeId=None):

	#fetcher
	fe = fetchHandler.AsyncFetchClient()

	if not typeId: typeId = 44992

	regions = ['10000019', '10000054', '10000069', '10000055', '10000007', '10000014', '10000051', '10000053', '10000012', '10000035', '10000060', '10000001', '10000005', '10000036', '10000043', '10000039', '10000064', '10000027', '10000037', '10000046', '10000056', '10000058', '10000029', '10000067', '10000011', '10000030', '10000025', '10000031', '10000009', '10000017', '10000052', '10000049', '10000065', '10000016', '10000013', '10000042', '10000028', '10000040', '10000062', '10000021', '10000057', '10000059', '10000063', '10000066', '10000048', '10000047', '10000023', '10000050', '10000008', '10000032', '10000044', '10000022', '10000041', '10000020', '10000045', '10000061', '10000038', '10000033', '10000002', '10000034', '10000018', '10000010', '10000004', '10000003', '10000015', '10000068', '10000006']
	#regions = ['10000002']

	data = []
	ids = set()
	requests = [{'kwargs':{},'url':'https://esi.evetech.net/latest/markets/'+str(r)+'/orders/?order_type=sell&type_id='+str(typeId)} for r in regions]
	chunkSize = 50
	for i in range(0, len(requests), chunkSize):
		chunk = requests[i:i + chunkSize]
		responses = yield fe.asyncMultiFetch(chunk)
		for response in responses:
			if response.code == 200:
					for item in json.loads(response.body.decode()):
						data.append(item)
						ids.add(item['location_id'])

	body = json.dumps({'ids':list(ids)})
	request = {'kwargs':{'method':'POST' , 'body':body } ,'url':'https://esi.evetech.net/legacy/universe/names/'}
	response = yield fe.asyncFetch(request)
	locations = { i['id'] : i['name'] for i in json.loads(response.body.decode())}

	for i in range(len(data)): 
		data[i]['location_name'] = locations[data[i]['location_id']]

	return data