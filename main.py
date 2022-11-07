"""
Tracks how the user uses the system, stores the value in an DB.
The values can be analyized using this program also.

Usage:
  usage.py write <path> [--timer=<num>] [--verbose]
  usage.py log <path> [--size=<num>]
  usage.py print <path> <report> [--day=<date>] [--days=<num>] [--className=<str>]
  usage.py (-h | --help)
  usage.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  <path>        Location of the DB
  write
    --timer=<num>  Timer after that a notification is drawn in seconds [default: 3600].
  log
    --size=<num>  Count of entries [default: 10].
  print
    <report> Available reports are AvgPerWeekday, DailyUsage, DetailedClass, PreviousDaysUsage,\
            ProgrammUsage [default: AvgPerWeekday]
    --day=<date>  Date to report on [default: 2022-11-07]
    --days=<num>  Count of days to report on for PreviousDaysUsage [default: 1].
    --className=<num>  Name of class to detail [default: firefox].
"""
from datetime import datetime
import sqlite3
import sys
import time
from docopt import docopt
from notify import notification
from wmctrl import Window

#TODO add tests
def main():
    """Handles the user input and calls function accordingly"""
    arguments = docopt(__doc__, version='Usage 0.1')

    create_database(arguments['<path>'])

    if arguments['log']:
        draw_log(arguments['<path>'], arguments['--size'])
    elif arguments['write']:
        write_usage_to_db(path=arguments['<path>'],\
                timer=int(arguments['--timer']), verbose=arguments['--verbose'])
    elif arguments['print']:
        if arguments['<report>'] == "AvgPerWeekday":
            draw_average_usage_per_weekday(path=arguments['<path>'])
        elif arguments['<report>'] == "DailyUsage":
            draw_daily_usage(path=arguments['<path>'], day=arguments['--day'])
        elif arguments['<report>'] == "DetailedClass":
            draw_detailed_class_usage(path=arguments['<path>'], class_name=arguments['--className'])
        elif arguments['<report>'] == "PreviousDaysUsage":
            draw_previous_days_usage(path=arguments['<path>'],days=arguments['--days'])
        elif arguments['<report>'] == "ProgrammUsage":
            draw_program_usage(path=arguments['<path>'])

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

def format_time(minutes):
    """Formats the input as a string and if is bigger 60 divives into hours"""
    if minutes >= 60:
        time_passed = str(int(minutes / 60)) + "h " + str(minutes % 60) + "min"
    else:
        time_passed = str(minutes) + " min"
    return time_passed

def draw_total_daily_usage(path):
    """Returns total usage for today to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    rows = cursor.execute("SELECT COUNT(*) FROM usage \
                          WHERE DATE(date,'unixepoch','localtime') IS DATE('now','localtime') \
                          GROUP BY DATE(date,'unixepoch','localtime')")
    for row in rows:
        return format_time(row[0])
    connection.close()

def write_usage_to_db(path, timer, verbose):
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
            total_usage = draw_total_daily_usage(path)
            notification('Screentime',message=f"uptime: {int(seconds_passed/timer)} h \nTotal daily uptime: {total_usage}",\
                    app_name='usage')
        if verbose:
            print(f"Running since {seconds_passed} seconds")
        seconds_passed += 60
        time.sleep(60)

def draw_log(path, limit):
    """Draws the last limit entries to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    rows = cursor.execute("SELECT DATETIME(date,'unixepoch'), wC.name, focusedWindowName \
            FROM usage JOIN windowClasses as wC ON usage.windowClassId = wC.id \
            ORDER BY date DESC LIMIT ?", (limit,))
    for row in rows:
        print(f"{row[0]} | {row[1]:<20} | {row[2]}")
    connection.close()

def draw_average_usage_per_weekday(path):
    """Draws the average usage per weekday to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    #TODO avrg
    rows = cursor.execute("SELECT STRFTIME('%w',date,'unixepoch') AS day, COUNT(*) AS time FROM usage GROUP BY day")

    day_names = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    for row in rows:
        print(f"{day_names[int(row[0])-1]:<9} {format_time(row[1]):<3}")
    connection.close()

def draw_program_usage(path):
    """Draws the usage seperated per program to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    rows = cursor.execute("SELECT ws.name, Count(u.windowClassId) \
            AS usage FROM usage AS u JOIN windowClasses AS ws ON u.windowClassId = ws.id \
            GROUP BY u.windowClassId ORDER BY usage DESC")

    for row in rows:
        print(f"{row[0]:<25} {format_time(row[1]):<3}")
    connection.close()

def draw_daily_usage(path, day):
    """Draws the usage for today grouped by hour to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    rows = cursor.execute("SELECT strftime('%H',date,'unixepoch','localtime') AS time, COUNT(*) \
            FROM usage WHERE DATE(date,'unixepoch','localtime') IS ? GROUP BY time \
            ORDER BY time ASC", (day,))
    for row in rows:
        print(f"{row[0]:<2} ({row[1]:<2} min) ",end="")
        for _ in range(row[1]):
            print("#",end="")
        print()
    connection.close()

def draw_previous_days_usage(path, days):
    """Draws the usage for the last 'days' including today to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    days = "-" + str(days) + " days"
    rows = cursor.execute("SELECT DATE(date,'unixepoch','localtime') AS time, COUNT(*) FROM usage \
            WHERE time >= DATE('now','localtime',?) \
            GROUP BY time ORDER BY time ASC", (days,))
    for row in rows:
        print(f"{row[0]:<2} {format_time(row[1]):<3}")
    connection.close()

def draw_detailed_class_usage(path, class_name):
    """Draws the detailed usage of a certain program to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    window_class_name = "%" + class_name + "%"
    rows = cursor.execute("SELECT focusedWindowName, COUNT(focusedWindowName) \
            AS usage FROM usage JOIN windowClasses ON usage.windowClassId = windowClasses.id  WHERE windowClasses.name LIKE ? \
            GROUP BY focusedWindowName ORDER BY usage ASC", (window_class_name,))

    #TODO define seperator, add up items
    #seperator is - or | or page name is at beginning
    for row in rows:
        test = row[0].split('—')[0] #.split()[-1]
        if '|' in test:
            test = test.split('|')[-1].strip()
        if '-' in test:
            test = test.split('-')[-1].strip()

        print(f"{test:<50} {format_time(row[1]):<3}")
    connection.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Closing')
        sys.exit(0)
