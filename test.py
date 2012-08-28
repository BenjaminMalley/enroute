import unittest
import enroute

class Test(unittest.TestCase):
	def setUp(self):
		enroute.app.auth_url = "127.0.0.1"
		enroute.app.site_url = "127.0.0.1"
		enroute.tweet_url = "127.0.0.1"
		self.app = enroute.app.test_client()

	def test_static_endpoints(self):
		for endpoint in ["/", "/cb/"]:
			assert self.app.get(endpoint).status_code == 200
		
		for endpoint in ["/authorize/"]:
			assert self.app.get(endpoint).status_code == 302
		
		'''
		for endpoint in ["/route/"]:
			print self.app.post(endpoint).status_code
			assert self.app.post(endpoint).status_code == 401
		'''
		
		
if __name__ == "__main__":
	unittest.main()