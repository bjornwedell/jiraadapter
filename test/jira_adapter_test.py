from unittest import TestCase
from mock import MagicMock
from app.jiraadapter import JiraAdapter


class TestSearch(TestCase):

    def setUp(self):
        self.jira = MagicMock()
        self.jira_adapter = JiraAdapter(self.jira)

    def test_calls_real_jira(self):
        jql_string = "jql string"
        fields = ["field1"]
        start = 51
        page_size = 50
        self.jira_adapter.search_issues(jql_string, fields=fields, startAt=start, maxResults=page_size)
        self.jira.search_issues.assert_called_with(jql_string, fields=fields, startAt=start, maxResults=page_size)

    def test_calls_worklog_for_issue_in_search_result(self):
        issue = MagicMock()
        issue_id = "FISK-123"
        issue.id = issue_id
        self.jira.search_issues.return_value = [ issue ]
        self.jira_adapter.search_issues(None, None, None, None)
        self.jira.worklogs.assert_called_with(issue_id)


    def test_returns_response_from_real_jira(self):
        return_value = MagicMock()
        self.jira.search_issues.return_value = return_value
        self.assertEqual(return_value, self.jira_adapter.search_issues("", [], 0, 50))
