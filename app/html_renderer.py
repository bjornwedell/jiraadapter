def generate_page(structure, user, fromDateString, toDateString, totalTimeSpent):
    issuesHtml = '<table>'
    for issue in structure:
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