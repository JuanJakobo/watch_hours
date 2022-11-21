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
    legend = 'Daily Usage'
    return render_template('chart.html', values=values, labels=labels, legend=legend, days=days)

if __name__ == "__main__":
    app.run(debug=True)
