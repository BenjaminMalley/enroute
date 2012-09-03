from flask import Flask, render_template, session, url_for, redirect, request, flash
import config
import oauth2 as oauth
import redis
import urlparse
from urllib import urlencode
import redis
import json
import random

app = Flask(__name__)
app.secret_key = config.consumer_key
app.consumer = oauth.Consumer(key=config.consumer_key, secret=config.consumer_secret)
app.cache = redis.StrictRedis(
	host=config.redis_host,
	port=config.redis_port,
	db=config.redis_db)
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

def verify_session(view):
	if "access_token" in session:
		return view()
	else:
		return ("Forbidden", 403)

@app.route("/begin/", methods=["POST",])
def start_trip():
	if "access_token" in session:
		client = oauth.Client(app.consumer,
			oauth.Token(key=session["access_token"]["oauth_token"],
			secret=session["access_token"]["oauth_token_secret"]))

		url = str(random.randint(0,1000))
		d = dict([(k, request.form[k]) for k in ('lat', 'lng', 'dest', 'dur')])
		d["url"] = url
		with app.cache.pipeline() as pipe:
			pipe.set(url, session["access_token"]["screen_name"])
			pipe.expire(session["access_token"]["screen_name"], int(request.form['dur'])+600)
			pipe.hmset(session["access_token"]["screen_name"], d)
			pipe.execute()
		
		'''
		resp, content = client.request(config.tweet_url, "POST",
			body=urlencode({"status":
			"I started a trip! Track my progress at {0}track/{1}".format(
			app.site_url, session["access_token"]["screen_name"])}))
		verify_response(resp, content)
		'''

		return "OK"
	else:
		return ("Forbidden", 403)
	
@app.route("/update/", methods=["POST",])
def update_location():
	if "access_token" in session:
		with app.cache.pipeline() as pipe:
			pipe.hmset(session["access_token"]["screen_name"],
				dict([(k, request.form[k]) for k in ('lat', 'lng', 'dest', 'dur')]))
			pipe.expire(session["access_token"]["screen_name"], int(request.form['dur'])+600)
			pipe.execute()
		return "OK"
	else:
		return "You must have an active session"

@app.route("/end/", methods=["POST",])
def end_trip():
	if "access_token" in session:
		with app.cache.pipeline() as pipe:
			k = pipe.hget(session["access_token"]["screen_name"], "url")
			pipe.expire(session["access_token"]["screen_name"], 0)
			pipe.expire(k, 0)
			pipe.execute()
		return "OK"
	else:
		return "You must have an active session"

@app.route("/track/<user>/")
def track_user(user):
	if not app.cache.exists(user):
		return ("nothing here", 404)
	return render_template("track.html", maps_api_key=config.maps_api_key, user=user)

@app.route("/loc/<user>/")
def get_location(user):
	if not app.cache.exists(user):
		return ("nothing here", 404)
	else:
		return json.dumps(app.cache.hgetall(user))

if __name__ == "__main__":
	app.run(debug=config.debug)
