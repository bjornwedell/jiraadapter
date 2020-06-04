def generate_page(structure, user, fromDateString, toDateString):
    issuesHtml = '<table>'
    totalTimeSpent = 0
    for issue in structure:
        totalTimeSpent += issue["hours_spent"]
        issuesHtml += '<tr>'
        issuesHtml += f'<td>{issue["summary"]}</td>'
        issuesHtml += f'<td>{issue["hours_spent"]} hours</td>'
        issuesHtml += '</tr>'
    issuesHtml += '</table>'
    issuesHtml += f'<p><b>Total hours:</b> {totalTimeSpent}</p>'
    return f"""
<html>
<head><title>JIRA Timetable</title></head>
<h1>{user} from {fromDateString} to {toDateString}</h1>
{issuesHtml}
</html>
"""