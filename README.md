#Brady vs. Grey

##The `.gitignore` File
I have listed a few files in `.gitignore` to avoid the publication of my API key and the possibility of other people's initiating of expensive update requests.
If you wish to run this project yourself, you will need to use this README to create your own files.
These hidden files are `api_key.txt`, `update_secret.txt`, and `cron.yaml` (optional).

##API Key Hiding (`api_key.txt`)
To make sure that my own YouTube Data API key was not published,
I separated it into a text file (`api_key.txt`) and used `.gitignore` to ensure that it wasn't published.

If you wish to do this yourself, you must

1. [Get your own API key from Google](http://developers.google.com/youtube/v3/getting-started#intro).
2. Put this key in a file entitled `api_key.txt`.
3. Put this file in the same directory as `youtube_integration.py`.


##The Updating Secret (`update_secret.txt` and `cron.yaml`)

I used a secret key, which must be passed in as a query parameter to `/update` and `/update_push` to avoid a 400 response;
this ensures that the expensive database queries and network requests can only be triggered by myself and the app's cron jobs.

To do this yourself, put must

1. Devise your own secret. (I used [KeePass](http://keepass.info).)
2. Put it in a file entitled `update_secret.txt` in the same directory as `main.py`.
3. If you wish to have your application auto-update, make a file entitled `cron.yaml` with the code below (replacing `<your secret>` with your actual secret). [More info about cron.](https://developers.google.com/appengine/docs/python/config/cron)
<pre><code>
cron:
- description: 4x daily update
  url: /update?secret=&lt;your secret&gt;
  schedule: every 6 hours synchronized
- description: hourly push
  url: /update_push?secret=&lt;your secret&gt;
  schedule: every 1 hours synchronized
</code></pre>

##Enjoy!

You can view the running version [here](http://brady-vs-grey.appspot.com).