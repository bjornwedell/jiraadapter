import os

jira_url = os.environ.get('JIRA_URL', "no.url.given")

def create_link_to_issue(issue_key):
    return f'<a href="{jira_url}/browse/{issue_key}">{issue_key}</a>'

def hours_spent_on_issue(issue, structure):
    ret = issue["hours_spent"]
    return ret

def generate_page(structure, user, fromDateString, toDateString, totalTimeSpent):
    epics = set(map(lambda issue: issue["epic"], structure))
    issuesHtml = ""
    for epic in epics:
        if not epic:
            continue
        spentOnEpic = 0
        issuesHtml += '<hr>'
        issuesHtml += f'<h3>Epic {create_link_to_issue(epic)}</h3>'
        issuesHtml += '<div class="indent"><table>'
        for issue in list(filter(lambda issue: issue['epic']==epic,structure)):
            issuesHtml += '<tr>'
            issuesHtml += f'<td>{create_link_to_issue(issue["key"])}: {issue["summary"]}</td>'
            hours_spent = hours_spent_on_issue(issue, structure)
            issuesHtml += f'<td>{hours_spent} hours</td>'
            issuesHtml += '</tr>'
            spentOnEpic += hours_spent
        issuesHtml += '</table></div>'
        issuesHtml += f'<p><b>Total epic hours:</b> {spentOnEpic}</p>'
    issuesHtml += '<hr>'
    issues_outside_epics = list(filter(lambda issue: not issue['epic'],structure))
    if issues_outside_epics:
        issuesHtml += f'<p><b>Issues outside epics:</b></p>'
        issuesHtml += '<table>'
        for issue in issues_outside_epics:
            issuesHtml += '<tr>'
            issuesHtml += f'<td>{create_link_to_issue(issue["key"])}: {issue["summary"]}</td>'
            issuesHtml += f'<td>   {hours_spent_on_issue(issue, structure)} hours</td>'
            issuesHtml += '</tr>'
            issuesHtml += '</table>'
            issuesHtml += '<hr>'
    issuesHtml += f'<p><b>Total hours:</b> {totalTimeSpent}</p>'
    css = """
    body {font-family: sans-serif;}
    .indent {margin-left: 30px;}
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
