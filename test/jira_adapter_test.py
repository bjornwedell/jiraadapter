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
        self.jira_adapter.search_issues(jql_string, fields=fields)
        self.jira.search_issues.assert_called_with(jql_string, fields=fields)

    def test_returns_response_from_real_jira(self):
        return_value = "something"
        self.jira.search_issues.return_value = return_value
        self.assertEqual(return_value, self.jira_adapter.search_issues("", []))
