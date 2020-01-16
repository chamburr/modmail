# ModMail

[![Discord](https://discordapp.com/api/guilds/576016832956334080/embed.png)](https://discord.gg/wjWJwJB)
[![License](https://img.shields.io/github/license/CHamburr/modmail.svg)](https://github.com/CHamburr/modmail/blob/master/LICENSE)
[![Codacy](https://api.codacy.com/project/badge/Grade/aad8b5aee37940a08b15d6de2bc977a8)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CHamburr/modmail&amp;utm_campaign=Badge_Grade)

A feature-rich Discord bot for easy communication between server staff and users.

![Screenshot](https://modmail.netlify.com/images/screenshot.png)

A new channel is created whenever a user messages the bot, and the channel will serve as a shared inbox for seamless communication between staff and the user.

To learn more, check out our [website](https://modmail.netlify.com) or visit our [Discord server](https://discord.gg/wjWJwJB).

## Contributing

Want to contribute? Awesome! There are many ways you can contribute to this project, for example:

- [Submitting bugs and feature requests](https://github.com/CHamburr/modmail/issues)
- [Reviewing changes](https://github.com/CHamburr/modmail/issues)
- Sponsoring the project (Please let CHamburr#2591 know on Discord)

If you wish to help us fix issues or contribute directly to the code base, please see [contributing guidelines](https://github.com/CHamburr/modmail/blob/master/CONTRIBUTING.md). You can also find a self-hosting guide below.

The issue tracker here is only for bug reports and feature requests. Please do not use it to ask a question. Instead, ask it on our [Discord server](https://discord.gg/wjWJwJB) or message CHamburr#2591 directly.

## Self-Hosting

This self-hosting guide requires you to have some basic knowledge about command line, Python, and Discord bots. If you meet any issues while running the bot, please use Google before asking in our Discord server.

### Prerequisites

In order to run ModMail, you will need to install the following tools.

- [Git](https://git-scm.com)
- [Python 3](https://www.python.org/downloads/)

### Getting the Sources

Please fork this repository so that you can make pull requests. Then, clone your fork.

```sh
git clone https://github.com/<github-username>/modmail.git
```

Sometimes you may want to merge changes from the upstream repository to your fork.

```sh
git checkout master
git pull https://github.com/CHamburr/modmail.git master
```

### Configuration

Configuration is done through a `config.py` file. You should make a copy of `config.example.py` and rename it to `config.py`. All fields must be filled in, except for bot list tokens and the Sentry URL only if you have `testing` set to `False`.

### Installing Modules

ModMail utilises [discord.py](https://github.com/Rapptz/discord.py) and several other modules to function properly. The list of modules can be found in `requirements.txt` and you can install them with the following command.

```sh
pip3 install -r requirements.txt
```

### Running the Bot

Congratulations! You have set up everything and you can finally have the bot up and running. Use the following command to run.

```sh
py main.py
```

## Code of Conduct

This project is governed by [Contributor Covenant Code of Conduct](https://github.com/CHamburr/modmail/blob/master/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

This project is licensed under [GNU Affero General Public License v3.0](https://github.com/CHamburr/modmail/blob/master/LICENSE).
