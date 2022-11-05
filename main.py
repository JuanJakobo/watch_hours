"""
Tracks how the user uses the system, stores the value in an DB.
The values can be analyized using this program also.

Usage:
  usage.py write <path> [--intervall=<num>] [--timer=<num>] [--verbose]
  usage.py log <path> [--size=<num>]
  usage.py (-h | --help)
  usage.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  <path>        Location of the DB
  write
    --timer=<num>  Timer after that a notification is drawn in seconds [default: 3600].
    --intervall=<num>  Intervall after that an log entry is written in seconds [default: 60].
  log
    --size=<num>  Count of entries [default: 10].
"""
from datetime import datetime
import sqlite3
import sys
import time
from docopt import docopt
from notify import notification
from wmctrl import Window

def main():
    """Handles the user input and calls function accordingly"""
    arguments = docopt(__doc__, version='Usage 0.1')

    create_database(arguments['<path>'])

    if arguments['log']:
        draw_log(arguments['<path>'], arguments['--size'])
    elif arguments['write']:
        write_usage_to_db(path=arguments['<path>'], intervall=int(arguments['--intervall']), \
                          timer=int(arguments['--timer']), verbose=arguments['--verbose'])

def create_database(path):
    """Opens the DB and creates a new table if not existend"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    table = """ CREATE TABLE IF NOT EXISTS usage (
       date INT PRIMARY KEY NOT NULL,
       windowClassId INT NOT NULL,
       focusedWindowName TEXT NOT NULL,
       FOREIGN KEY(windowClassId) REFERENCES windowClasses(id)); """
    cursor.execute(table)
    table = """ CREATE TABLE IF NOT EXISTS windowClasses (
       id INTEGER PRIMARY KEY NOT NULL,
       name TEXT NOT NULL UNIQUE); """
    cursor.execute(table)
    connection.close()

def insert_usage_into_db(path, window_name, window_class, verbose):
    """inserts items into the DB"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("BEGIN TRANSACTION")
    window_class_id = 0
    try:
        cursor.execute("INSERT INTO windowClasses ('name') VALUES (?)", (window_class,))
        window_class_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        if verbose:
            print(f"Window_class '{window_class}' already exists.")
        result = cursor.execute("SELECT id FROM windowClasses \
                        WHERE name = ?", (window_class,))
        for row in result:
            window_class_id = row[0]
    if window_class_id > 0:
        item = (time.mktime(datetime.now().timetuple()), window_class_id, window_name)
        cursor.execute("INSERT INTO USAGE VALUES (?,?,?)", item)
    cursor.execute("COMMIT TRANSACTION")
    if verbose:
        print(f"Added {item}")
    connection.commit()

def write_usage_to_db(path, intervall, timer, verbose):
    """Endless loop that tracks each minute which windows are open
    and writes these values to an DB."""
    seconds_passed = 0
    while True:
        #get current window
        current_window = Window.get_active()
        if current_window is not None:
            window_class = current_window.wm_class
            window_name = current_window.wm_name
        else:
            window_class = "Empty.Empty"
            window_name = "Empty"
        insert_usage_into_db(path, window_name, window_class, verbose)
        #draw notification after timer
        if seconds_passed % timer == 0:
            notification('Screentime',message=f"uptime: {int(seconds_passed/60)} h",\
                    app_name='usage')
        if verbose:
            print(f"Running since {seconds_passed} seconds")
        seconds_passed += intervall
        time.sleep(intervall)

def draw_log(path, limit):
    """Draws the last limit entries to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    rows = cursor.execute("SELECT datetime(date,'unixepoch'), wC.name, focusedWindowName \
            FROM usage JOIN windowClasses as wC ON usage.windowClassId = wC.id \
            ORDER BY date DESC LIMIT ?", (limit,))
    for row in rows:
        print(f"{row[0]} | {row[1]:<20} | {row[2]}")
    connection.close()

def format_time(minutes):
    """Formats the input as a string and if is bigger 60 divives into hours"""
    if minutes >= 60:
        time_passed = str(int(minutes / 60)) + "h " + str(minutes % 60) + "min"
    else:
        time_passed = str(minutes) + " min"
    return time_passed

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Closing')
        sys.exit(0)
