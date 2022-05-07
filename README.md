# ModMail

[![Discord](https://discord.com/api/guilds/576016832956334080/widget.png)][discord]
[![License](https://img.shields.io/github/license/chamburr/modmail.svg)](LICENSE)

A feature-rich Discord bot for easy communication between server staff and users.

![Screenshot](https://chamburr.xyz/u/7PUf0Z.png)

A new channel is created whenever a user messages the bot, and the channel will serve as a shared
inbox for seamless communication between staff and the user.

To learn more, check out our [website](https://modmail.xyz) or visit our [Discord server][discord].

## Contributing

There are many ways you can contribute to this project:

- [Submitting bugs and suggestions](https://github.com/chamburr/modmail/issues)
- [Reviewing pull requests](https://github.com/chamburr/modmail/pulls)
- [Contribute directly to the code base](https://github.com/chamburr/modmail/pulls)

For more information, please see our [contributing guidelines](CONTRIBUTING.md).

The issue tracker here is only for bug reports and suggestions. Please do not use it to ask a
question. Instead, ask it on our [Discord server][discord].

## Self-hosting

Modmail can now be hosted through Docker. 

To start, you will need to clone the repository locally or fork it.
```
$ git clone git@github.com:chamburr/modmail.git
```
or
```
$ git clone git@github.com:<Your Username>/modmail.git
```

You will need to make sure that you have [created a bot application](https://discordpy.readthedocs.io/en/stable/discord.html) through Discord. Then, you will need three pieces of information to put them into the `.env` file located in `modmail/docker`

###### REQUIRED
```
BOT_TOKEN = The Token on your Bot page
BOT_CLIENT_ID = Client ID on the OAuth2 page
BOT_CLIENT_SECRET = Client Secret on the OAuth2 page
```
###### OPTIONAL

```
STATUS = <online | idle | dnd | offline>
ACTIVITY_NAME - Displays the bot's current activity
DEFAULT_SERVER - If a server ID is put here, all tickets will be directed to this server
DEFAULT_PREFIX - Change the default prefix of the bot
OWNER_USERS - Users who have access to sensitive commands 
ADMIN_USERS - Users who have a subset of the owner commands (not necessary to use)
```

#### Build the Project
You must have Docker installed on your system, and instructions on how to do so can be found [here](https://docs.docker.com/get-docker/). Once you have Docker installed, you can do the following:

```
$ cd modmail/docker

$ docker compose up
```

The initial build can take anywhere from 10-30 minutes depending on your computer specs, but subsequent builds will usually take under a minute. These commands will build 3 volumes and 7 containers on your computer. 
## License

This project is licensed under [GNU Affero General Public License v3.0](LICENSE).

[discord]: https://discord.gg/wjWJwJB
