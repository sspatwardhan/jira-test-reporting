import argparse
import uuid
from .test_results_to_jira import process_test_report
from .test_results_to_slack import send_slack_notification


def get_args():
    parser = argparse.ArgumentParser(
        description='Report pytest results to Jira and Slack.')
    parser.add_argument('--test-env', default='dev',
                        help='example: --test-env=dev)')
    parser.add_argument('--test-run', default='Daily Run',
                        help='example: --test-run=regression-test-release-2b)')
    parser.add_argument('--report', default="test-reports/pytest_report.json",
                        help='example: --report=test-reports/pytest_report.json')
    parser.add_argument('--notify-slack', default="yes",
                        help='example: --notify-slack=yes or no')
    return parser.parse_args()


def main():
    args = get_args()
    test_run_id = str(uuid.uuid4().hex)
    report = process_test_report(
        args.report, args.test_run.title(), args.test_env.title(), test_run_id=test_run_id)
    if args.notify_slack.lower() == 'yes':
        send_slack_notification(report, args.test_run.title(
        ), args.test_env.title(), test_run_id=test_run_id)


if __name__ == '__main__':
    main()
