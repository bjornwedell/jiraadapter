import datetime
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
        user = "a.user"
        start_date = "2020-01-01"
        end_date = "2020-03-01"
        issue1 = MagicMock()
        sum = 5467
        worklogs = [MagicMock()]
        self.handler.sum_of_worklogs.return_value = sum
        issue1.fields.worklog.worklogs = worklogs
        issues = [issue1]
        structure = self.handler.generate_worklog_structure(issues, user, start_date, end_date)
        self.assertEqual(sum,
                         structure[0]['hours_spent'])
        self.handler.sum_of_worklogs.assert_called_with(worklogs, user, start_date, end_date)


class TestSumOfWorklogs(TestCase):

    def setUp(self):
        self.handler = Handler(MagicMock())

    def test_should_sum_worklogs_and_convert_to_hours(self):
        secs1 = 3636
        secs2 = 2430
        worklogs = [MagicMock(), MagicMock()]
        worklogs[0].timeSpentSeconds = secs1
        worklogs[0].started = datetime.datetime.now().strftime("%Y-%m-%dT%h:%m%s")
        worklogs[1].timeSpentSeconds = secs2
        worklogs[1].started = datetime.datetime.now().strftime("%Y-%m-%dT%h:%m%s")

        self.assertEqual((secs1 + secs2) / 60 / 60, self.handler.sum_of_worklogs(worklogs))

    def test_should_only_include_worklogs_from_specified_user(self):
        secs1 = 3636
        user = 'the.user'
        worklogs = [MagicMock(), MagicMock()]
        worklogs[0].timeSpentSeconds = secs1
        worklogs[0].started = datetime.datetime.now().strftime("%Y-%m-%dT%h:%m%s")
        worklogs[0].author.name = user
        worklogs[1].timeSpentSeconds = 34215
        worklogs[1].started = datetime.datetime.now().strftime("%Y-%m-%dT%h:%m%s")
        worklogs[1].author.name = "other.user"
        self.assertEqual(secs1 / 60 / 60, self.handler.sum_of_worklogs(worklogs, user))

    def test_should_only_include_worklogs_before_end_date(self):
        secs1 = 3600
        endDate = datetime.datetime.now()
        workStartedDate = endDate - datetime.timedelta(days=2)
        workStartedDateOutside = endDate + datetime.timedelta(days=2)
        worklogs = [MagicMock(), MagicMock()]
        worklogs[0].timeSpentSeconds = secs1
        worklogs[0].started = workStartedDate.strftime("%Y-%m-%dT%h:%m%s")
        worklogs[1].timeSpentSeconds = 34215
        worklogs[1].started = workStartedDateOutside.strftime("%Y-%m-%dT%h:%m%s")
        self.assertEqual(secs1 / 60 / 60,
                         self.handler.sum_of_worklogs(worklogs, end_date=endDate.strftime("%Y-%m-%d")))

    def test_should_only_include_worklogs_after_start_date(self):
        secs1 = 3600
        startDate = datetime.datetime.now() - datetime.timedelta(days=2)
        workStartedDate = datetime.datetime.now()
        workStartedDateOutside = datetime.datetime.now() - datetime.timedelta(days=3)
        worklogs = [MagicMock(), MagicMock()]
        worklogs[0].timeSpentSeconds = secs1
        worklogs[0].started = workStartedDate.strftime("%Y-%m-%dT%h:%m%s")
        worklogs[1].timeSpentSeconds = 34215
        worklogs[1].started = workStartedDateOutside.strftime("%Y-%m-%dT%h:%m%s")
        self.assertEqual(secs1 / 60 / 60,
                         self.handler.sum_of_worklogs(worklogs, start_date=startDate.strftime("%Y-%m-%d")))
