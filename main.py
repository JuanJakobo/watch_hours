"""
Tracks how the user uses the system, stores the value in an DB.
The values can be analyized using this program also.
"""

from datetime import datetime
import sqlite3
import sys
from sys import argv
import time
from notify import notification
from wmctrl import Window

def main():
    """Handles the user input and calls function accordingly"""
    #TODO check if arguments are supplied
    #TODO get path
    path = ""
    #TODO check if DB exists
    #open_db(path)
    if len(argv) >= 2:
        for arg in argv:
            if arg == "-f":
                write_usage_to_db(path)
            elif arg == "-d":
                draw_average_usage_per_weekday(path)
            elif arg == "-p":
                draw_program_usage(path)
            elif arg == "-t":
                draw_todays_usage(path)
    else:
        #TODO mention options
        print("Please select an option")

def open_database(path):
    """Opens the DB and creates a new table if not existend"""
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    #TODO test if db exists
    #cursor.execute("DROP TABLE IF EXISTS usage")
    table = """ CREATE TABLE usage (
       date TEXT NOT NULL,
       focusedWindowClass VARCHAR(100) NOT NULL,
       focusedWindow VARCHAR(255) NOT NULL); """
    cursor.execute(table)
    connection.close()

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
            counter += counter
            if counter % 60 == 0:
                notification('Screentime',message=f"uptime: {counter/60} h",app_name='usage')
            time.sleep(60)
            counter =+ 1
    except KeyboardInterrupt:
        print('Closing')
        connection.close()
        sys.exit(0)

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
