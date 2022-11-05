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

#TODO put together
def draw_usage(path, start_time, end_time, order_by, calculation_type):
    """Draws the usage for the last 7 days to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%Y-%m-%d',date) AS time, COUNT(*) FROM usage \
            WHERE Date >= DATE('now','localtime','weekday 0','-6 days') \
            GROUP BY time ORDER BY time ASC")
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]:<2} {format_time(row[1]):<3}")
    connection.close()

def draw_average_usage_per_weekday(path):
    """Draws the average usage per weekday to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    #TODO avrg
    cursor.execute("SELECT strftime('%w',Date) AS day, COUNT(*) AS time FROM usage GROUP BY day")
    rows = cursor.fetchall()

    day_names = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    for row in rows:
        print(f"{day_names[int(row[0])-1]:<9} {format_time(row[1]):<3}")
    connection.close()

def draw_program_usage(path):
    """Draws the usage seperated per program to the terminal"""
    #TODO select range
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT focusedWindowClass, Count(focusedWindowClass) \
            AS usage FROM usage GROUP BY focusedWindowClass ORDER BY usage DESC")
    rows = cursor.fetchall()

    for row in rows:
        print(f"{row[0]:<25} {format_time(row[1]):<3}")
    connection.close()

def draw_usage_between_timeintervalls(path):
    """Draws the usage between certain timeintervalls to the terminal"""
    #TODO implement
    #cursor.execute("SELECT time(Date), FocusedWindow FROM
    #usage WHERE time(Date) > '19:50:00' and time(Date) < '19:52:00'")
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%H',date) AS time, COUNT(*) FROM usage \
                   WHERE date >= DATE('now','localtime') GROUP BY time \
                   ORDER BY time ASC")
    rows = cursor.fetchall()

    for row in rows:
        print(f"{row[0]:<2} {format_time(row[1]):<3}")

def draw_todays_usage(path):
    """Draws the usage for today grouped by hour to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%H',date) AS time, COUNT(*) FROM usage \
            WHERE Date >= DATE('now','localtime') GROUP BY time \
            ORDER BY time ASC")
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]:<2} ({row[1]:<2} min) ",end="")
        for _ in range(row[1]):
            print("#",end="")
        print()
    connection.close()

def draw_last_seven_days_usage(path):
    """Draws the usage for the last 7 days to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%Y-%m-%d',date) AS time, COUNT(*) FROM usage \
            WHERE Date >= DATE('now','localtime','weekday 0','-6 days') \
            GROUP BY time ORDER BY time ASC")
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]:<2} {format_time(row[1]):<3}")
    connection.close()

def draw_detailed_program_usage(path):
    """Draws the detailed usage of a certain program to the terminal"""
    #select where program is
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    window_class_name = "%firefox%"
            #cursor.execute("INSERT INTO USAGE VALUES (?,?,?)",
            #               (datetime.now(), window_class, window_name))
    cursor.execute("SELECT focusedWindow, COUNT(focusedWindow) \
            AS usage FROM usage WHERE focusedWindowClass LIKE ? \
            GROUP BY focusedWindow ORDER BY usage ASC", (window_class_name,))
    rows = cursor.fetchall()

    #seperator is - or | or page name is at beginning
    for row in rows:
        test = row[0].split('—')[0] #.split()[-1]
        if '|' in test:
            test = test.split('|')[-1].strip()
        if '-' in test:
            test = test.split('-')[-1].strip()

        print(f"{test:<50} {format_time(row[1]):<3}")
        #if row[1] > 1:
            #print(f"{row[0].split('—')[0]:<50} ({row[1]:<3} min) ",end="")
            #print()
    connection.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Closing')
        sys.exit(0)
