## Description
This repository contains utility scripts for
- reporting automated test results Jira
- sending a slack notification with proper stats and jira url that shows failed tests in the current test run id (trid)
specifically designed for use in CI/CD pipelines such as Bitbucket Pipelines.

## Prerequisites
- **Python**: Version 3.12 or higher.
- **Json Report**: Calling project should generate json report. How to [create pytest json report](https://pypi.org/project/pytest-json-report/)
- **Jira Access**: A Jira instance with API token authentication. How to [create jira api token](https://id.atlassian.com/manage-profile/security/api-tokens)
- **Slack Webhook**: A Slack webhook URL for sending notifications. How to [create slack incoming webhook](https://api.slack.com/messaging/webhooks#getting_started)
- **Configuration File**: A `_env_configs/third_party.conf` file with Jira and Slack settings.

## Installation
```pip install jira-test-reporting```

## Jira project preperation
### Create new Jira project and configure issue type "Task" with following fields
The script uses the following custom fields in Jira tasks:
- Test Environment : Field Type - Dropdown. ```Important - Pre-populate the values```
- Test Area : Field Type - Dropdown - ```Important - Pre-populate the values```
- Test Type : Field Type - Labels
- Test Run : Field Type - Short Text
- Test Tags : Field Type - Labels
- Test Status : Field Type - Dropdown ```Important - Pre-populate the values```
- TRID : Field Type - Short Text
### Important Instructions
- In the pytest json report check block ```"nodeid": "api_tests/Test_Pilot/test_jira_reporting_scenarios.py::Test_JIRA_Reporting_Scenarios::test_jira_reporting_test_passed",```
-- ```api_tests``` should be pre-populated under the Test Type field options
-- ```Test_Pilot``` should be pre-populated under the Test Area field options
- Similarly, in the pytest json report check block ```"outcome": "passed"```
-- ```Passed``` should be pre-populated under the Test Status field options. For this field, the values should be pre-populate in the title case.
- Also, make sure that in your jira project, the issue type "Task" has default fields Description and Status
- In the caller projetct, create `_env_configs/third_party.conf` file with the following structure:
    ```ini
    [DEFAULT]
    jira_field_id_test_env = customfield_10208
    jira_field_id_test_area = customfield_10236
    jira_field_id_test_type = customfield_10301
    jira_field_id_test_run_name = customfield_10205
    jira_field_id_test_tags = customfield_10202
    jira_field_id_test_status = customfield_10235
    jira_field_id_test_run_id = customfield_10269
    scm_url_variable = BITBUCKET_GIT_HTTP_ORIGIN
    scm_build_number_variable = BITBUCKET_BUILD_NUMBER
    ```

The script also uses the following default fields in Jira tasks:
- `project` - reflects ```jira_project_key```
- `summary` - test_name
- `description` - failure or passing description
- `status` - reflects test_status as in ```jira_field_id_test_status```

```
  The values for the fields above will be fetched directly from the json_report
  New jira tasks will be created for non-existing tests
  Existing tests will be updated
```

## Examples
### Jira Reported Tests Example
![image](https://github.com/user-attachments/assets/525b2aa7-99a8-4be9-8377-dbd260009230)

### Slack Notification Example
```
API Test Results
──────────────
🚀 *Test Run:* Release-X
🌎 *Environment:* Staging
❌ *Failed:* 4
──────────────
🧪 *Total Tests:* 148
✅ *Passed:* 143
🔄 *Executed:* 147
⏸️ *Skipped:* 1
📈 Click to open Test Report in Jira
📡 FYA: @User1 @User2
Execution Date: May-23-2025
```

## Usage
### Standalone
1. Ensure parameters in `_env_configs/third_party.conf` has valid values
2. Export environment variables as follows
```
export jira_host_url=https://my-jira-team.atlassian.net
export jira_username=whoami@my-jira-team.com
export jira_password=XXXXXXXXXXXXXXXXXXXXX
export jira_project_key=TMGT
export slack_dev_channel_webhook=https://hooks.slack.com/services/AAAAAA/BBBBBBB/CCCCCCCCC
export slack_prod_channel_webhook=https://hooks.slack.com/services/AAAAAA/BBBBBBB/CCCCCCCCC
export slack_test_webhook=https://hooks.slack.com/services/AAAAAA/BBBBBBB/CCCCCCCCC
```
3. Run the script with command-line arguments to process a pytest report:
```bash
python -m jira_test_reporting.test_results_processor --test-env=Dev --test-run=Release-X --report=sample-test-reports/pytest_report.json --notify-slack=yes
```
### CI-CD hooked example (this copies required files into your test_automation directory)
Assuming you have
- set `Repository Variables` (as in step #2 mentioned in the standalone setup above) in your scm tool. (How to: [bitbcket](https://support.atlassian.com/bitbucket-cloud/docs/variables-and-secrets/), [github](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables))
- configured pipeline in your SCM tool or a shell script in the caller project to execute the tests.
```bash
#!/bin/bash
# -----------------------------------------------------------------------------------------
# # Test Execution
# -----------------------------------------------------------------------------------------
.. pip install -r requirements.txt > /dev/null 2>&1
.. test execution code here
.. pytest -s --tb=no --no-header api_tests --testenv="$TEST_ENV" --json-report -v --json-report-indent=4 --json-report-omit collectors setup teardown --json-report-file=./test-reports/pytest_report.json
# JUST ADD FOLLOWING CODE BLOCK to report the issues
# -----------------------------------------------------------------------------------------
# Report test results to Jira
# -----------------------------------------------------------------------------------------
echo "Reporting test results into Jira and notifying slack"
if [ -n "$TEST_RUN_NAME" ]; then
    python -m jira_test_reporting.test_results_processor --test-env="$TEST_ENV" --test-run="$TEST_RUN_NAME"
else
    python -m jira_test_reporting.test_results_processor --test-env="$TEST_ENV"
fi
```

### Arguments

- `--test-env`: Test environment (default: `Dev`). Examples: `--test-env=dev`, `--test-env=stage`.
- `--test-run`: Test run identifier (default: `Daily Run`). Examples: `--test-run=Release-X`, `--test-run="Regression Tests"`.
- `--report`: Test report file path (default: `test-reports/pytest_report.json`). Examples: `--report=my-test-reports/my-pytest_report.json`
- `--notify-slack`: Whether or not you want to send out a notification to slack (default: `yes`). Examples: `--notify-slack=yes`, `--notify-slack=no`

## Troubleshooting

- **Jira Connection Errors**:
  - Verify `jira_host_url`, `jira_username`, and `jira_password` in `_env_configs/third_party.conf`.
  - Ensure the API token is valid and has “Create Issues” and “Edit Issues” permissions.
- **Slack Notification Failure**:
  - Check the webhook URL in the config file.
  - Ensure the Slack app is configured to allow incoming webhooks.
- **Pytest Report Issues**:
  - Confirm `test-reports/pytest_report.json` exists and contains valid JSON.
- **Custom Field Errors**:
  - Validate field IDs and allowed values in Jira Admin > Issues > Custom Fields.

## Contributing

Please read [CONTRIBUTE.md](https://github.com/sspatwardhan/jira-test-reporting/blob/main/CONTRIBUTE.md)

## License

This project is licensed under the MIT License. See `LICENSE` for details.
