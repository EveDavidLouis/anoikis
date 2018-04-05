from tornado import gen 

@gen.coroutine
def GET(webHandler,payload={}):

	return {'mode':'render','template':'home.html','data':payload}
