docker build --rm=true -f docker/bot/Dockerfile . -t modmail-bot:dev

docker build --rm=true -f docker/api/Dockerfile . -t modmail-api:dev

docker build --rm=true -f docker/web/Dockerfile . -t modmail-web:dev