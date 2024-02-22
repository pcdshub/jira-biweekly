Add the keywords:

highlight:
lowlight:

to your comment on any Jira issue to include it in upcoming bi-weekly reports.

To use:
------------------
1. Generate a personal access token in Jira
2. Add the personal access token to a file called 'config.json' adjacent to this script with the following format:

`{"pat":"<your pat>"}`

3. Run the script `python .\jira-biweekly.py --assignee <your username> --format csv`
