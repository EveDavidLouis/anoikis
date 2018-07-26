import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

from tornado import ioloop , gen , web
from motor.motor_tornado import MotorClient
from server import config
from server.handlers import webHandler, socketHandler, jobHandler, fetchHandler

class Application(web.Application):

	def __init__(self):
		handlers = [
			(r"/ws/(.*)", socketHandler.SocketHandler),
			(r"/(.*)", webHandler.DefaultHandler),
			(r"", webHandler.DefaultHandler),
		]
		settings = dict(	
			cookie_secret=config.server['secret'],
			template_path=os.path.join(os.path.dirname(__file__), "docs"),
			static_path=os.path.join(os.path.dirname(__file__), "docs"),
			xsrf_cookies=False,
			debug=False,
			autoreload=True
		)
		super(Application, self).__init__(handlers, **settings)

if __name__ == "__main__":

	logger.info(config.server['host'] + ':' + str(config.server['port']))

	#mongodb
	db = MotorClient(config.mongodb['url'])[config.mongodb['db']]

	#fetcher
	fe = fetchHandler.AsyncFetchClient()

	#workers
	ws = socketHandler.SocketWorker('ws://'+config.server['host']+':'+str(config.server['port'])+'/ws/test')
	
	#application
	app = Application()
	app.settings['db'] = db
	app.settings['fe'] = fe
	app.settings['ws'] = ws
	app.settings['co'] = config
	app.listen(config.server['port'],config.server['host'])
	
	#cron
	#cron_test = ioloop.PeriodicCallback(lambda : jobHandler.test(ws,fe),10000)
	#cron_test.start()

	#starting IOLoop
	ioloop.IOLoop.instance().run_sync(ws.run)
	ioloop.IOLoop.instance().start()