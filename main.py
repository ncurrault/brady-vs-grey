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
import webapp2

import time


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

def load_front_data():
	bradyVids = memcache.get('bradyVids')
	greyVid = memcache.get('greyVid')
	lastUpdate = memcache.get('lastUpdate')
	
	if not (bradyVids and greyVid and lastUpdate):
		bradyVids = db.GqlQuery("SELECT * FROM BradyVideo ORDER BY published DESC")
		bradyVids = list(bradyVids)
		memcache.set('bradyVids', bradyVids)
		
		greyVid = list(db.GqlQuery("SELECT * FROM GreyVideo ORDER BY published DESC LIMIT 1"))[0]
		memcache.set('greyVid', greyVid)
		
		lastUpdate = list(db.GqlQuery("SELECT * FROM UpdateLog ORDER BY update_time DESC LIMIT 1"))[0].update_time
		memcache.set('lastUpdate', lastUpdate)
	
	return (bradyVids, greyVid, lastUpdate)

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
</head>
<body>
<font size="5">Q: How many videos has Brady Haran released since C.G.P. Grey last released a video?<br />
A:
</font>
<span style="font-size: 100px;">%(number)s</span>
<br><br>
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
<br>
Coming soon: view totals/averages.
<br><br>
Last updated: %(refresh_date)s
<br>
Powered by YouTube Data API (v3)

<!--
FYI:
Grey's channels: CGPGrey, CGPGrey2, and greysfavs
Brady's channels: numberphile, Computerphile, sixtysymbols, periodicvideos, nottinghamscience, DeepSkyVideos, bibledex, wordsoftheworld, FavScientist, psyfile, BackstageScience, BradyStuff, and foodskey
-->
</body>
</html>
"""
def get_row(vid, creator):
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
	'published': vid.published.strftime('%B %d, %Y, %I:%M %p'),
	'url': 'http://youtu.be/' + vid.yt_id,
	'creator': creator,
	'views': ( \
	vid.viewcount if vid.viewcount >= 0 \
	else ("&lt;live video&gt;" if vid.viewcount==-1 \
	else ("&lt;not yet calculated&gt;" if vid.viewcount==-2 \
	else "&lt;error&gt;")))
	}

class MainHandler(Handler):
    def get(self):
        try:
        	bradyVids, greyVid, lastUpdate = load_front_data()
        	formatting_table = { }
        	formatting_table['number'] = len(bradyVids)
        	formatting_table['refresh_date'] = lastUpdate.strftime('%Y-%m-%d, %H:%M:%S UTC')
        	formatting_table['rows'] = '\n'.join([get_row(greyVid, "C.G.P. Grey")] + [get_row(vid, "Brady Haran") for vid in bradyVids[::-1]])
        	
        	self.write(page_template%formatting_table)
        except IndexError:
        	self.error(500)
        	self.write("I'm currently updating to add view counters.  Back in a bit :)<br><br>-Nicholas")
        

class UpdateHandler(Handler):
	def get(self):
		all_grey_vids = [ ]
		for channel in GREY_CHANNELS:
			all_grey_vids += youtube_integration.get_vids(channel,'GreyVideo')
		
		all_brady_vids = [ ]
		for channel in BRADY_CHANNELS:
			all_brady_vids += youtube_integration.get_vids(channel,'BradyVideo')
		
		
		all_grey_vids.sort(key=lambda vid:vid.published, reverse=True)
		latest_grey_vid = all_grey_vids[0]
		
		all_brady_vids.sort(key=lambda vid:vid.published, reverse=True)
		
		bradyVids = [vid for vid in all_brady_vids if vid.published > latest_grey_vid.published]
		greyVid = all_grey_vids[0]
		
		for e in db.GqlQuery("SELECT * FROM BradyVideo WHERE published <:1", latest_grey_vid.published):
			e.delete()
		
		already_added_ids = [ e.yt_id for e in list(db.GqlQuery("SELECT * FROM BradyVideo")) ]
		for e in bradyVids:
			if e.yt_id not in already_added_ids:
				e.put()
		
		for e in db.GqlQuery("SELECT * FROM GreyVideo"):
			e.delete()
		latest_grey_vid.viewcount = youtube_integration.get_view_count(latest_grey_vid.yt_id)
		latest_grey_vid.put()
		
		for e in db.GqlQuery("SELECT * FROM UpdateLog"):
			e.delete() 
		UpdateLog().put()
		
		time.sleep(1)
		
		for brady_vid in list(db.GqlQuery("SELECT * FROM BradyVideo")):
			brady_vid.viewcount = youtube_integration.get_view_count(brady_vid.yt_id)
			brady_vid.put()
		
		self.write('Database updated! <a href="/update_push">Push this update.</a>')

class UpdatePushHandler(Handler):
	def get(self):
		memcache.flush_all()
		load_front_data()
		
		self.write('Update pushed! <a href="/">Go back to the homepage.</a>')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/update/?',UpdateHandler),
    ('/update_push/?',UpdatePushHandler),
], debug=True)
