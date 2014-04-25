import os
import urllib

from apiclient.discovery import build
from optparse import OptionParser

import json

import datetime
import time

from database_tables import *

REGISTRATION_INSTRUCTIONS = """
    You must set up a project and get an API key to run this code. Please see
    the instructions for creating a project and a key at <a
    href="https://developers.google.com/youtube/registering_an_application"
    >https://developers.google.com/youtube/registering_an_application</a>.
    <br><br>
    Make sure that you have enabled the YouTube Data API (v3) and the Freebase
    API for your project."""

# Set API_KEY to the "API key" value from the "Access" tab of the
# Google APIs Console http://code.google.com/apis/console#access
# Please ensure that you have enabled the YouTube Data API and Freebase API
# for your project.
with open('api_key.txt', 'r') as key_file:
	API_KEY = key_file.read()

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
FREEBASE_SEARCH_URL = "https://www.googleapis.com/freebase/v1/search?%s"
QUERY_TERM = "dog"



def get_view_count(vid_id):
	try:
		p = urllib.urlopen("https://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=json" % vid_id)
		json_data = p.read()
		p.close()
		json_data = json.loads(json_data)
		
		views = int(json_data['entry']['yt$statistics']['viewCount'])
		return views
	except KeyError:
		return -1 # For live videos
	except:
		return -3 # For misc. errors
	

def get_vids(input_channel_name, save_class='Video'):
  # Service for calling the YouTube API
  youtube = build(YOUTUBE_API_SERVICE_NAME,
                  YOUTUBE_API_VERSION,
                  developerKey=API_KEY)

  # Use form inputs to create request params for channel details
  channels_response = None
  
  channels_response = youtube.channels().list(
        forUsername=input_channel_name,
        part='snippet,contentDetails'
    ).execute()

  channel_name = ''
  videos = []

  for channel in channels_response['items']:
    uploads_list_id = channel['contentDetails']['relatedPlaylists']['uploads']
    channel_name = channel['snippet']['title']
    
    next_page_token = ''
    while next_page_token is not None:
      playlistitems_response = youtube.playlistItems().list(
          playlistId=uploads_list_id,
          part='snippet',
          maxResults=50,
          pageToken=next_page_token
      ).execute()

      for playlist_item in playlistitems_response['items']:
        videos.append(playlist_item)
        
      next_page_token = playlistitems_response.get('tokenPagination', {}).get(
          'nextPageToken')
      
      if len(videos) > 100:
        break
 
  return [ \
  	eval(save_class)(
  		title=e[u'snippet'][u'title'], \
  		channel=input_channel_name, \
  		published=(datetime.datetime.strptime(e[u'snippet'][u'publishedAt'][:-5],'%Y-%m-%dT%H:%M:%S')), \
  		yt_id=(e[u'snippet'][u'resourceId'][u'videoId']), \
  		viewcount=-2 \
  	) \
  for e in videos ]