from tornado import gen 

@gen.coroutine
def GET(webHandler,payload={}):

	payload['time'] 	= webHandler.getRequestTime()
	payload['request'] 	= webHandler.getRequest()
	payload['cookies'] 	= webHandler.getCookies()
	payload['inputs'] 	= webHandler.getInputs()
	payload['path'] 	= webHandler.getPath()

	return {'mode':'render','template':'payload.html','data':payload}