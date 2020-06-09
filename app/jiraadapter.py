import asyncio
import datetime
import os

class JiraAdapter:
    def __init__(self, jira):
        self.jira = jira

    def search_issues(self, jql_string, fields, startAt, maxResults):
        results = self.jira.search_issues(jql_string, fields=fields, startAt=startAt, maxResults=maxResults)
        for issue in results:
            issue.fields.worklog.worklogs = self.jira.worklogs(issue.id)
        return results
