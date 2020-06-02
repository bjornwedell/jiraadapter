from unittest import TestCase
from mock import MagicMock
from app import Handler


class TestGenerateWorklogStructure(TestCase):

    def setUp(self):
        self.handler = Handler(MagicMock())
        self.handler.sum_of_worklogs = MagicMock()
        self.handler.jira = MagicMock()

    def assert_issue_in_structure(self, issue, structure):
        for item in structure:
            if item['summary'] == issue.fields.summary:
                return
        self.assertFalse(True,
                         f"Issue {issue.fields.summary} should be in structure: {str(structure)}")

    def test_include_summary(self):
        issue1 = MagicMock()
        summary1 = "summary1"
        issue1.fields.summary = summary1
        issue2 = MagicMock()
        summary2 = "summary2"
        issue2.fields.summary = summary2
        issues = [issue1, issue2]
        structure = self.handler.generate_worklog_structure(issues)
        self.assert_issue_in_structure(issue1,
                                       structure)
        self.assert_issue_in_structure(issue2,
                                       structure)

    def test_include_sum_of_hours(self):
        issue1 = MagicMock()
        sum = 5467
        worklogs = [MagicMock()]
        self.handler.sum_of_worklogs.return_value = sum
        issue1.fields.worklog.worklogs = worklogs
        issues = [issue1]
        structure = self.handler.generate_worklog_structure(issues)
        self.assertEqual(sum,
                         structure[0]['hours_spent'])
        self.handler.sum_of_worklogs.assert_called_with(worklogs)


class TestSumOfWorklogs(TestCase):

    def setUp(self):
        self.handler = Handler(MagicMock())

    def test_should_sum_worklogs_and_convert_to_hours(self):
        secs1 = 3636
        secs2 = 2430
        worklogs = [MagicMock(), MagicMock()]
        worklogs[0].timeSpentSeconds = secs1
        worklogs[1].timeSpentSeconds = secs2

        self.assertEqual((secs1 + secs2) / 60 / 60, self.handler.sum_of_worklogs(worklogs))

# test_should_only_include_worklogs_from_specified_user
# test_should_only_include_worklogs_before_end_date
# test_should_only_include_worklogs_after_start_date
