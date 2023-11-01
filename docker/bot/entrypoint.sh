#!/bin/bash

start() {
    /app/scripts/database.sh list &> /dev/null

    if [ $? -ne 0 ]; then
        /app/scripts/database.sh setup
    else
        /app/scripts/database.sh migrate
    fi

    while [[ ! $(echo "EXISTS bot_user" | nc -q1 redis 6379 2>&1) =~ ":1" ]]; do
       sleep 1
    done

    while [[ ! $(echo "12345\n" | nc -q1 rabbitmq 5672 2>&1 | tr -d "\0") =~ "AMQP" ]]; do
        sleep 1;
    done

    python3 -u main.py
}

start
