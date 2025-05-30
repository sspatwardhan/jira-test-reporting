import json
import os
import requests
import string
from datetime import datetime
from .test_results_to_jira import load_third_party_config


def send_slack_message(slack_webhook_url, message_blocks):
    payload = {"blocks": message_blocks}
    response = requests.post(slack_webhook_url, data=json.dumps(
        payload), headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")
    else:
        print("Slack notification sent!")


def send_slack_notification(report, test_run, test_env, test_run_id):
    third_party_config = load_third_party_config()
    test_type = report['tests'][0]['nodeid'].split('/')[0]
    build_url = f"{os.environ.get(third_party_config['scm_url_variable'])}/pipelines/results/{os.environ.get(third_party_config['scm_build_number_variable'])}" if os.environ.get(
        third_party_config['scm_url_variable']) else "Not Applicable"
    report_url = f"{os.environ.get('jira_host_url')}/issues/?jql=project%20%3D%20TMGT%20AND%20%22trid%5BShort%20text%5D%22%20~%20%22{test_run_id}%22%20AND%20%22test%20status%5BDropdown%5D%22%20IN%20(Failed%2C%20Skipped)%20ORDER%20BY%20status%20ASC"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{string.capwords(test_type.replace('_', ' '))} Results",
                "emoji": True
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🚀 *Test Run:* {test_run}\n"
                        f"🌎 *Environment:* {test_env}\n"
                        f"❌ *Failed:* {report.get('summary', {}).get('failed', 0)}\n"
                        f"📈 Click to open <{report_url}|Test Report> in Jira\n"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🧪 *Total Tests:* {report.get('summary', {}).get('total', 0)}\n"
                        f"✅ *Passed:* {report.get('summary', {}).get('passed', 0)}\n"
                        f"🔄 *Executed:* {report.get('summary', {}).get('collected', 0)}\n"
                        f"⏸️ *Skipped:* {report.get('summary', {}).get('deselected', 0)}\n"
                        f"🛠️ Click to open <{build_url}|Build {os.environ.get('BITBUCKET_BUILD_NUMBER', '-')}>\n"
                        f"📡 FYA: <@U07F4HJFT63>" if test_type == "api_tests" else "📡 FYA: <@U07UQKM5YE9>"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Execution Date: _{datetime.fromtimestamp(report.get('created', 0)).strftime('%b-%d-%Y')}_"
                }
            ]
        }
    ]

    slack_webhook_url = os.environ.get('slack_test_webhook') if test_run != 'Daily Run' else os.environ.get(
        'slack_dev_channel_webhook') if test_env.lower() == 'dev' else os.environ.get('slack_prod_channel_webhook')
    send_slack_message(slack_webhook_url=slack_webhook_url,
                       message_blocks=blocks)
