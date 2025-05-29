import configparser
import hashlib
import json
import os
from datetime import datetime
from jira import JIRA

testCreatedOrUpdatedAt = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000-0700')


def load_jira_config():
    config = configparser.ConfigParser()
    config.read('_env_configs/third-party.conf')
    return config['DEFAULT']


def connect_to_jira(config):
    options = {'server': config['jira_host_url']}
    return JIRA(options, basic_auth=(config['jira_username'], config['jira_password']))


def is_test_description_matching(old_description, new_description):
    old_description_filtered = [line for line in old_description.split(
        '\n') if not "Build Number" in line and not "Build URL" in line]
    new_description_filtered = [line for line in new_description.split(
        '\n') if not "Build Number" in line and not "Build URL" in line]
    old_description_hash = hashlib.sha1(
        str(old_description_filtered).encode()).hexdigest()
    new_description_hash = hashlib.sha1(
        str(new_description_filtered).encode()).hexdigest()
    return old_description_hash == new_description_hash


def create_or_update_task(jira, jira_project_key, test_run_id, test_summary, test_description, test_type, test_area, test_run, test_env, test_tags, test_status):
    issue_dict = {
        'project': {'key': jira_project_key},
        'summary': test_summary,
        'issuetype': {'name': 'Task'},
        'customfield_10208': {'value': test_env},
        'customfield_10236': {'value': test_area},
        'customfield_10301': test_type,
        'customfield_10205': test_run,
        'description': test_description,
        'customfield_10202': test_tags,
        'customfield_10235': {'value': test_status},
        'customfield_10269': test_run_id,
    }
    test_run_summary = f"Test Name: {test_area} | {test_summary} | Test Run ID: {test_run_id}"
    existing_test_search_query = f"""project = {jira_project_key} AND "Test Run[Short text]" ~ "\\\"{test_run}\\\"" AND type = Task AND "test environment[Dropdown]" = {test_env} AND "Test Area[Dropdown]" = "{test_area}" AND summary ~ "\\\"{test_summary}\\\"" ORDER BY createdDate DESC"""
    existing_test = jira.search_issues(
        existing_test_search_query, maxResults=1)
    if len(existing_test) == 0:
        test_id = jira.create_issue(fields=issue_dict)
        print(f"Created {test_run_summary} | Test ID: {test_id}")
        jira.transition_issue(test_id, test_status)
        return test_id
    else:
        existing_test_id = jira.issue(existing_test[0])
        if not is_test_description_matching(old_description=existing_test_id.fields.description, new_description=test_description):
            print(
                f"New failure identified for Test: {test_run_summary} | Test ID: {existing_test[0]}. Moving older description to comments.")
            jira.add_comment(
                existing_test[0], f"\nPreviously with Test Run ID: {existing_test_id.fields.customfield_10269}\n{existing_test_id.fields.description}")
        existing_test_id.update(fields=issue_dict)
        jira.transition_issue(existing_test_id, test_status)
        print(
            f"Updated Test: {test_run_summary} | Test ID: {existing_test[0]}")
        return existing_test[0]


def parse_pytest_report(report_path):
    try:
        with open(report_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Report file {report_path} not found")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in report file {report_path}")


def process_test_report(report_path, test_run, test_env, test_run_id):
    third_party_config = load_jira_config()
    jira = connect_to_jira(third_party_config)
    jira_project_key = third_party_config['jira_project_key']
    report = parse_pytest_report(report_path)
    eligiblePytestMarkers = ['classificationAccuracyTest',
                             'dataIntegrityTest', 'skipOnLocal', 'graphql', 'RestAPIs', 'only']
    test_type = report['tests'][0]['nodeid'].split('/')[0]
    build_url = f"{os.environ.get('BITBUCKET_GIT_HTTP_ORIGIN')}/pipelines/results/{os.environ.get('BITBUCKET_BUILD_NUMBER')}" if os.environ.get(
        "BITBUCKET_GIT_HTTP_ORIGIN") else "Not Applicable"
    test_description_footer = f"\n*Build Number:* {os.environ.get('BITBUCKET_BUILD_NUMBER', 'Not Applicable')}\n*Build URL:* {build_url}\n"

    for test in report['tests']:
        test_tags = []
        nodeid = test['nodeid'].replace('[', '-').replace(']', '')
        test_area = nodeid.split('/')[1].replace('_', ' ')
        test_name = nodeid.split(
            '::')[-1].replace('test_', '', 1).replace('_', ' ').capitalize().strip()
        test_status = test['outcome'].title()
        test_path = f"\n*Test Path*: {nodeid}"
        if test_status == "Passed":
            test_description = test_path
        elif test_status == "Failed":
            test_description = "\n*Failure Message:*\n{code}" + test.get('call', {}).get(
                'crash', {}).get('message', 'No failure message available') + "{code}" + test_path
        elif test_status == "Skipped":
            test_description = test_path
        test_description = test_description + test_description_footer
        if test.get('keywords'):
            test_tags.extend([label for label in test['keywords']
                             if label in eligiblePytestMarkers])
        create_or_update_task(jira=jira, jira_project_key=jira_project_key, test_run_id=test_run_id, test_summary=test_name, test_description=test_description, test_type=[test_type], test_area=test_area,
                              test_run=test_run, test_env=test_env, test_tags=test_tags, test_status=test_status)

    return report
