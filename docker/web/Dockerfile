FROM node:16-alpine AS builder

RUN npm install -g -f yarn

WORKDIR /build

COPY web/package.json web/yarn.lock ./

RUN yarn --frozen-lockfile

COPY web/nuxt.config.js ./
COPY web/assets ./assets
COPY web/components ./components
COPY web/content ./content
COPY web/layouts ./layouts
COPY web/pages ./pages
COPY web/plugins ./plugins
COPY web/static ./static
COPY web/store ./store

RUN yarn build

FROM node:16-alpine

RUN apk add --no-cache dumb-init

WORKDIR /app

COPY web/package.json web/yarn.lock ./

RUN yarn --frozen-lockfile --prod

COPY --from=builder /build/.nuxt ./.nuxt

COPY web/nuxt.config.js ./
COPY web/content ./content

EXPOSE 6000

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["yarn", "start"]
