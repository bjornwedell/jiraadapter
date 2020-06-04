def generate_page(structure, user, fromDateString, toDateString):
    string = ""
    totalTimeSpent = 0
    for issue in structure:
        string += f"<h1>{issue['summary']}</h1>"
        string += f"<h3>{issue['hours_spent']} hours</h3>"
        totalTimeSpent += issue['hours_spent']
    string += f"<h2>Total hours: {totalTimeSpent}</h2>"
    return f"""
<html>
<head><title>JIRA Timetable</title></head>
<h1>{user} from {fromDateString} to {toDateString}</h1>
{string}
</html>
"""