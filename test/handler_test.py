import datetime
import asyncio
from unittest import TestCase
from mock import MagicMock, patch
from app import Handler
from app import get_total_hours

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class TestTimes(TestCase):
    def setUp(self):
        self.handler = Handler(MagicMock())
        self.handler.sum_of_worklogs = MagicMock()
        self.handler.generate_worklog_structure = MagicMock()
        self.handler.jira = MagicMock()
        self.request = MagicMock()

    @patch('app.web')
    def test_handles_invalid_parameters(self, web_mock):
        response = MagicMock()
        web_mock.Response.return_value = response
        self.request.match_info = {}
        self.assertEqual(response, _run(self.handler.times(self.request)))
        web_mock.Response.assert_called_with(status=500)

    def test_uses_jira_to_search_for_issues(self):
        _run(self.handler.times(self.request))
        self.handler.jira.search_issues.assert_called()

    def test_builds_structure_with_result_from_jira(self):
        user = 'a.user'
        toDateString = '2020-01-01'
        fromDateString = '2020-02-01'
        self.request.match_info = {'user' : user,
                                   'toDateString':toDateString,
                                   'fromDateString':fromDateString}
        issues = MagicMock()
        self.handler.jira.search_issues.return_value = issues
        _run(self.handler.times(self.request))
        self.handler.generate_worklog_structure.assert_called_with(issues,
                                                                   user,
                                                                   toDateString,
                                                                   fromDateString)

class TestGenerateWorklogStructure(TestCase):

    def setUp(self):
        self.handler = Handler(MagicMock())
        self.handler.sum_of_worklogs = MagicMock()
        self.handler.epic = MagicMock()
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

    def test_include_epic(self):
        epic_key = "EPIC-123"
        self.handler.epic.return_value = epic_key
        issue1 = MagicMock()
        issues = [issue1]
        structure = self.handler.generate_worklog_structure(issues)
        self.assertEqual(epic_key, structure[0]['epic'])
        self.handler.epic.assert_called_with(issue1)

def seconds_to_hours(seconds):
    return seconds / 60 / 60

def create_worklog(start_datetime, seconds, user=None):
    worklog = MagicMock()
    if user:
        worklog.author.name = user
    if start_datetime:
        worklog.started = start_datetime.strftime("%Y-%m-%dT%h:%m%s")
    if seconds:
        worklog.timeSpentSeconds = seconds
    return worklog

class TestSumOfWorklogs(TestCase):

    def setUp(self):
        self.handler = Handler(MagicMock())
        self.date_format = "%Y-%m-%d"

    def test_should_sum_worklogs_and_convert_to_hours(self):
        secs1 = 3636
        secs2 = 2430
        worklogs = [create_worklog(datetime.datetime.now(), secs1),
                    create_worklog(datetime.datetime.now(), secs2)]

        self.assertEqual(seconds_to_hours(secs1 + secs2), self.handler.sum_of_worklogs(worklogs))

    def test_should_only_include_worklogs_from_specified_user(self):
        secs1 = 3636
        user = 'the.user'
        worklogs = [create_worklog(datetime.datetime.now(), secs1, user=user),
                    create_worklog(datetime.datetime.now(), 34215, user='other.user')]
        self.assertEqual(seconds_to_hours(secs1), self.handler.sum_of_worklogs(worklogs, user))

    def test_should_only_include_worklogs_from_specified_multiple_users(self):
        secs1 = 3636
        user1 = 'the.user1'
        secs2 = 3030
        user2 = 'the.user2'
        worklogs = [create_worklog(datetime.datetime.now(), secs1, user=user1),
                    create_worklog(datetime.datetime.now(), secs2, user=user2),
                    create_worklog(datetime.datetime.now(), 34215, user='other.user')]
        self.assertEqual(seconds_to_hours(secs1 + secs2), self.handler.sum_of_worklogs(worklogs, f"{user1}+{user2}"))

    def test_should_only_include_worklogs_before_end_date(self):
        secs1 = 3600
        endDate = datetime.datetime.now()
        worklogs = [create_worklog(endDate - datetime.timedelta(days=2), secs1),
                    create_worklog(endDate + datetime.timedelta(days=2), 34215)]
        self.assertEqual(seconds_to_hours(secs1),
                         self.handler.sum_of_worklogs(worklogs, end_date=endDate.strftime(self.date_format)))

    def test_should_only_include_worklogs_after_start_date(self):
        secs1 = 3600
        startDate = datetime.datetime.now() - datetime.timedelta(days=2)
        worklogs = [create_worklog(datetime.datetime.now(), secs1),
                    create_worklog(datetime.datetime.now() - datetime.timedelta(days=3), 34215)]
        self.assertEqual(seconds_to_hours(secs1),
                         self.handler.sum_of_worklogs(worklogs, start_date=startDate.strftime(self.date_format)))

class TestGetTotalHoursFunctions(TestCase):
    def test_should_raise_if_none(self):
        with self.assertRaises(ValueError):
            self.assertEqual(0, get_total_hours(None))

    def test_should_return_zero_if_no_issues(self):
        self.assertEqual(0, get_total_hours([]))

    def test_should_return_sum_of_worklog(self):
        issues = [{'hours_spent': 2},
                  {'hours_spent': 3}]
        self.assertEqual(5, get_total_hours(issues))

class TestEpic(TestCase):
    def setUp(self):
        self.handler = Handler(MagicMock())
        self.issue = MagicMock()
        self.epic_key = "EPIC-123"

    def test_should_return_epic_link_for_non_epic(self):
        self.issue.fields.issuetype = "Story"
        self.issue.fields.customfield_10006 = self.epic_key
        self.assertEqual(self.epic_key, self.handler.epic(self.issue))

    def test_should_return_key_epic(self):
        self.issue.fields.issuetype = "Epic"
        self.issue.key = self.epic_key
        self.assertEqual(self.epic_key, self.handler.epic(self.issue))
