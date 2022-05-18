#!/bin/bash

database_url=""

init() {
    if [[ ! -x "$(command -v diesel)" ]]; then
        echo "Error: diesel not found."
        exit 1
    fi

    if [[ -f .env ]]; then
        source .env
    else
        echo "Warning: .env file not found."
    fi

    database=$POSTGRES_DATABASE
    username=$POSTGRES_USERNAME
    password=$POSTGRES_PASSWORD
    host=$POSTGRES_HOST
    port=$POSTGRES_PORT
    database_url="postgresql://$username:$password@$host:$port/$database"
}

help() {
    echo "ModMail Database"
    echo "Database management CLI. Configure details in .env file."
    echo ""
    echo "USAGE:"
    echo "    ./scripts/database.sh [COMMAND]"
    echo ""
    echo "COMMANDS:"
    echo "    help      Show usage information."
    echo "    setup     Create the database and run migrations."
    echo "    reset     Reset the entire database."
    echo "    create    Create a new migration."
    echo "    migrate   Run all pending migrations."
    echo "    revert    Revert the last migration."
    echo "    redo      Revert and re-run the last migration."
    echo "    list      List all the migrations."
}

init

case "$1" in
    help|"")
        help
        ;;
    setup)
        echo "Setting up database..."
        diesel database setup --database-url $database_url
        ;;
    reset)
        echo "Resetting database..."
        diesel database reset --database-url $database_url
        ;;
    create)
        if [[ "$#" -eq 1 ]]; then
            echo "Usage: ./scripts/database.sh create <name>"
        else
            shift
            echo "Creating new migration..."
            diesel migration generate "$@" --database-url $database_url
        fi
        ;;
    migrate)
        echo "Running migrations..."
        diesel migration run --database-url $database_url
        ;;
    revert)
        echo "Reverting migration..."
        diesel migration revert --database-url $database_url
        ;;
    redo)
        echo "Redoing migration..."
        diesel migration redo --database-url $database_url
        ;;
    list)
        diesel migration list --database-url $database_url
        ;;
    *)
        echo "The command $1 was not found."
        echo ""
        echo "Use ./scripts/database.sh help for more information."
        ;;
esac
