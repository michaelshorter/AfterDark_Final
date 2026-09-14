#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/jukebox/.Xauthority

# Kill any existing jukebox processes
killall python3 2>/dev/null
killall python 2>/dev/null
sleep 1

# Hide the cursor
sleep 2
unclutter -idle 0 -root &

# Wait for USB drive
echo "Waiting for USB drive..."
while [ ! -d "/media/jukebox/JUKEBOX/videos" ]; do
    sleep 1
done
echo "USB drive found, starting jukebox..."

source /home/jukebox/jukebox-env/bin/activate

# Runs on the small screen only. Large screen stays free for development.
python /home/jukebox/AfterDark2_DualScreen_v2/jukebox_main.py &
MAIN_PID=$!

wait $MAIN_PID
