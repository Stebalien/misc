#!/bin/bash

# Quit if I can't get my stuff
test -d "$XDG_DATA_HOME" || exit 0

# Check for pid (remove stale).
if [[ -e "$XDG_DATA_HOME/offlineimap/pid" ]]; then
    kill -0 $(cat "$XDG_DATA_HOME/offlineimap/pid") 2>/dev/null && exit
    rm "$XDG_DATA_HOME/offlineimap/pid"
fi

# Restart on fail, die if killed.
trap 'pkill -USR2 -P $$ -x offlineimap; exit 0' 0
while true; do
    # Wait until we have an internet connection.
    while ! ping -nc1 google.com 2>&1 >/dev/null; do
        sleep 300
    done

    mc=0
    { ionice -c2 -n7 nice -n 10 offlineimap -u Basic 2>/dev/null |
    while read line; do
        if echo $line | grep -e "^Sleeping " >/dev/null; then
            if [[ $mc -gt 0 ]]; then
                if [[ -n "$DISPLAY" ]]; then
                    notify-send "New Mail" "You have $mc new messages."
                    xset led 3
                    mc=0
                elif [[ -n "$TMUX" ]]; then
                    tmux display-message "You have $mc new messages."
                elif [[ -n "$STY" ]]; then
                    screen -X echo "You have $mc new messages."
                else
                    setleds +scroll
                fi
            fi
            continue
        else
            echo "$line" | grep -e '^Copy message [0-9]* \w*\[INBOX\] ->.*$' > /dev/null && mc=$(( $mc + 1 ))
        fi
    done } && exit 0
done
