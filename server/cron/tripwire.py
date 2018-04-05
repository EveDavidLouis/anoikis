from tornado import gen 
from server.utils import tripwire

import datetime

import logging
logger = logging.getLogger('cron-tripwire')
	
@gen.coroutine
def refresh_tripwire(chars=[],db=None):
	
	_changedOn = datetime.datetime.utcnow()
	payload={}

	for char in chars:
		
		result = yield char.getAll()

		for mask,signatures in result.items():

			i = 0
			
			for signature in signatures:
				signature['_changedOn'] = _changedOn
				result = yield db.tripwire.update({'id':signature['id']},{'$set':signature},upsert=True)
				i = i + 1
			
			payload[mask] = i

	logger.info(payload)