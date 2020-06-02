import asyncio
import datetime
import os
from aiohttp import web
from jira import JIRA

def totalLoggedHours(worklog):
    ret = 0
    for entry in worklog:
        ret += entry.timeSpent
    return ret

class Handler:
    def __init__(self, jira):
        self.jira = jira

    async def times(self, request):
        user = request.match_info['user']
        fromDateString = request.match_info['fromDateString']
        toDateString = request.match_info['toDateString']
        issues = self.jira.search_issues(f"worklogDate <= {toDateString} AND worklogDate >= {fromDateString} AND worklogAuthor  in ({user})", fields=['summary', 'worklog'])
        string = ""
        n = 0
        for issue in issues:
            worklogs = filter(lambda wl: wl.author.name == user, issue.fields.worklog.worklogs)
            string += "<h1>" + issue.fields.summary + "</h1>"
            timespent = 0
            for logs in worklogs:
                toDate = datetime.datetime.strptime(toDateString, '%Y-%m-%d')
                fromDate = datetime.datetime.strptime(fromDateString, '%Y-%m-%d')
                logStarted = datetime.datetime.strptime(logs.started.split('T')[0],
                                                    '%Y-%m-%d')
                if logStarted <= toDate and logStarted >= fromDate:
                    timespent += logs.timeSpentSeconds
            string += "<h3>" + str(timespent / 60 / 60) + " hours</h3>"

        return web.Response(text=f"""
<html>
    <head><title>JIRA Timetable</title></head>
    <h1>{user} from {fromDateString} to {toDateString}</h1>
    {string}
</html>
    """,
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
