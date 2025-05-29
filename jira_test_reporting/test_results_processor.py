import argparse
import uuid
from .test_results_to_jira import process_test_report
from .test_results_to_slack import send_slack_notification


def get_args():
    parser = argparse.ArgumentParser(
        description='Report pytest results to Jira and Slack.')
    parser.add_argument('--test-env', default='dev',
                        help='Test environment (e.g., dev, prod)')
    parser.add_argument('--test-run', default='Daily Run',
                        help='Test run identifier (e.g., regression-test-release-2b)')
    parser.add_argument('--report', default="test-reports/pytest_report.json",
                        help='Path to the pytest report file')
    return parser.parse_args()


def main():
    args = get_args()
    test_run_id = str(uuid.uuid4().hex)
    report = process_test_report(
        args.report, args.test_run.title(), args.test_env.title(), test_run_id=test_run_id)
    send_slack_notification(
        report, args.test_run.title(), args.test_env.title(), test_run_id=test_run_id)


if __name__ == '__main__':
    main()
