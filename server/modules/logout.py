from tornado import gen 

@gen.coroutine
def GET(webHandler,payload={}):

	webHandler.clear_all_cookies()

	return {'mode':'redirect','url':'/'}