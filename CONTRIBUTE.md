# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a 
   build.
2. Update the README.md with details of changes to the interface, this includes new environment 
   variables, exposed ports, useful file locations and container parameters.
3. Increase the version numbers in any examples files and the README.md to the new version that this
   Pull Request would represent. The versioning scheme we use is [SemVer](http://semver.org/).
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you 
   do not have permission to do that, you may request the second reviewer to merge it for you.

## Instructions
1. Clone the repository `git@github.com:sspatwardhan/jira-test-reporting.git` and create a new branch `git checkout -b feature/short-description` or `git checkout -b fix/short-description`
2. [Create and activate a python virtual environement](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
3. `Evaluate and review the design in your mind from the end-user perspective.`
4. Make the code changes
5. To test it locally
    1. Run `uv pip install -e .`
    2. Ensure parameters in `_env_configs/third_party.conf` has valid values as mentioned in [Important Instructions](https://github.com/sspatwardhan/jira-test-reporting?tab=readme-ov-file#important-instructions)
    3. Ensure `Repository Variables` are set up (as in step #2 mentioned in the [standalone setup](https://github.com/sspatwardhan/jira-test-reporting?tab=readme-ov-file#standalone))
    3. Run the script with command-line arguments to process a pytest report:
    ```bash
    python -m jira_test_reporting.test_results_processor --test-env=Dev --test-run=Release-X --report=sample-test-reports/pytest_report.json
    ```
6. If it all works, commit your code by [adding appropriate commit message](https://www.theserverside.com/video/Follow-these-git-commit-message-guidelines#:~:text=Write%20git%20commit%20messages%20imperatively,ethnocentricity%20built%20into%20this%20rule.)
7. Create a PR

## Code of Conduct
Please refer [Contributor Covenant][homepage], version 1.4, available at [http://contributor-covenant.org/version/1/4][version]

[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/


Thanks | Saurabh Patwardhan