# fitness tracker - slack bot
This is the slack bot i built to gamify fitness and working out etc.

## requirements
Slack app tutorial: https://api.slack.com/docs/apps

Make sure you have the proper things enabled. Here are some tutorials I followed:
- https://api.slack.com/tutorials/tracks/responding-to-app-mentions
- https://api.slack.com/interactivity/slash-commands

```
pip install pygsheets python-dotenv slack_bolt aiohttp slack_sdk
```

It is linked pretty tightly to a spreadsheet, and I'll upload an example later.

## environment
.env file should look something like this:
```
SLACK_APP_TOKEN=xapp-12345
SLACK_BOT_TOKEN=xoxb-ABCDE
SPREADSHEET_KEY=abcde
SPREADSHEET_API_PRIVATE_KEY_LOCATION=./09876.json
```
## testing and launching
To test it, i created a private channel for myself and the bot where I could experiment with it.
I run it locally on my computer `python app.py` and then trigger it from slack.com.

To launch it I will attach it to a free instance of a [Web Service on render.com](https://docs.render.com/web-services)
