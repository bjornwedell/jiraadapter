import asyncio
import datetime
import os
from aiohttp import web
from jira import JIRA
from .jiraadapter import JiraAdapter
from .html_renderer import generate_page

def get_total_hours(issues):
    if issues is None:
        raise ValueError('No issues passed')
    result = 0
    for issue in issues:
        result += issue['hours_spent']
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
            if log.author.name in users or len(users) == 0 \
               and started_time \
               and end_date_time >= started_time \
               and start_date_time <= started_time:
                sum_of_secs += log.timeSpentSeconds
        return sum_of_secs / 60 / 60

    def epic(self, issue):
        if str(issue.fields.issuetype) == 'Epic':
            return issue.key
        return issue.fields.customfield_10006

    def generate_worklog_structure(self, issues, user=None, end_date=None, start_date=None):
        return list(map(lambda issue: {'summary': issue.fields.summary,
                                       'hours_spent': self.sum_of_worklogs(issue.fields.worklog.worklogs, user, end_date, start_date),
                                       'epic': self.epic(issue)}, issues))


    async def times(self, request):
        user = None
        fromDateString = None
        toDateString = None
        try:
            user = request.match_info['user']
            fromDateString = request.match_info['fromDateString']
            toDateString = request.match_info['toDateString']
        except KeyError:
            return web.Response(500)
        issues = self.jira.search_issues(f"worklogDate <= {toDateString} AND worklogDate >= {fromDateString} AND worklogAuthor  in ({','.join(user.split('+'))})", fields=['summary', 'worklog','customfield_10006','issuetype'])
        issues_list = self.generate_worklog_structure(issues, user, toDateString, fromDateString)
        return web.Response(text=generate_page(issues_list, user, fromDateString, toDateString, get_total_hours(issues_list)),
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
                handler.times)
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
