from google.appengine.ext import db

class Video(db.Model):
	url = db.StringProperty()
	title = db.StringProperty()
	published = db.DateTimeProperty()
	channel = db.StringProperty()
class BradyVideo(Video):
	pass
class GreyVideo(Video):
	pass

class UpdateLog(db.Model):
	update_time = db.DateTimeProperty(auto_now=True)