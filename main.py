from wmctrl import Desktop, Window
from datetime import datetime
import time
import sqlite3
import sys
from sys import argv
import os
from notify import notification

def main():
    #check if arguments are supplied
    path = ""
    #open_db(path)
    if len(argv) >= 2:
        for arg in argv:
            if arg == "-f":
                write_usage_to_db(path)
            elif arg == "-d":
                draw_average_usage_per_day(path)
            elif arg == "-p":
                draw_program_usage(path)
            elif arg == "-t":
                draw_todays_usage(path)

def open_database(path):
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    #test if db exists
    cursor.execute("DROP TABLE IF EXISTS usage")
    table = """ CREATE TABLE usage (
       date TEXT NOT NULL,
       focusedWindowClass VARCHAR(100) NOT NULL,
       focusedWindow VARCHAR(255) NOT NULL); """
    cursor.execute(table)

def write_usage_to_db(path):
    try:
        connection = sqlite3.connect(path)
        counter = 0
        while(True):
            current_window = Window.get_active()
            if current_window is not None:
                window_class = currentWindow.wm_class
                if window_class == "Alacritty.Alacritty":
                    #TODO tmux window name
                    window_name = "Code"
                else:
                    window_name = currentWindow.wm_name
            else:
                window_class = "Empty.Empty"
                window_name = "Empty"
            cursor = connection.cursor()
            cursor.execute("INSERT INTO USAGE VALUES (?,?,?)", (datetime.now(), window_class, window_name))
            connection.commit()
            counter += counter
            if counter % 60 == 0:
                notification('Screentime',message=f"uptime: {counter/60} h",app_name='usage')
            time.sleep(60)
            counter =+ 1
    except KeyboardInterrupt:
        print('Closing')
        connection.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(1)

def draw_average_usage_per_day(path):
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    #TODO avrg
    cursor.execute("SELECT strftime('%w',Date) as day, Count(*) as time FROM usage GROUP BY day")
    rows = cursor.fetchall()

    day_names = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    for row in rows:
        print(f"{day_names[int(row[0])-1]:<9} {row[1]:<3} min")

def draw_program_usage(path):
    #select where program is
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT focusedWindowClass,Count(focusedWindowClass) as usage FROM usage GROUP BY focusedWindowClass ORDER BY usage DESC")
    rows = cursor.fetchall()

    for row in rows:
        print(f"{row[0]:<20} ({row[1]:<3} min) ",end="")
        for i in range(row[1]):
            print("#",end="")
        print()

def draw_usage_between_timeintervalls(path):
    #select where program is
    #cursor.execute("SELECT time(Date), FocusedWindow FROM usage WHERE time(Date) > '19:50:00' and time(Date) < '19:52:00'")
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%H',date) as time,Count(*) FROM usage WHERE date >= DATE('now','localtime') GROUP BY time ORDER BY time ASC")
    rows = cursor.fetchall()

    for row in rows:
        print(f"{row[0]} ",end="")
        for i in range(row[1]):
            print("#",end="")
        print()

def draw_todays_usage(path):
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("SELECT strftime('%H',date) as time,Count(*) FROM usage WHERE Date >= DATE('now','localtime') GROUP BY time ORDER BY time ASC")
    rows = cursor.fetchall()

    for row in rows:
        print(f"{row[0]:<2} ({row[1]:<2} min) ",end="")
        for i in range(row[1]):
            print("#",end="")
        print()

if __name__ == '__main__':
    main()
