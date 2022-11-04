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

if __name__ == '__main__':
    main()
