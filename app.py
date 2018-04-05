import os

from tornado.ioloop import IOLoop , PeriodicCallback
from tornado.web import Application

from motor import motor_tornado

from server.config import config
from server.handlers import socket , web , worker
from server import cron
from server.utils import tripwire, eve

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

class Application(Application):

	def __init__(self):
		handlers = [
			(r"/ws/(.*)", socket.SocketHandler),
			(r"/ws", socket.SocketHandler),
			(r"/(.*)", web.MainHandler),
		]
		settings = dict(	
			cookie_secret="not so secret!",
			template_path=os.path.join(os.path.dirname(__file__), "server/templates"),
			static_path=os.path.join(os.path.dirname(__file__), "static"),
			xsrf_cookies=False,
			debug=False,
			autoreload=config.server['autoreload']
		)
		super(Application, self).__init__(handlers, **settings)

if __name__ == "__main__":

	logger.info('Starting server ' + str(config.server))

	#mongoDb
	mongoClient = motor_tornado.MotorClient(config.mongodb['host'], config.mongodb['port'])
	mongoDb = mongoClient[config.mongodb['db']]
	workerClient = worker.Worker("ws://"+config.server['host']+":"+str(config.server['port'])+"/ws")
	solarMap = eve.SolarMap(mongoDb)
	itemMap = eve.ItemMap(mongoDb)

	#application
	app = Application()
	app.settings['config'] = config
	
	app.settings['db'] = mongoDb
	app.settings['worker'] = workerClient

	app.settings['itemMap'] = itemMap
	app.settings['solarMap'] = solarMap
	
	app.listen(config.server['port'],config.server['host'])

	#cron jobs
	cron_refreshTokens = PeriodicCallback(lambda : cron.esi.refreshTokens(db=app.settings['db'],authorization=config.sso['authorization']),60000)
	cron_refreshTokens.start()
 	
	tripwireChars=[tripwire.Tripwire(tripwireUsername=i['tripwireUsername'],tripwirePassword=i['tripwirePassword'],maskList=i['maskList'])for i in config.tripwire]
	cron_tripwire = PeriodicCallback(lambda : cron.tripwire.refresh_tripwire(db=app.settings['db'],chars=tripwireChars),60000*15)
	cron_tripwire.start()
	
	#workers
	IOLoop.instance().run_sync(workerClient.run)

	#starting IOLoop
	IOLoop.instance().start()