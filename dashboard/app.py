"""
Displays an dashboard with the usage of the computer
"""
import sqlite3
import json
from datetime import date
from flask import Flask, render_template, request

app = Flask(__name__)

def openDB():
    #check if is none
    path = config_data['path']
    connection = sqlite3.connect(path)
    #TODO test if path exists and is SQL DB
    return connection

@app.route("/")
def index():
    """Draws the usage for the last 'days' including today"""
    days = request.args.get("days")
    if days is None:
        days = 10
    connection = openDB()
    cursor = connection.cursor()

    days = "-" + str(days) + " days"
    rows = cursor.execute("SELECT DATE(date,'unixepoch','localtime') AS time, COUNT(*) FROM usage \
            WHERE time >= DATE('now','localtime',?) \
            GROUP BY time ORDER BY time ASC", (days,))
    labels = []
    values = []
    for row in rows:
        labels.append(row[0])
        values.append(row[1]/60)
    connection.close()
    legend = "Daily Usage in hours"
    title = "Usage of last days"
    return render_template('chartLastDays.html', values=values, labels=labels, legend=legend, title=title, days=days)

@app.route("/usagePerHour")
def draw_usage_per_hour():
    """Draws the usage for today grouped by hour"""
    day = request.args.get("day")
    if day is None:
        day = date.today()
    connection = openDB()
    cursor = connection.cursor()
    rows = cursor.execute("SELECT strftime('%H',date,'unixepoch','localtime') AS time, COUNT(*) \
            FROM usage WHERE DATE(date,'unixepoch','localtime') IS ? GROUP BY time \
            ORDER BY time ASC", (day,))
    labels = []
    values = []
    for row in rows:
        labels.append(f"{row[0]}:00 h")
        values.append(row[1])
    connection.close()
    legend = "Usage per hour"
    title = "Usage per hour on certain day"
    return render_template('chartUsagePerHour.html', values=values, labels=labels, legend=legend, title=title, day=day)

@app.route("/programUsage")
def draw_program_usage():
    """Draws the usage seperated per program"""
    connection = openDB()
    cursor = connection.cursor()
    rows = cursor.execute("SELECT ws.name, Count(u.windowClassId) \
            AS usage FROM usage AS u JOIN windowClasses AS ws ON u.windowClassId = ws.id \
            GROUP BY u.windowClassId ORDER BY usage DESC")
    #TODO use a SET or dictinoary
    labels = []
    values = []
    for row in rows:
        labels.append(row[0][row[0].find('.')+1:])
        values.append(row[1])
    connection.close()
    legend = 'Total Minutes'
    title = 'Usage per Program'
    return render_template('chart.html', values=values, labels=labels, legend=legend, title=title)

@app.route("/AvgPerWeekday")
def draw_average_usage_per_weekday():
    """Draws the average usage per weekday"""

    connection = openDB()
    cursor = connection.cursor()
    #TODO avrg
    rows = cursor.execute("SELECT STRFTIME('%w',day) AS weekday, AVG(time) from (SELECT DATE(date,'unixepoch') AS day, \
                          COUNT(*) AS time FROM usage GROUP BY day) GROUP BY weekday")

    day_names = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    labels = []
    values = []
    for row in rows:
        labels.append(day_names[int(row[0])-1])
        values.append(row[1]/60)
    connection.close()
    legend = 'Average Hours'
    title = 'Avg. Usage per weekday'
    return render_template('chart.html', values=values, labels=labels, legend=legend, title=title)

@app.route("/detailedClassUsage")
def draw_detailed_class_usage():
    """Draws the detailed usage of a certain program"""
    #name of the window class
    connection = openDB()
    cursor = connection.cursor()

    rows = cursor.execute("SELECT name from WindowClasses")
    window_classes = []
    for row in rows:
        window_classes.append(row[0][row[0].find('.')+1:])

    class_name = request.args.get("class_name")
    if class_name is None:
        class_name = "firefox"
    detail = request.args.get("detail")
    if detail is None:
        detail = ""
    window_class_name = "%" + class_name + "%"
    rows = cursor.execute("SELECT focusedWindowName, COUNT(focusedWindowName) \
            AS usage FROM usage JOIN windowClasses ON usage.windowClassId = windowClasses.id  WHERE windowClasses.name LIKE ? \
            GROUP BY focusedWindowName ORDER BY usage DESC", (window_class_name,))

    #TODO clean up
    labels = []
    values = []
    sum = 0
    for row in rows:
        #test = row[0].split('—')[0] #.split()[-1]
        #if '|' in test:
        #    test = test.split('|')[-1].strip()
        #if '-' in test:
        #    test = test.split('-')[-1].strip()
        if len(detail) == 0:
            labels.append(row[0])
            values.append(row[1])
        elif row[0].find(detail) >= 0:
            sum += row[1]
    if not len(detail) == 0:
        labels.append(detail)
        values.append(sum)
    connection.close()
    legend = "Total Usage in min"
    title = "Usage per Name"
    return render_template('chartDetailedClassUsage.html', values=values, labels=labels, legend=legend, title=title, window_classes=window_classes, detail=detail, class_name=class_name)

@app.route("/log")
def draw_log():
    """Draws the last "limit" entries"""
    limit = 200
    connection = openDB()
    cursor = connection.cursor()
    rows = cursor.execute("SELECT DATETIME(date,'unixepoch','localtime'), wC.name, focusedWindowName \
            FROM usage JOIN windowClasses as wC ON usage.windowClassId = wC.id \
            ORDER BY date DESC LIMIT ?", (limit,))
    values = []
    for row in rows:
        values.append(f"{row[0]} | {row[1]:<20} | {row[2]}")
    connection.close()
    title = "Log"
    return render_template('log.html', values=values, title=title)


if __name__ == "__main__":
    with open('config.json') as config_file:
        config_data = json.load(config_file)
    app.run(debug=True)
