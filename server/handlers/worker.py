import json

from tornado.queues import Queue
from tornado import gen 

from tornado.websocket import websocket_connect

import logging
logger = logging.getLogger('worker')

class Worker():

	def __init__(self, url='ws://0.0.0.0:8081/ws'):
		self.socketServer = url
		self.q = Queue(maxsize=10)

	@gen.coroutine
	def run(self):

		#logger.info('Starting worker ' + str(socketServer))
		self.client = yield websocket_connect(self.socketServer)
		self.client.write_message('{"a":"worker"}')

		while True:
			item = yield self.q.get()
			try:
				#logger.info(str(item))
				message = {'b':str(item)}
				
				if 's' in item: yield gen.sleep(item['s'])

				self.client.write_message(json.dumps(message))

			finally:
				self.q.task_done()

	@gen.coroutine
	def add(self,job=None):
		self.q.put(job)

# def init(url='ws://0.0.0.0:8081/ws'):
	
# 	global socketServer
# 	socketServer = url