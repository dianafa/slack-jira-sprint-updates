# coding=utf-8
import logging
import datetime
import requests
import sys
import getopt
from credentials import SLACK_BOT_TOKEN,\
    JIRA_AUTHORIZATION,\
    JIRA_API_URL,\
    SLACK_CHANNEL_ID,\
    SLACK_TEST_CHANNEL_ID,\
    SLACK_BOT_NAME

days_count = {
    0: '5', #Monday
    1: '1', #Tue
    2: '2', #Wed
    3: '1', #Thu
    4: '2', #Fri
    5: '3', #Sat
    6: '4'  #Sunday
}

class JiraController():
    def __init__(self):
        logging.basicConfig(level = logging.INFO)

    def get_tickets(self):
        """
        Gets the finished tickets statistics
        """
        response = []
        params = self.get_params()

        finished_tickets = self.make_jira_request(params)

        for ticket in finished_tickets['issues']:
            response.append({
                "key" : ticket['key'],
                "desc" : ticket['fields']['summary']
            })

        return response

    def make_jira_request(self, params):
        headers = {
            'contentType': 'application/json',
            'Authorization': JIRA_AUTHORIZATION
        }

        response = requests.get(
                JIRA_API_URL,
                params = {
                    'jql':
                        'project="' + params['project_name'] + '" AND ' +
                        'resolved >= -' + params['days_before'] + 'd AND ' +
                        'resolved <= startOfDay() AND ' +
                        'status was in (QA, "Code Review") AND ' +
                        'type not in ("Product Design", Sub-task, Implementation-defect)'
                },
                headers = headers
            ).json()

        logging.info("\n\n*** Fetching data from last " + params['days_before'] + " days for project " + params['project_name'] + ". ***\n\n")

        return response

    def get_params(self):
        project_name = 'West Wing'
        today = datetime.datetime.today().weekday()

        print today
        params = {
            'project_name': project_name,
            'days_before': days_count[today]
        }

        optlist, args = getopt.getopt(sys.argv[1:], "p:d:", ["project=", "days=", "test"])

        for option, arg in optlist:
            if option in ("-p", "--project") and arg != '--days':
                params['project_name'] = arg
            if option in ("-d", "--days") and arg.isdigit():
                params['days_before'] = arg

        return params


class SlackUpdater(object):
    SLACK_API_URL = 'https://slack.com/api/chat.postMessage'

    def __init__(self, slack_bot_token = None, slack_bot_channel = SLACK_CHANNEL_ID):
        params = sys.argv[1:]

        for param in params:
            if param == "--test":
                slack_bot_channel = SLACK_TEST_CHANNEL_ID
                break

        assert slack_bot_token is not None
        assert slack_bot_channel is not None

        self.slack_bot_token = slack_bot_token
        self.slack_bot_channel = slack_bot_channel

    def post_slack_message(self, payload):
        response = requests.post(self.SLACK_API_URL,
                      data = {
                          'channel': self.slack_bot_channel,
                          'token': self.slack_bot_token,
                          'text': payload,
                          'username': SLACK_BOT_NAME
                      })

        logging.info("\nPosting to Slack: done")

    def prepare_slack_update(self, tickets, team = '*Fan Knowledge West- Wing*'):
        """
        Processes acquired results
        """
        if (len(tickets) == 0):
            return team + ' :Nothing user facing'

        result = '```'

        for ticket in tickets:
            result += 'https://wikia-inc.atlassian.net/browse/' + ticket['key'] + ' ' + ticket['desc'] + '\n'

        return result + '```'


if __name__ == "__main__":
    calculation = JiraController()
    slack_updater = SlackUpdater(slack_bot_token = SLACK_BOT_TOKEN)

    tickets = calculation.get_tickets()
    release_update = slack_updater.prepare_slack_update(tickets)
    slack_updater.post_slack_message(release_update)
