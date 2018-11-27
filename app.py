import os
import logging
import json

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('app')

from tornado import ioloop , gen , web
from motor.motor_tornado import MotorClient
from server import config
from server.handlers import webHandler, socketHandler, fetchHandler , jobHandler

class Application(web.Application):

	def __init__(self):
		handlers = [
			(r"/images/(.*)"	,web.StaticFileHandler, {"path": "docs/images"}),
			(r"/templates/(.*)"	,web.StaticFileHandler, {"path": "docs/templates"}),
			(r"/styles/(.*)"	,web.StaticFileHandler, {"path": "docs/styles"}),
			(r"/scripts/(.*)"	,web.StaticFileHandler, {"path": "docs/scripts"}),	
			(r"/esi/(.*)"		,socketHandler.SocketHandler , {},"wsi"),
			(r"/market/(.*)"	,webHandler.MarketHandler),
			(r"/tripwire"		,webHandler.TripwireHandler),
			(r"/system/(.*)"	,webHandler.SystemHandler),
			(r"/index.html"		,web.StaticFileHandler, {"path": "docs/index.html"}),
			(r"/(.*)"			,web.StaticFileHandler, {"path": "docs/index.html"}),
			(r""				,web.StaticFileHandler, {"path": "docs/index.html"}),
		]
		settings = dict(	
			cookie_secret=config.server['secret'],
			template_path=os.path.join(os.path.dirname(__file__), "server/templates"),
			static_path=os.path.join(os.path.dirname(__file__), "docs"),
			static_url_prefix = "/static/",
			xsrf_cookies=False,
			debug=False,
			autoreload=True
		)
		super(Application, self).__init__(handlers, **settings)

if __name__ == "__main__":

	logger.info(config.server['host'] + ':' + str(config.server['port']))

	#application
	app = Application()

	#modules
	db = MotorClient(config.mongodb['url'])[config.mongodb['db']]
	fe = fetchHandler.AsyncFetchClient()
	ws = app.wildcard_router.named_rules['wsi'].target

	#workers
	qe = jobHandler.QueueWorker(db=db,fe=fe,ws=ws,co=config)
	cr = jobHandler.CronWorker(db=db,fe=fe,ws=ws,co=config,qe=qe)

	#settings
	app.settings['co'] = config
	app.settings['db'] = db
	app.settings['fe'] = fe
	app.settings['qe'] = qe
	app.listen(config.server['port'],config.server['host'])
	
	#cronWorker
	cron = ioloop.PeriodicCallback(lambda : cr.refresh_api(),15*60*1000)
	cron.start()

	#queueWorker
	ioloop.IOLoop.instance().run_sync(qe.run)

	#starting IOLoop

	ioloop.IOLoop.instance().start()