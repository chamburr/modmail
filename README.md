# ModMail

[![Discord](https://discordapp.com/api/guilds/576016832956334080/embed.png)](https://discord.gg/wjWJwJB)
[![License](https://img.shields.io/github/license/CHamburr/ModMail.svg)](https://github.com/CHamburr/modmail/blob/master/LICENSE)
[![Codacy](https://api.codacy.com/project/badge/Grade/aad8b5aee37940a08b15d6de2bc977a8)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CHamburr/modmail&amp;utm_campaign=Badge_Grade)

A feature-rich Discord bot for easy communication between server staff and users.

Check out [modmail.netlify.com](https://modmail.netlify.com) or visit our [Discord server](https://discord.gg/wjWJwJB) to learn more.

## Contributing

First off, thanks for taking your time to contribute! There are many ways you can contribute to this project, for example:

- [Submitting bugs and feature requests](https://github.com/CHamburr/modmail/issues)
- [Reviewing changes](https://github.com/CHamburr/modmail/issues)
- [Sponsoring the project](https://discord.gg/wjWJwJB) (Please let CHamburr#2591 know on Discord)

If you wish to help us fix issues or contribute directly to the code base, please see the [contributing guidelines](https://github.com/CHamburr/modmail/blob/master/CONTRIBUTING.md). You can also find the self-hosting guide below.

## Self-Hosting

You can run your own instance of ModMail only for testing purposes. This guide requires you to have some basic knowledge about command line, Python, and Discord bots.

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

### Preparing to Run

#### Configuration

Configuration is done through a `config.py` file. You should make a copy of `config.example.py` and rename it to `config.py`. All fields must be filled in, except for bot list tokens and the Sentry URL only if you have `testing` set to `False`.

#### Installing Modules

ModMail utilises [discord.py](https://github.com/Rapptz/discord.py) and several other modules to function properly. The list of modules can be found in `requirements.txt` and you can install them with the following command.

```sh
pip3 install -r requirements.txt
```

### Running the Bot

Congratulations! You have set up everything and you can finally have the bot up and running. Use the following command to run.

```sh
py main.py
```

### Having Issues?

If you meet any issues while running the bot, please feel free to ask in our Discord server! However, before you do so, you should definitely ask your best friend Google.

## Links

- [Website](https://modmail.netlify.com)
- [Discord Server](https://discord.gg/wjWJwJB)

## License

This project is licensed under [GNU Affero General Public License v3.0](https://github.com/CHamburr/modmail/blob/master/LICENSE).
