from wmctrl import Desktop, Window
from datetime import datetime
import time

counter = 0
while(True):
    out = str(datetime.now().strftime('%Y-%m-%d;%H:%M')) + ';' + str(counter)
    activeDesktop = Desktop.get_active().num
    for i in Window.list():
        if(i.desktop == activeDesktop):
            out = out + ';' + i.wm_name
            #TODO tmux window name
    print(out)
    time.sleep(60)
    counter += counter
