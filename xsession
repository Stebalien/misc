#!/bin/bash
xlogout() {
        source "$HOME/.xlogoutrc"
        for sig in INT TERM KILL; do
            killall -SIG$sig -ew ${AUTOKILL[@]}

            trap "echo Timout..." INT
            ( sleep 5; kill -SIGINT $$ ) & kill_pid=$!; disown $!
            if wait; then
                kill -SIGTERM $kill_pid
                break
            fi
        done
}

case $1 in
    login)
        exec ck-launch-session $SHELL "$HOME/.xinitrc"
        ;;
    logout)
        xlogout
        eval $LOGOUTCMD
        ;;
    lock)
        sudo -k &
		echo "vicious.suspend()" | awesome-client
        vlock -ns
		echo "vicious.activate()" | awesome-client
        ;;
    shutdown)
        xlogout
        exec dbus-send --system --print-reply --dest="org.freedesktop.ConsoleKit" /org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop
        ;;
    restart)
        xlogout
        exec dbus-send --system --print-reply --dest="org.freedesktop.ConsoleKit" /org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Restart
        ;;
    suspend)
        sudo -k &
        exec dbus-send --print-reply --system --dest="org.freedesktop.UPower" /org/freedesktop/UPower org.freedesktop.UPower.Suspend
        ;;
esac
