#Brady vs. Grey

---

##API Key Hiding
To make sure that my own YouTube Data API key was not published, I separated it into a text file (`api_key.txt`) and used .gitignore to ensure that it wasn't published.

If you wish to create your own version of this, [get your own API key from Google](http://developers.google.com/youtube/v3/getting-started#intro), put this key in a file entitled `api_key.txt` and put it in the same directory as `youtube_integration.py`.


##The Updating Secret

I used a secret key (which is passed in as a query parameter to `/update` and `/update_push`) to ensure that the expensive database queries and network requests can only be triggered by myself and the app's cron jobs.

To do this yourself, put must

1. Devise your own secret. (I used [KeePass](http://keepass.info).)
2. Put it in a file entitled `update_secret.txt` in the same directory as `main.py`.
3. If you wish to have your application auto-update, make a file entitled `cron.yaml` with the code below.  [More info about cron.](https://developers.google.com/appengine/docs/python/config/cron)

<code>
cron:
- description: 4x daily update
  url: /update?secret=<your "secret">
  schedule: every 6 hours synchronized
- description: hourly push
  url: /update_push?secret=<your "secret">
  schedule: every 1 hours synchronized
</code>


##Enjoy!

You can view the running version [here](http://brady-vs-grey.appspot.com).