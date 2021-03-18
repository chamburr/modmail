# Contributing Guide

Hi, thanks for your interest in contributing to ModMail! We'd love your help to make ModMail even
better than it is today. As a contributor, please be sure follow our set of guidelines below.

- [Issues and Bugs](#issues-and-bugs)
- [Pull Requests](#pull-requests)
- [Commit Convention](#commit-convention)
- [Development Environment](#development-environment)
- [Questions](#questions)
- [Code of Conduct](#code-of-conduct)

## Issues and Bugs

We track bugs and features using the GitHub issue tracker. If you come across any bugs or have
feature suggestions, please let us know by submitting an issue, or even better, making a pull
request.

## Pull Requests

Please follow these guidelines related to submitting a pull request.

We use [black](https://github.com/psf/black) and [isort](https://github.com/timothycrosley/isort)
for code style, and use [flake8](https://github.com/PyCQA/flake8) for linting. Please always
run `scripts/format.sh` and ensure that `scripts/lint.sh` returns no error before submitting a pull
request.

Please follow our commit conventions below. For subsequent commits to a pull request, it is okay not
to follow them, because they will be eventually squashed.

## Development Environment

To set up your development environment, follow the self-hosting
guide [here](https://github.com/chamburr/modmail/blob/master/README.md). When you successfully
self-host the bot, your development environment should more or less be ready.

## Commit Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org) to allow for more readable
messages in the commit history.

The commit message must follow this format:

```
<type>(<scope>): <description>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

Additionally, the maximum length of each line must not exceed 72 characters.

### Header

The header is mandatory.

The type must be one of the following, the scope is optional and can be decided at your discretion.

- `build`: Changes to the build system or dependencies.
- `ci`: Changes to our CI configuration files and scripts.
- `chore`: Miscellaneous change.
- `docs`: Changes only the documentation.
- `feat`: Implements a new feature.
- `fix`: Fixes an existing bug.
- `perf`: Improves the performance of the code.
- `refactor`: Changes to code neither fixes a bug nor adds a feature.
- `style`: Changes to code that do not affect its functionality.
- `test`: Adding missing tests or correcting existing tests.

### Body

The body is optional and can contain additional information, such as motivation for the commit.

### Footer

The footer is optional and should contain any information about breaking changes. It is also the
place to reference GitHub issues that the commit closes.

Breaking changes should start with `BREAKING CHANGE:` with a space or two newlines. The rest of the
commit message is then used for explaining the change.

## Questions

Have a question? Please avoid opening issues for general questions. Instead, it is much better to
ask your question on our [Discord server](https://discord.gg/wjWJwJB).

## Code of Conduct

This project is governed by [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
