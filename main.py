#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import cgi
import datetime
import time
import webapp2

import hashlib
import pickle

from google.appengine.ext import db
from google.appengine.api import memcache

import youtube_integration
from database_tables import *

GREY_CHANNELS = [ 'CGPGrey', 'CGPGrey2',
'greysfavs']
BRADY_CHANNELS = [ 'numberphile', 'Computerphile',
'sixtysymbols', 'periodicvideos', 'nottinghamscience',
'DeepSkyVideos', 'bibledex', 'wordsoftheworld',
'FavScientist', 'psyfile', 'BackstageScience',
'foodskey', 'BradyStuff']

def disp_viewcount(db_views):
	if db_views == 301:
		return '<a href="http://youtu.be/oIkhgagvrjI">301</a>'
	elif db_views >= 0:
		return db_views
	elif db_views == -1:
		return "&lt;live video&gt;"
	elif db_views == -2:
		return "&lt;not yet calculated&gt;"
	else:
		return "&lt;error&gt;"
	
def load_front_data():
	bradyVids = memcache.get('bradyVids')
	greyVid = memcache.get('greyVid')
	lastUpdate = memcache.get('lastUpdate')
	
	greyViews = memcache.get('greyViews')
	bradyTotal = memcache.get('bradyTotal')
	bradyAverage = memcache.get('bradyAverage')
	
	if not (bradyVids and greyVid and lastUpdate and greyViews and bradyTotal and bradyAverage):
		bradyVids = db.GqlQuery("SELECT * FROM BradyVideo ORDER BY published DESC")
		bradyVids = list(bradyVids)
		memcache.set('bradyVids', bradyVids)
		
		greyVid = list(db.GqlQuery("SELECT * FROM GreyVideo ORDER BY published DESC LIMIT 1"))[0]
		memcache.set('greyVid', greyVid)
		
		lastUpdate = list(db.GqlQuery("SELECT * FROM UpdateLog ORDER BY update_time DESC LIMIT 1"))[0].update_time
		memcache.set('lastUpdate', lastUpdate)
		
		greyViews = disp_viewcount(greyVid.viewcount)
		memcache.set('greyViews', greyViews)
		
		countable_brady_counts = [vid.viewcount for vid in bradyVids if vid.viewcount>=0]
		
		bradyTotal = sum(countable_brady_counts)
		memcache.set('bradyTotal', bradyTotal)
		
		
		if len(countable_brady_counts)==0:
			bradyAvg = 'N/A'
		else:
			bradyAvg = bradyTotal/len(countable_brady_counts)
		
		memcache.set('bradyAvg', bradyAvg)
	
	return (bradyVids, greyVid, lastUpdate, greyViews, bradyTotal, bradyAvg)

def esc(s):
	return cgi.escape(s,quote=True)


class Handler(webapp2.RequestHandler):
	def write(self,content):
		self.response.out.write(content)
	
	def set_cookie(self, name, value, expires=None, path='/', domain=None):
		extra_info = ''
		if expires:
			extra_info += 'expires=%s; '%expires
		if path:
			extra_info += 'path=%s; '%path
		if domain:
			extra_info += 'domain=%s; '%domain
		if extra_info:
			extra_info = '; ' + extra_info[:-2]
		main_statement = '%s=%s'%(name,value)
		set_cookie_val = main_statement + extra_info
		self.response.headers.add_header('Set-Cookie',set_cookie_val)
	
	def clear_cookie(self, name):
		cookie = self.read_cookie(name)
		if not cookie:
			return
		self.set_cookie(name, '', path=None)
	
	def read_cookie(self, name, alt=None):
		return self.request.cookies.get(name,alt)

page_template = """
<!DOCTYPE html>

<html>
<head>
	<title>Brady vs. Grey</title>
	<script>
		function revealThings ()
		{
			for (var i in document.getElementsByClassName('hidden-to-grey'))
			{
				document.getElementsByClassName('hidden-to-grey')[i].hidden = false;
			}
			var button = document.getElementById('hidden-stuff-toggle');
			button.parentNode.removeChild(button);	
		}
	</script>
	
	<script>
      (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
      (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
      })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
    
      ga('create', 'UA-50387911-1', 'brady-vs-grey.appspot.com');
      ga('send', 'pageview');
	</script>
</head>
<body>
<font size="5">Q: How many videos has Brady Haran released since C.G.P. Grey last released a video?<br />
A:
</font>
<span style="font-size: 100px;">%(number)s</span>
<br /><hr /><br />
<table cellpadding="5" cellspacing="5">
	<tr>
		<td><strong>
			Creator
		</strong></td>
		<td><strong>
			Channel
		</strong></td>
		<td><strong>
			Uploaded
		</strong></td>
		<td><strong>
			View Count
		</strong></td>
		<td><strong>
			Title/Link
		</strong></td>
	</tr>
	%(rows)s
</table>
<hr>
<font size="5">Q: How do their view counts compare?<br />A:</font>

<table cellpadding="3" cellspacing="3">
	<tr>
		<td>Grey</td>
		<td align="right">%(grey_views)s</td>
	</tr>
	<tr>
		<td>Brady: Average</td>
		<td align="right">%(brady_avg)s</td>
	</tr>
	<tr id="hidden-stuff-toggle" %(brady_visible)s>
		<td colspan="2">
			<button onclick="revealThings();">Grey, don't click here!</button>
		</td>
	</tr>
	<tr class="hidden-to-grey" %(brady_hidden)s>
		<td>Brady: Total</td>
		<td align="right">%(brady_total)s</td>
	</tr>
</table>

<hr />
Last updated: %(refresh_date)s.
Powered by YouTube Data API (v3).
<hr />
<a href="http://github.com/nicktendo64/brady-vs-grey">View the source code on GitHub.</a>
<br />
<iframe style="width: 100%%; border: 0;" src="https://dl.dropboxusercontent.com/u/23230235/For%%20Other%%20Websites/brady_vs_grey_messages.html"></iframe>
</body>
</html>
"""
def get_row(vid):
	return \
	"""
	<tr>
		<td>
			%(creator)s
		</td>
		<td>
			%(channel)s
		</td>
		<td>
			%(published)s
		</td>
		<td>
			%(views)s
		</td>
		<td>
			<a href="%(url)s">
				%(title)s
			</a>
		</td>
	</tr>
	""" % {
	'title': vid.title,
	'channel': vid.channel,
	'published': vid.published.strftime('%B %d, %Y @ %I:%M %p'),
	'url': 'http://youtu.be/' + vid.yt_id,
	'creator': ("Brady Haran" if vid.channel in BRADY_CHANNELS else "C.G.P. Grey"),
	'views': disp_viewcount(vid.viewcount)
	}

class MainHandler(Handler):
    def get(self):
        bradyVids, greyVid, lastUpdate, greyViews, bradyTotal, bradyAvg = load_front_data()
        formatting_table = { }
        formatting_table['number'] = len(bradyVids)
        formatting_table['refresh_date'] = lastUpdate.strftime('%Y-%m-%d, %H:%M:%S UTC')
        formatting_table['rows'] = '\n'.join([get_row(greyVid)] + [get_row(vid) for vid in bradyVids[::-1]])
        formatting_table['grey_views'] = greyViews
        formatting_table['brady_total'] = bradyTotal
        formatting_table['brady_avg'] = bradyAvg
        formatting_table['brady_visible'] = ('hidden' if greyViews > bradyTotal else '')
        formatting_table['brady_hidden'] = ('hidden' if greyViews <= bradyTotal else '')
        
        self.write(page_template%formatting_table)        

class UpdateHandler(Handler):
	def get(self):
		if self.request.headers.get('X-Appengine-Cron') != 'true': # This header is only given by a cron job.
			self.error(400)
			return
		
		
		all_grey_vids = [ ]
		for channel in GREY_CHANNELS:
			all_grey_vids += youtube_integration.get_vids(channel,'GreyVideo')
		
		all_brady_vids = [ ]
		for channel in BRADY_CHANNELS:
			all_brady_vids += youtube_integration.get_vids(channel,'BradyVideo')
		
		
		all_grey_vids.sort(key=lambda vid:vid.published, reverse=True)
		latest_grey_vid = all_grey_vids[0]
		
		all_brady_vids.sort(key=lambda vid:vid.published, reverse=True)
		
		for e in db.GqlQuery("SELECT * FROM BradyVideo"):
			e.delete()
		for e in [vid for vid in all_brady_vids if vid.published > latest_grey_vid.published]:
			e.put()
		
		for e in db.GqlQuery("SELECT * FROM GreyVideo"):
			e.delete()
		latest_grey_vid.viewcount = youtube_integration.get_view_count(latest_grey_vid.yt_id)
		latest_grey_vid.put()
		
		for e in db.GqlQuery("SELECT * FROM UpdateLog"):
			e.delete() 
		UpdateLog().put()
		
		time.sleep(1) # Wait for all the videos to be added before view calculation
		
		for brady_vid in list(db.GqlQuery("SELECT * FROM BradyVideo")):
			brady_vid.viewcount = youtube_integration.get_view_count(brady_vid.yt_id)
			brady_vid.put()
		
		time.sleep(1)
		
		# Extra duplicate prevention
		already_cleaned = [ ]
		for vid in db.GqlQuery("SELECT * FROM BradyVideo"):
			if vid.yt_id in already_cleaned: # Prevents videos from being deleted entirely
				continue
			
			for other_vid in db.GqlQuery("SELECT * FROM BradyVideo"):
				if (other_vid.yt_id == vid.yt_id) and (vid.key().id() != other_vid.key().id()):
					other_vid.delete()
					already_cleaned.append(vid.yt_id)
		
		self.write('Database updated! <a href="/update_push?secret=%s">Push this update.</a>' % secret)

class UpdatePushHandler(Handler):
	def get(self):
		if self.request.headers.get('X-Appengine-Cron') != 'true': # This header is only given by a cron job.
			self.error(400)
			return
			
		memcache.flush_all()
		load_front_data()
		
		self.write('Update pushed! <a href="/">Go back to the homepage.</a>')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/update/?',UpdateHandler),
    ('/update_push/?',UpdatePushHandler),
], debug=True)




e404 = """
<!DOCTYPE html>

<html>
<head>
	<title>404 &mdash; Not Found</title>
	<style>
		.error {
			color: red;
			font-family: Impact, "Arial Black", "Comic Sans MS", Verdana, sans-serif;
			font-size: 72pt;
			text-transform: uppercase;
		}
	</style>
</head>
<body>
<center><div class="error">error 404:&nbsp;&nbsp; not found</div></center>
<img src="http://dl.dropboxusercontent.com/u/23230235/For%20Other%20Websites/notthedroids.jpg" height="50%" width="50%"><br>
<font size="5">This is not the page you're looking for.<br>Move along...<br>Move along...</font>
<br><br>
<p>If you wish to report how you got here, email me at
nich<a href="http://www.google.com/recaptcha/mailhide/d?k=01YCS2MGMsm9uky9oHmBW4qw==&amp;c=kjLOqocHPj-BfkpO4at5Sq3r0HGqipZ--vuRwJrolms=" onclick="window.open('http://www.google.com/recaptcha/mailhide/d?k\07501YCS2MGMsm9uky9oHmBW4qw\75\75\46c\75kjLOqocHPj-BfkpO4at5Sq3r0HGqipZ--vuRwJrolms\075', '', 'toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,width=500,height=300'); return false;" title="Reveal this e-mail address">...</a>
@gmail.com</p>
</body>
</html>
"""
def handle_404(request, response, exception):
	response.write(e404)
	response.set_status(exception.status_int)
app.error_handlers[404] = handle_404

e500 = """
<!DOCTYPE html>

<html>
<head>
	<title>500 &mdash; Internal Server Error</title>
	<style>
		.error {
			color: red;
			font-family: Impact, "Arial Black", "Comic Sans MS", Verdana, sans-serif;
			font-size: 72pt;
			text-transform: uppercase;
		}
	</style>
</head>
<body>
<center><div class="error">error 500:&nbsp;&nbsp; internal server error</div></center>

<p>Something's wrong; that's my fault!</p>
<p>Please <a href="mailto:nicholas.curr+webapps@gmail.com">report this (email me at nicholas.curr+webapps@gmail.com)</a> so that the error may be fixed.
</p>
</body>
</html>
"""
def handle_500(request, response, exception):
	response.clear()
	response.write(e500)
app.error_handlers[500] = handle_500
