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
    legend = "Daily Usage"
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
        values.append(row[1]/60)
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
    rows = cursor.execute("SELECT STRFTIME('%w',date,'unixepoch') AS day, COUNT(*) AS time \
            FROM usage GROUP BY day ORDER BY day DESC")

    day_names = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    labels = []
    values = []
    for row in rows:
        labels.append(day_names[int(row[0])-1])
        values.append(row[1]/60)
    connection.close()
    legend = 'Average Minutes'
    title = 'Avg. Usage per weekday'
    return render_template('chart.html', values=values, labels=labels, legend=legend, title=title)


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
