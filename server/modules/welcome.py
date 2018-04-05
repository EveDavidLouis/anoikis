from tornado import gen 
import logging
logger = logging.getLogger('welcome')

@gen.coroutine
def GET(webHandler,payload={}):

	payload['sso'] = webHandler.settings['config'].sso
	payload['state'] = 'welcome'
	return {'mode':'render','template':'welcome.html','data':payload}