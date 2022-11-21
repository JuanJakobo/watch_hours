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
