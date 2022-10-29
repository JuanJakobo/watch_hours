#!/bin/bash
# Estimate usage, notify every hour

#TODO compare last datetime with now, if time difference smaller 5 min, count on
counter=0
currentDate=$(date)
echo "Start session " $currentDate
while true; do
    currentScreen=$(wmctrl -d | grep -m1 "*" | awk '{print $1}')
    currentProgramms=$(wmctrl -lG | awk -v ref="$currentScreen" '$2==ref {for (i=8; i<NF; i++) printf $i "_"; print $NF " |";}')
    uptime=$(uptime | awk -F , '{print $1}' | awk '{print $3 " " $4}')
    echo $uptime "|" $currentProgramms
    sleep 60
    if [[ $(( counter % 60 )) == 0 ]];
    then
        notify-send "uptime: $uptime" "" -u normal -a 'Time'
    fi
    counter=$((counter+1))
done

echo "End session"
exit 0
