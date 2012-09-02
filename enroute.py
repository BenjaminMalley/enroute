from flask import Flask, render_template, session, url_for, redirect, request, flash, make_response
import config
import oauth2 as oauth
import redis
import urlparse
from urllib import urlencode
import redis
import json

app = Flask(__name__)
app.secret_key = config.consumer_key
app.consumer = oauth.Consumer(key=config.consumer_key, secret=config.consumer_secret)
app.cache = redis.StrictRedis(
	host="localhost",
	port=6379,
	db=0)
app.auth_url = config.auth_url
app.site_url = config.site_url
app.tweet_url = config.tweet_url
app.client = oauth.Client(app.consumer)

def verify_response(resp, content):
	if app.debug:
		with open(config.log_file, "a") as log:
			log.write(request.url+"\n")
			log.write("".join(["twitter response: ", str(resp), "\n"]))
			log.write("".join(["twitter content: ", content, "\n"]))
	if resp["status"] != "200":
		session.pop("access_token", None)
		session.pop("request_token", None)
		flash("Bad response from Twitter")	
		return redirect(url_for("index"))	
	else:
		return None

@app.route("/", methods=["GET",])
def index():
	return render_template("index.html")

@app.route("/signin/")
def twitter_signin():
	resp, content = app.client.request(app.auth_url+"request_token", "POST",
		body=urlencode({"oauth_callback": app.site_url+url_for("twitter_authenticated")}))
	verify_response(resp, content)
	session["request_token"] = dict(urlparse.parse_qsl(content))
	return redirect("{0}?oauth_token={1}".format(app.auth_url+"authorize",
							session["request_token"]["oauth_token"]))
							
@app.route("/authenticated/")
def twitter_authenticated():
	if "request_token" in session:
		client = oauth.Client(app.consumer, oauth.Token(session["request_token"]["oauth_token"],
			session["request_token"]["oauth_token_secret"]))
		resp, content = client.request(app.auth_url+"access_token", "GET")
		verify_response(resp, content)
		session["access_token"] = dict(urlparse.parse_qsl(content))
		return render_template("route.html", maps_api_key=config.maps_api_key)
	else:
		return "You must have an active session"

@app.route("/tweet/", methods=["GET", "POST"])
def send_tweet():
	if "access_token" in session:
		client = oauth.Client(app.consumer,
			oauth.Token(key=session["access_token"]["oauth_token"],
			secret=session["access_token"]["oauth_token_secret"]))
		resp, content = client.request(config.tweet_url, "POST",
			body=urlencode({"status":
			"I started a trip! Track my progress at {0}track/{1}".format(
			app.site_url, session["access_token"]["screen_name"])}))
		verify_response(resp, content)

		session.pop("access_token", None)
		session.pop("request_token", None)
		return ""
	else:
		return "You must have an active session"
	


'''
@app.route('/route/', methods=['POST',])
def route():
	try:
		user = session['access_token']['screen_name']
	except KeyError:
		# not authorized
		return make_response('You must have a valid session to complete this request.', 401)
	
	#if not app.cache.exists(':'.join([user,'dur'])):	
		
		# this is the first server push, generate a tweet
	client = oauth.Client(app.consumer,
		oauth.Token(key=session['access_token']['oauth_token'],
		secret=session['access_token']['oauth_token_secret']))
	resp, content = client.request(config.tweet_url, 'POST', body=urlencode({
		'status': "I started a trip! Track my progress at {0}track/{1}".format(
		app.site_url, user),
	}))
	if app.debug:
		with open(config.log, 'a') as log:
			log.write("\n".join(["", "/route/", "access_token: {0}".format(session['access_token']['oauth_token'])]))
	verify_response(resp)

	"""
	with app.cache.pipeline() as pipe:
		for key in ('lat', 'lng', 'dest', 'dur'):
			pipe.set(':'.join([user,key]), request.form[key])
			# set to expire ten minutes after arrival
			pipe.expire(':'.join([user,key]), int(request.form['dur'])+600)
		pipe.execute()
	"""
	return 'OK'
'''

@app.route("/track/<user>/")
def track_user(user):
	if not app.cache.exists(":".join([user,"dur"])):
		return make_response("nothing here", 404)
	return render_template("track.html", maps_api_key=config.maps_api_key, user=user)

@app.route("/loc/<user>/")
def get_location(user):
	d = dict([(i,app.cache.get(":".join([user,i])))
		for i in ("lat","lng","dest","dur")])
	return json.dumps(d)


if __name__ == "__main__":
	app.run(debug=True)
