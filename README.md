# slack-jira-sprint-updates
Bot which posts on slack recently finished tickets.

## Setup
To use bot you need to create file credentials.py where you'll put:
```
JIRA_API_URL = ''
JIRA_AUTHORIZATION = ''
SLACK_CHANNEL_ID = ''
SLACK_BOT_TOKEN = ''
SLACK_BOT_NAME = ''
```

## Running
All you need to do is go to `slack-jira-sprint-updates` dir and run:

`python diana_bot.py`

For now, it by default assumes releases are on Tuesdays and Thursdays.

## Options
If you want to see tickets from last couple of days, for example finished within last 10 days, run:

`python diana_bot.py -d 10` or `python diana_bot.py --days 10`

If you want to see tickets from particular project, for example Social, run:

`python diana_bot.py -p Social` or `python diana_bot.py --project Social`

## Integration with Slack
Go to channel you want to add the bot to and click: `Add a service integration` -> `Bots` -> `Add bot integration` and you'll get your `SLACK_BOT_TOKEN` needed to post a message.

## Schedule it!
To run task periodically, every fixed amount of time, use `cron`.

For example, to run scrypt every week from Monday to Thursday at 4p.m.:

* run `crontab -e` on machine you want to run the script on.
* paste following line:

`0 16 * * 1-4 python ~/slack-jira-sprint-updates/diana_bot.py`

