#!/bin/sh
# Run or attach program in tmux

PROG="$(basename $1)"

WIN=$(tmux lsw -aF '#{session_name}:#{window_index}!#{window_name}' | awk '
BEGIN{
    FS="!"
}
($2 == prog){
    print $1
    exit
}' prog=$PROG)

if [[ -z "$WIN" ]]; then
    exec tmux new-window -n "$PROG" "$@"
else
    exec tmux link-window -s "$WIN"
fi

