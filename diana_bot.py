# coding=utf-8
import logging
import datetime
import requests
import sys
import getopt
import json
from urllib2 import urlopen
from bs4 import BeautifulSoup as bs
from credentials import SLACK_BOT_TOKEN,\
    JIRA_AUTHORIZATION,\
    JIRA_API_URL,\
    SLACK_TEST_CHANNEL_ID,\
    SLACK_BOT_NAME,\
    HOOK_URL_ADENG_BOTS,\
    HOOK_URL_WEEKLY_RELEASE,\
    TEST_HOOK_URL

def get_release_number_string(preview=False):
    domain = 'muppet.wikia.com'

    if preview:
        domain = 'preview.' + domain

    url = 'http://' + domain + '/wiki/Special:Version'
    html = bs(urlopen(url), "html.parser")

    for row in html.find_all('tr'):
        tds = row.find_all('td')
        if len(tds) == 2 and tds[0].text == 'Fandom code' and tds[1].text.startswith('release-'):
            version = tds[1].text
            return str(int(float(version.replace('release-', ''))))

class JiraController():
    def __init__(self):
        logging.basicConfig(level = logging.INFO)

    def get_tickets(self, release_number):
        """
        Gets the finished tickets statistics
        """
        response = []
        params = self.get_params()
        params['release_number'] = release_number

        finished_tickets = self.make_jira_request(params)

        if 'issues' in finished_tickets:
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
                        'fixVersion = "' + params['release_number'] + '" AND ' +
                        'type not in ("Product Design", Sub-task, Implementation-defect)'
                },
                headers = headers
            ).json()

        logging.info("\n\n*** Fetching data from preview. Relase: " + params['release_number'] + " for project " + params['project_name'] + ". ***\n\n")

        return response

    def get_params(self):
        project_name = 'ADEN'

        params = {
            'project_name': project_name
        }

        optlist, args = getopt.getopt(sys.argv[1:], "p:d:", ["project=", "days=", "test"])

        for option, arg in optlist:
            if option in ("-p", "--project") and arg != '--days':
                params['project_name'] = arg

        return params


class SlackUpdater(object):
    SLACK_API_URL = 'https://slack.com/api/chat.postMessage'

    def __init__(self, slack_hook_url = None, slack_bot_channel_name = None):
        params = sys.argv[1:]

        for param in params:
            if param == "--test":
                slack_bot_channel_name = '#diana-test'
                slack_hook_url = TEST_HOOK_URL
                break

        assert slack_hook_url is not None
        assert slack_bot_channel_name is not None

        self.slack_hook_url = slack_hook_url
        self.slack_bot_channel_name = slack_bot_channel_name

    def post_slack_message(self, text):
        response = requests.post(self.slack_hook_url,
                      data = {
                          'payload': json.dumps({"text": text, "channel": self.slack_bot_channel_name}),
                      })

        logging.info("\nPosting to Slack: done. Response: " + str(response.status_code))

    @staticmethod
    def prepare_slack_update(release_number, tickets, team = '*Ad Engineering*'):
        """
        Processes acquired results
        """
        if (len(tickets) == 0):
            return team + ' : Nothing to see here.'

        result = 'Preview version: *' + release_number + '*. Tickets below will be released tomorrow.'
        result += '```'

        for ticket in tickets:
            result += 'https://wikia-inc.atlassian.net/browse/' + ticket['key'] + ' ' + ticket['desc'] + '\n'

        return result + '```'


if __name__ == "__main__":
    calculation = JiraController()
    slack_updater_adeng = SlackUpdater(slack_hook_url = HOOK_URL_ADENG_BOTS, slack_bot_channel_name = '#adeng-bots')
    slack_updater_weekly_release = SlackUpdater(slack_hook_url = HOOK_URL_WEEKLY_RELEASE, slack_bot_channel_name = '#weekly-release-update')

    release_number = get_release_number_string(True)

    tickets = calculation.get_tickets(release_number)
    release_update = SlackUpdater.prepare_slack_update(release_number, tickets)

    slack_updater_adeng.post_slack_message(release_update)
    slack_updater_weekly_release.post_slack_message(release_update)
