# watch_hours

Keep track how much time you are using your computer.

## How does it work?
The tool tracks the focused window on ***X Window manager*** and writes its class and name each minute to an DB.
After an timer has finished it writes an notification to the screen to inform the user how long he has been using the computer.
There are some reports available to get an overview over the daily usage.

## How do I use it?
Put the following command into your autostart:
'python <Place of the file> write <path to save the DB>'
