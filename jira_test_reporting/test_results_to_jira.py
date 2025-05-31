import configparser
import hashlib
import json
import os
from datetime import datetime
from jira import JIRA

testCreatedOrUpdatedAt = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000-0700')
regression_tag = "Regression"


def load_third_party_config():
    config = configparser.ConfigParser()
    config.read('_env_configs/third_party.conf')
    return config['DEFAULT']


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


def get_updated_test_tags_wrt_regression(previous_test_status: str, current_test_status: str, previous_test_tags: list):
    updated_test_tags = previous_test_tags
    # print(
    #     f"Inputs: previous_test_status='{previous_test_status}', current_test_status='{current_test_status}', previous_test_tags={previous_test_tags}")
    try:
        # if the test was passing earlier and it has failed now then its a regression
        if previous_test_status == "Passed" and current_test_status == "Failed":
            # print("Condition met: Test went from Passed to Failed, adding Regression")
            updated_test_tags.append(regression_tag)
        # if the test was failing earlier and it has passed now then its not a regression
        elif previous_test_status == "Failed" and current_test_status == "Passed":
            updated_test_tags.remove(regression_tag)
        # if the test is passing and if it still has regression label, just remove it
        elif current_test_status == "Passed" and regression_tag in updated_test_tags:
            updated_test_tags.remove(regression_tag)
        # if previous and current status matches and it was reported as a regression then its no more a regression
        elif previous_test_status == current_test_status and regression_tag in updated_test_tags:
            updated_test_tags.remove(regression_tag)
    except ValueError:
        pass

    # print(f"Updated tags: {updated_test_tags} ")
    return list(set(updated_test_tags))


def create_or_update_task(jira, jira_project_key, test_run_id, test_summary, test_description, test_type, test_area, test_run, test_env, test_tags, test_status):
    jira_custom_fields_map = load_third_party_config()
    issue_dict = {
        'project': {'key': jira_project_key},
        'summary': test_summary,
        'issuetype': {'name': 'Task'},
        jira_custom_fields_map['jira_field_id_test_env']: {'value': test_env},
        jira_custom_fields_map['jira_field_id_test_area']: {'value': test_area},
        jira_custom_fields_map['jira_field_id_test_type']: test_type,
        jira_custom_fields_map['jira_field_id_test_run_name']: test_run,
        'description': test_description,
        jira_custom_fields_map['jira_field_id_test_tags']: test_tags,
        jira_custom_fields_map['jira_field_id_test_status']: {'value': test_status},
        jira_custom_fields_map['jira_field_id_test_run_id']: test_run_id,
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
        # Update the test tags wrt. regression
        issue_dict[jira_custom_fields_map['jira_field_id_test_tags']] = get_updated_test_tags_wrt_regression(previous_test_status=str(getattr(
            existing_test_id.fields, jira_custom_fields_map['jira_field_id_test_status'], None)), current_test_status=test_status, previous_test_tags=getattr(existing_test_id.fields, jira_custom_fields_map['jira_field_id_test_tags'], None))
        # determine whether test failed because of a new reason
        if not is_test_description_matching(old_description=existing_test_id.fields.description, new_description=test_description):
            print(
                f"New failure identified for Test: {test_run_summary} | Test ID: {existing_test[0]}. Moving older description to comments.")
            jira.add_comment(
                existing_test[0], f"\nPreviously with Test Run ID: {getattr(
                    existing_test_id.fields, jira_custom_fields_map['jira_field_id_test_run_id'], None)}\n{existing_test_id.fields.description}")
        # Update the test details
        existing_test_id.update(fields=issue_dict)
        # Transition jira task to respective status
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
    # Following values need to be set as either environment variables OR repository variables if you're running this in CI/CD
    jira = JIRA({'server': os.environ.get('jira_host_url')}, basic_auth=(
        os.environ.get('jira_username'), os.environ.get('jira_password')))
    jira_project_key = os.environ.get('jira_project_key')
    report = parse_pytest_report(report_path)
    eligiblePytestMarkers = ['classificationAccuracyTest',
                             'dataIntegrityTest', 'skipOnLocal', 'graphql', 'RestAPIs', 'test_tag', regression_tag]
    test_type = report['tests'][0]['nodeid'].split('/')[0]
    # this configuration will be picked up from _env_config/third_party.conf
    third_party_config = load_third_party_config()
    build_url = f"{os.environ.get(third_party_config['scm_url_variable'])}/pipelines/results/{os.environ.get(third_party_config['scm_build_number_variable'])}" if os.environ.get(
        third_party_config['scm_url_variable']) else "Not Applicable"
    test_description_footer = f"\n*Build Number:* {os.environ.get(third_party_config['scm_build_number_variable'], 'Not Applicable')}\n*Build URL:* {build_url}\n"
    # Start processing every result
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
