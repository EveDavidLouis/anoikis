from tornado import gen 

@gen.coroutine
def GET(webHandler,payload={}):

	payload['sso'] = webHandler.settings['config'].sso
	if not 'state' in payload: payload['state'] = 'home'

	return {'mode':'render','template':'login.html','data':payload}