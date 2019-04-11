from tornado import gen , httpclient

class AsyncFetchClient():

	@gen.coroutine
	def asyncFetch(self,request):

		client = httpclient.AsyncHTTPClient()
		response = yield client.fetch(request['url'],validate_cert=False,raise_error=False,**request['kwargs'])
		client.close()
		return response 

	@gen.coroutine
	def asyncMultiFetch(self,requests):
		
		client = httpclient.AsyncHTTPClient()
		responses = yield [ client.fetch(request['url'],validate_cert=False,raise_error=False,**request['kwargs'])  for request in requests]
		client.close()
		return responses