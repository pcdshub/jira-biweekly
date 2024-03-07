import requests
import json
import re
import csv
import argparse
from datetime import datetime, timedelta, timezone

# Load the PAT from the config file
with open('config.json', 'r') as file:
    config = json.load(file)
pat = config['pat']

# Function to fetch issues from Jira
def fetch_issues(jira_server_url, project_keys, pat, assignee):
    headers = {
       "Accept": "application/json",
       "Content-Type": "application/json",
       "Authorization": "Bearer " + pat
    }
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).strftime("%Y-%m-%d")
    jql_query = f'project in ({",".join(project_keys)}) AND assignee = {assignee} AND updated >= {two_weeks_ago}'
    response = requests.get(
       f'{jira_server_url}/rest/api/2/search?jql={jql_query}',
       headers=headers
    )
    return response.json()['issues']

# Function to check if a comment date is within the last 2 weeks
def is_recent(comment_date):
    comment_datetime = datetime.strptime(comment_date, "%Y-%m-%dT%H:%M:%S.%f%z")
    return datetime.now(timezone.utc) - comment_datetime <= timedelta(weeks=2)

def process_issues(issues, jira_server_url, pat):
    report_data = []
    for issue in issues:
        issue_key = issue['key']
        title = issue['fields']['summary']
        description = issue['fields']['description'] or 'No description available'
        participants = set()
        highlights, lowlights = [], []

        # Add reporter and assignee to participants
        participants.add(issue['fields']['reporter']['displayName'])
        if issue['fields']['assignee']:
            participants.add(issue['fields']['assignee']['displayName'])
        
        # Get and add watchers to participants
        watchers_response = requests.get(
            f'{jira_server_url}/rest/api/2/issue/{issue_key}/watchers',
            headers={"Authorization": "Bearer " + pat}
        )
        watchers_data = watchers_response.json()
        for watcher in watchers_data['watchers']:
            participants.add(watcher['displayName'])

        # Get comments
        comments_response = requests.get(
            f'{jira_server_url}/rest/api/2/issue/{issue_key}/comment',
            headers={"Authorization": "Bearer " + pat}
        )
        for comment in comments_response.json()['comments']:
            if is_recent(comment['created']):
                participants.add(comment['author']['displayName'])
                comment_body = comment['body']
                if re.search(r'highlights?', comment_body, re.IGNORECASE):
                    highlights.append(comment_body)
                elif re.search(r'lowlights?', comment_body, re.IGNORECASE):
                    lowlights.append(comment_body)

        # Include issue only if it has recent highlights or lowlights
        if highlights or lowlights:
            report_data.append({
                'ticket_number': issue_key,
                'title': title,
                'description': description,
                'participants': ', '.join(participants),
                'highlights': ' | '.join(highlights),
                'lowlights': ' | '.join(lowlights)
            })
    return report_data

def output_report(report_data, format):
    if format == 'csv':
        with open('report.csv', 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['ticket_number', 'title', 'description', 'participants', 'highlights', 'lowlights'])
            writer.writeheader()
            for row in report_data:
                writer.writerow(row)
    else:  # Default to print
        for row in report_data:
            print(f"Ticket Number: {row['ticket_number']}, Title: {row['title']}, Description: {row['description']}, Participants: {row['participants']}, Highlights: {row['highlights']}, Lowlights: {row['lowlights']}")


# CLI argument parsing
parser = argparse.ArgumentParser(description="Generate a Jira report.")
parser.add_argument('--assignee', required=True, help="Assignee for the issues.")
parser.add_argument('--format', choices=['csv', 'print'], default='print', help="Output format: csv or print.")
args = parser.parse_args()

# Main script logic
jira_server_url = 'https://jira.slac.stanford.edu'
project_keys = ['ECS']  # Replace with your project keys

issues = fetch_issues(jira_server_url, project_keys, pat, args.assignee)
report_data = process_issues(issues, jira_server_url, pat)
output_report(report_data, args.format)