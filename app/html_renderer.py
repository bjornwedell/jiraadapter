import os

jira_url = os.environ.get('JIRA_URL', "no.url.given")

def create_link_to_issue(issue_key):
    return f'<a href="{jira_url}/browse/{issue_key}">{issue_key}</a>'

def generate_page(structure, user, fromDateString, toDateString, totalTimeSpent):
    epics = set(map(lambda issue: issue["epic"], structure))
    issuesHtml = ""
    for epic in epics:
        if not epic:
            continue
        spentOnEpic = 0
        issuesHtml += '<hr>'
        issuesHtml += f'<p><b>{create_link_to_issue(epic)}:</b></p>'
        issuesHtml += '<table>'
        for issue in list(filter(lambda issue: issue['epic']==epic,structure)):
            issuesHtml += '<tr>'
            issuesHtml += f'<td>{create_link_to_issue(issue["key"])}:{issue["summary"]}</td>'
            issuesHtml += f'<td>{issue["hours_spent"]} hours</td>'
            issuesHtml += '</tr>'
            spentOnEpic += issue["hours_spent"]
        issuesHtml += '</table>'
        issuesHtml += f'<p><b>Total epic hours:</b> {spentOnEpic}</p>'
    issuesHtml += '<hr>'
    issuesHtml += f'<p><b>Issues outside epics:</b></p>'
    issuesHtml += '<table>'
    for issue in list(filter(lambda issue: not issue['epic'],structure)):
        issuesHtml += '<tr>'
        issuesHtml += f'<td>{issue["summary"]}</td>'
        issuesHtml += f'<td>{issue["hours_spent"]} hours</td>'
        issuesHtml += '</tr>'
    issuesHtml += '</table>'
    issuesHtml += f'<p><b>Total hours:</b> {totalTimeSpent}</p>'
    css = """
    body {font-family: sans-serif;}
    """
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
