#!/bin/bash
# Estimate usage, notify every hour

#TODO compare last datetime with now, if time difference smaller 5 min, count on
counter=0
echo "Start session"
while true; do
    currentDate=$(date +%d-%m-%Y,%H:%M)
    currentScreen=$(wmctrl -d | grep -m1 "*" | awk '{print $1}')
    currentProgramms=$(wmctrl -lG | awk -v ref="$currentScreen" '$2==ref {print ","; for (i=8; i<NF; i++) printf $i "_"; print $NF;}')
    echo $currentDate","$counter$currentProgramms
    if [[ $(( counter % 60 )) == 0 ]];
    then
        notify-send "Screentime" "uptime: $counter min" -u normal -a 'Time'
    fi
    counter=$((counter+1))
    sleep 60
done

echo "End session"
exit 0
