import asyncio
import datetime
import os

class JiraAdapter:
    def __init__(self, jira):
        self.jira = jira

    def find_all_parents(self, results, jql_string, fields, startAt, maxResults):
        # THIS CRAP IS NEEDED SINCE customfield_12504 seems broken in server
        results_with_project = self.jira.search_issues(jql_string, fields=['project'], startAt=startAt, maxResults=maxResults)
        if not results_with_project:
            return []
        projects = set(map(lambda i: i.fields.project.id, results_with_project))
        maxNumberOfParents = 0
        parents = []
        while maxNumberOfParents is len(parents):
            maxNumberOfParents += 20
            parents = list(filter(lambda i: i.fields.subtasks, self.jira.search_issues(f"project in ({','.join(projects)}) AND issuetype not in (Epic, Sub-task) ORDER BY subtasks", fields=fields + ['subtasks'], maxResults=maxNumberOfParents)))
        parents_to_include = []
        for issue in results:
            if str(issue.fields.issuetype) == 'Sub-task':
                parent = list(filter(lambda i : list(filter(lambda st: st.key == issue.key, i.fields.subtasks)), parents))
                if parent:
                    issue.fields.customfield_12504 = parent[0].key
                    if not list(filter(lambda i: i.key == parent[0].key, results + parents_to_include)):
                        parents_to_include += [parent[0]]
        return parents_to_include

    def search_issues(self, jql_string, fields, startAt, maxResults):
        results = self.jira.search_issues(jql_string, fields=fields, startAt=startAt, maxResults=maxResults)

        parents = self.find_all_parents(results, jql_string, fields, startAt, maxResults)
        if parents:
            results += parents
        for issue in results:
            issue.fields.worklog.worklogs = self.jira.worklogs(issue.id)
        return results
