import datetime
import os

jira_url = os.environ.get('JIRA_URL', "no.url.given")

def create_link_to_issue(issue_key):
    return f'<a href="{jira_url}/browse/{issue_key}">{issue_key}</a>'

css = """
body {font-family: sans-serif;}
.indent {margin-left: 30px;}
"""

def hours_spent_on_issue(issue, structure):
    ret = sum(list(issue["hours_spent"].values()))
    for sub_task in list(filter(lambda task: issue["key"]==task["parent"],structure)):
        ret += sum(list(sub_task["hours_spent"].values()))
    return ret

def hours_spent_on_issue_by_date(issue, date_string, structure):
    ret = issue["hours_spent"][date_string]
    for sub_task in list(filter(lambda task: issue["key"]==task["parent"],structure)):
        ret += sub_task["hours_spent"][date_string]
    return ret

def generate_page(structure, user, fromDateString, toDateString, totalTimeSpent):
    dates=[]
    end_date_time = datetime.datetime.strptime(toDateString, '%Y-%m-%d')
    date_time = datetime.datetime.strptime(fromDateString, '%Y-%m-%d')
    while date_time <= end_date_time:
        dates += [date_time.strftime("%Y-%m-%d")]
        date_time = date_time + datetime.timedelta(days = 1)
    epics = set(map(lambda issue: issue["epic"], structure))
    issuesHtml = ""
    issuesHtml += '<hr>'
    issuesHtml += '<div class="indent"><table>'
    issuesHtml += '<tr>'
    issuesHtml += '<td>dates -> </td>'
    for date in dates:
        issuesHtml += f'<td>{date}</td>'
    issuesHtml += f'<td>Total for period</td>'
    issuesHtml += '</tr>'
    spentPerDay = list(map(lambda date: 0, dates))
    for epic in epics:
        if not epic:
            continue
        spentOnEpics = list(map(lambda date: 0, dates))
        issuesHtml += '<tr>'
        issuesHtml += f'<td><b>Epic {create_link_to_issue(epic)}</b></td><td></td>'
        issuesHtml += '</tr>'
        for issue in list(filter(lambda issue: issue['epic']==epic and not issue["parent"], structure)):
            issuesHtml += '<tr>'
            issuesHtml += f'<td>{create_link_to_issue(issue["key"])}: {issue["summary"]}</td>'
            idx = 0
            for date in dates:
                hours_spent = hours_spent_on_issue_by_date(issue, date, structure)
                issuesHtml += f'<td>{hours_spent} hours</td>'
                spentOnEpics[idx] += hours_spent
                spentPerDay[idx] += hours_spent
                idx += 1
            issuesHtml += '</tr>'
        issuesHtml += '<tr>'
        issuesHtml += f'<td><b>Total epic hours:</b></td>'
        for spentOnEpic in spentOnEpics:
            issuesHtml += f'<td><b>{spentOnEpic}</b></td>'
        issuesHtml += f'<td><b>{sum(spentOnEpics)}</b></td>'
        issuesHtml += '</tr><tr><td><hr></td></tr>'
    issuesHtml += '<hr>'
    issues_outside_epics = list(filter(lambda issue: not issue['epic'] and not issue["parent"], structure))
    if issues_outside_epics:
        issuesHtml += '<tr>'
        issuesHtml += f'<td><b>Issues outside epics:</b></td>'
        issuesHtml += '</tr>'
        for issue in issues_outside_epics:
            issuesHtml += '<tr>'
            issuesHtml += f'<td>{create_link_to_issue(issue["key"])}: {issue["summary"]}</td>'
            idx = 0
            spent_in_period = 0
            for date in dates:
                hours_spent = hours_spent_on_issue_by_date(issue, date, structure)
                issuesHtml += f'<td>{hours_spent} hours</td>'
                spentPerDay[idx] += hours_spent
                spent_in_period += hours_spent
                idx += 1
            issuesHtml += f'<td>{spent_in_period}</td>'
            issuesHtml += '</tr>'
    issuesHtml += '</tr><tr><td><hr></td></tr>'
    issuesHtml += '<tr><td><b>Total time per day:</b></td>'
    for spent in spentPerDay:
        issuesHtml += f'<td><b>{spent} hours</b></td>'
    issuesHtml += '</tr></table></div>'
    issuesHtml += f'<p><b>Total hours:</b> {totalTimeSpent} = {totalTimeSpent/8} workdays</p>'
    return f"""
<html>
<head>
  <title>JIRA Timetable</title>
  <style>{css}</style>
</head>
<h1>{user} from {fromDateString} to {toDateString}</h1>
{issuesHtml}
</html>
"""

def generate_remainings(epics):
    totRemaining = 0
    issuesHtml = ""
    for epic in epics:
        issuesHtml += '<hr>'
        issuesHtml += f'<h3>Epic {create_link_to_issue(epic)} {epics[epic]["summary"]} :  {epics[epic]["remaining"]} hours remaining</h3>'
        issuesHtml += '<div class="indent"><table>'
        issuesHtml += '</table></div>'
        totRemaining += epics[epic]["remaining"]
    issuesHtml += f"<h3>Totally remaining {totRemaining} hours = {totRemaining/8} work days.</h3>"
    return f"""
<html>
<head>
  <title>JIRA Epics remainings</title>
  <style>{css}</style>
</head>
<h1>Remaining work on epics</h1>
{issuesHtml}
</html>
"""
