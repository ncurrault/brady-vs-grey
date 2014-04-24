from google.appengine.ext import db

class Video(db.Model):
	yt_id = db.StringProperty()
	title = db.StringProperty()
	published = db.DateTimeProperty()
	channel = db.StringProperty()
	
	viewcount = db.IntegerProperty()
	# [0,inf) for actual view count
	# -1 for live videos
	# -2 for not yet calculated
	# -3 for misc. errors
	

class BradyVideo(Video):
	pass
class GreyVideo(Video):
	pass

class UpdateLog(db.Model):
	update_time = db.DateTimeProperty(auto_now=True)