import asyncio
import datetime
import os
from aiohttp import web
from jira import JIRA
from .jiraadapter import JiraAdapter
from .html_renderer import generate_page, generate_remainings


def get_total_hours(issues):
    if issues is None:
        raise ValueError('No issues passed')
    result = 0
    for issue in issues:
        result += sum(list(issue["hours_spent"].values()))
    return result

class Handler:
    def __init__(self, jira):
        self.jira = JiraAdapter(jira)

    def sum_of_worklogs(self, worklogs, user=None, end_date=None, start_date=None):
        users = []
        if user:
            users = user.split('+')
        sum_of_secs = 0
        try:
            end_date_time = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except TypeError as _e:
            end_date_time = datetime.datetime.now() + datetime.timedelta(days = 1)
        try:
            start_date_time = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        except TypeError as _e:
            start_date_time = datetime.datetime.now() - datetime.timedelta(weeks=1)
        for log in worklogs:
            try:
                started_time = datetime.datetime.strptime(log.started.split('T')[0], '%Y-%m-%d')
            except TypeError as _e:
                started_time = None
            if (log.author.name in users or len(users) == 0) \
               and started_time \
               and end_date_time >= started_time \
               and start_date_time <= started_time:
                sum_of_secs += log.timeSpentSeconds
        return sum_of_secs / 60 / 60

    def sum_of_worklogs_by_date(self, worklogs, user=None, end_date=None, start_date=None):
        try:
            end_date_time = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except TypeError as _e:
            end_date_time = datetime.datetime.now() + datetime.timedelta(days = 1)
        try:
            date_time = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        except TypeError as _e:
            date_time = datetime.datetime.now() - datetime.timedelta(weeks=1)
        ret = {}
        while date_time <= end_date_time:
            ret[date_time.strftime("%Y-%m-%d")] = self.sum_of_worklogs(worklogs, user, date_time.strftime("%Y-%m-%d"), date_time.strftime("%Y-%m-%d"))
            date_time = date_time + datetime.timedelta(days = 1)
        return ret

    def epic(self, issue):
        if str(issue.fields.issuetype) == 'Epic':
            return issue.key
        return issue.fields.customfield_10006

    def generate_worklog_structure(self, issues, user=None, end_date=None, start_date=None):
        return list(map(lambda issue: {'summary': issue.fields.summary,
                                       'hours_spent': self.sum_of_worklogs_by_date(issue.fields.worklog.worklogs, user, end_date, start_date),
                                       'epic': self.epic(issue),
                                       'key': issue.key,
                                       'parent': issue.fields.customfield_12504}, issues))


    async def times(self, request):
        user = None
        fromDateString = (datetime.datetime.now() - datetime.timedelta(weeks=1)).strftime("%Y-%m-%d")
        toDateString = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            user = request.match_info['user']
        except KeyError:
            return web.Response(status=500)
        try:
            fromDateString = request.match_info['fromDateString']
            toDateString = request.match_info['toDateString']
        except KeyError:
            pass
        issues = []
        issuesLenBefore = len(issues)
        page = 0
        while True:
            issues.extend(self.jira.search_issues(f"worklogDate <= {toDateString} AND worklogDate >= {fromDateString} AND worklogAuthor  in ({','.join(user.split('+'))})", fields=['summary', 'worklog','customfield_10006','issuetype','customfield_12504', 'parent'], startAt=page*50, maxResults=50))
            if len(issues) - issuesLenBefore < 50:
                break
            issuesLenBefore = len(issues)
            page += 1
        issues_list = self.generate_worklog_structure(issues, user, toDateString, fromDateString)
        return web.Response(text=generate_page(issues_list, user, fromDateString, toDateString, get_total_hours(issues_list)),
                            content_type='text/html')

    async def remaining(self, request):
        epicsString = None
        try:
            epicsString = request.match_info['epics']
        except KeyError:
            return web.Response(status=500)
        epics = epicsString.split('+')
        search_results = self.jira.search_issues(f"'Epic Link' in ({','.join(epics)}) OR issuekey in ({','.join(epics)})", fields=['summary', 'worklog','customfield_10006','issuetype','customfield_12504', 'parent','issuetype','timeestimate', 'timeoriginalestimate'], startAt=0, maxResults=300)
        epicsCollection = {}
        for epic in epics:
            filtered = list(filter(lambda i: i.key == epic, search_results))
            epicIssue = filtered and filtered[0]

            includedTasks = list(filter(lambda i: i.fields.customfield_10006 == epic, search_results))
            print(f"epic: {epicIssue}, tasks: {includedTasks}", flush = True)
            remainingWorkTasks = 0
            doneWorkTasks = 0
            for task in includedTasks:
                sum_task_logs = self.sum_of_worklogs(task.fields.worklog.worklogs, start_date="1978-11-21")
                print(f"task {task.key}: {sum_task_logs} {task.fields.worklog.worklogs}")
                doneWorkTasks += sum_task_logs
                if task.fields.timeestimate:
                    remainingWorkTasks += task.fields.timeestimate / 60 / 60
            if (epicIssue.fields.timeestimate or epicIssue.fields.timeestimate == 0):
                remainingWorkEpic = epicIssue.fields.timeestimate / 60 / 60
            else:
                remainingWorkEpic = (epicIssue.fields.timeoriginalestimate or 0) / 60 / 60
            doneWorkEpic = self.sum_of_worklogs(epicIssue.fields.worklog.worklogs)
            print(f"tasks: {remainingWorkTasks}", flush=True)
            print(f"epic: {remainingWorkEpic} {epicIssue.fields.timeestimate} {epicIssue.fields.timeoriginalestimate}", flush=True)
            print(doneWorkTasks, flush=True)
            remainingWork = remainingWorkEpic - doneWorkTasks
            if remainingWork < remainingWorkTasks:
                remainingWork = remainingWorkTasks
            epicsCollection[epic] = {}
            epicsCollection[epic]["remaining"] = remainingWork
            epicsCollection[epic]["summary"] = epicIssue.fields.summary
        return web.Response(text=generate_remainings(epicsCollection),
                            content_type='text/html')

async def http_main(host, port):
    app = web.Application(client_max_size=500_000_000)
    jira_url = os.environ.get('JIRA_URL', None)
    jira_user = os.environ.get('JIRA_USER', None)
    jira_pwd = os.environ.get('JIRA_PASSWORD', None)
    if not jira_url or not jira_user or not jira_pwd:
        print("You need JIRA_URL, JIRA_USER and JIRA_PASSWORD in your environment", flush=True)
        return 1
    options = {'server': jira_url}
    jira = JIRA(basic_auth=(jira_user, jira_pwd), options=options)
    handler = Handler(jira)

    app.add_routes([
        web.get('/times/{user}/{fromDateString}/{toDateString}',
                handler.times),
        web.get('/times/{user}/{fromDateString}/{toDateString}/',
                handler.times),
        web.get('/times/{user}/{fromDateString}',
                handler.times),
        web.get('/times/{user}/{fromDateString}/',
                handler.times),
        web.get('/times/{user}',
                handler.times),
        web.get('/times/{user}/',
                handler.times),
        web.get('/remaining/{epics}/',
                handler.remaining)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"HTTP: Serving on {host}:{port}", flush=True)

    while True:
        await asyncio.sleep(3600)


def serve():
    loop = asyncio.get_event_loop()

    # Initialize the HTTP server.
    loop.create_task(http_main("",
                               1337))

    loop.run_forever()
