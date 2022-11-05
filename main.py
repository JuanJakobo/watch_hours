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
    connection.close()

def format_time(minutes):
    """Formats the input as a string and if is bigger 60 divives into hours"""
    if minutes >= 60:
        time_passed = str(int(minutes / 60)) + "h " + str(minutes % 60) + "min"
    else:
        time_passed = str(minutes) + " min"
    return time_passed

def write_usage_to_db(path):
    """Endless loop that tracks each minute which windows are open
    and writes these values to an DB."""
    try:
        connection = sqlite3.connect(path)
        counter = 0
        while True:
            current_window = Window.get_active()
            if current_window is not None:
                window_class = current_window.wm_class
                if window_class == "Alacritty.Alacritty":
                    #TODO tmux window name
                    window_name = "Code"
                else:
                    window_name = current_window.wm_name
            else:
                window_class = "Empty.Empty"
                window_name = "Empty"
            cursor = connection.cursor()
            cursor.execute("INSERT INTO USAGE VALUES (?,?,?)",
                           (datetime.now(), window_class, window_name))
            connection.commit()
            #TODO variable, print on verbose option
            if counter % 60 == 0:
                notification('Screentime',message=f"uptime: {int(counter/60)} h",app_name='usage')
            time.sleep(60)
            counter += 1
    except KeyboardInterrupt:
        print('Closing')
        connection.close()
        sys.exit(0)

def draw_log(path):
    """Draws the usage for the last 7 days to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM usage ORDER BY date DESC LIMIT 10")
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]} {row[1]}")
    connection.close()


def draw_average_usage_per_weekday(path):
    """Draws the average usage per weekday to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    #TODO avrg
    cursor.execute("SELECT strftime('%w',Date) as day, Count(*) as time FROM usage GROUP BY day")
    rows = cursor.fetchall()

    day_names = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    for row in rows:
        print(f"{day_names[int(row[0])-1]:<9} {row[1]:<3} min")
    connection.close()

def draw_program_usage(path):
    """Draws the usage seperated per program to the terminal"""
    #select where program is
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT focusedWindowClass, Count(focusedWindowClass) \
            as usage FROM usage GROUP BY focusedWindowClass ORDER BY usage DESC")
    rows = cursor.fetchall()

    for row in rows:
        print(f"{row[0]:<20} ({row[1]:<3} min) ",end="")
        for _ in range(row[1]):
            print("#",end="")
        print()
    connection.close()

def draw_usage_between_timeintervalls(path):
    """Draws the usage between certain timeintervalls to the terminal"""
    #TODO implement
    #cursor.execute("SELECT time(Date), FocusedWindow FROM
    #usage WHERE time(Date) > '19:50:00' and time(Date) < '19:52:00'")
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%H',date) as time,Count(*) FROM usage \
                   WHERE date >= DATE('now','localtime') GROUP BY time ORDER BY time ASC")
    rows = cursor.fetchall()

    for row in rows:
        print(f"{row[0]} ",end="")
        for _ in range(row[1]):
            print("#",end="")
        print()

def draw_todays_usage(path):
    """Draws the usage for today grouped by hour to the terminal"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%H',date) as time,Count(*) FROM usage \
            WHERE Date >= DATE('now','localtime') GROUP BY time ORDER BY time ASC")
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]:<2} ({row[1]:<2} min) ",end="")
        for _ in range(row[1]):
            print("#",end="")
        print()
    connection.close()

if __name__ == '__main__':
    main()
