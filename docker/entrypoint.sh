#!/bin/sh

start() {
    /app/scripts/database.sh list &> /dev/null

    if [ $? -ne 0 ]; then
        /app/scripts/database.sh setup
    else
        /app/scripts/database.sh migrate
    fi

    while [[ $(echo "EXISTS bot_user\r\n" | nc localhost 6379) =~ "0" ]]; do
       sleep 1
    done

    python3 main.py
}

start
