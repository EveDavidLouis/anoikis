import datetime , json
from tornado import gen

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cron')

from server import esi

@gen.coroutine
def test(ws,fe):

	# response = yield esi.getMarket()

	# if response:
	# 	ws.send(response)
	# else:
	# 	ws.send({})

	ws.send({'test':1})