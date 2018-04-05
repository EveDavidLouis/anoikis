from tornado import gen 
from tornado.httpclient import AsyncHTTPClient

@gen.coroutine
def asyncFetch(request):

	http_client = AsyncHTTPClient()
	response = yield http_client.fetch(request['url'],None,raise_error=False,**request['kwargs'])
	http_client.close()

	return response 

@gen.coroutine
def asyncMultiFetch(requests):

	http_client = AsyncHTTPClient()

	responses = yield [ http_client.fetch(request['url'],None,raise_error=False,**request['kwargs'])  for request in requests]
	http_client.close()

	return responses

class AsyncClient():

	@gen.coroutine
	def asyncFetch(self,request):

		client = AsyncHTTPClient()
		response = yield client.fetch(request['url'],None,raise_error=False,**request['kwargs'])
		client.close()
		return response 

	@gen.coroutine
	def asyncMultiFetch(self,requests):
		
		client = AsyncHTTPClient()
		responses = yield [ client.fetch(request['url'],None,raise_error=False,**request['kwargs'])  for request in requests]
		client.close()
		return responses