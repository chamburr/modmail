# Contributing to ModMail

Thank you for your interest in contributing!

The following is a set of guidelines, and it should provide a good overview of how you can get involved in contributing to ModMail.

## Reporting Bugs and Suggesting Features

We track bugs and features using the [GitHub issue tracker](https://github.com/chamburr/modmail/issues).

Before submitting a bug or a feature, please perform a search on the list of [issues](https://github.com/chamburr/modmail/issues) and check whether it has already been reported or suggested to prevent duplicates. In the case that you find the issue is closed however, read up on the issue and create a new one if necessary.

When writing the report or suggestion, please provide as much information as possible. For bugs, provide clear steps on how to reproduce the bug and include screenshots. For suggestions, provide a concise description on the feature. Generally, filling in the template would work well.

Following these guidelines will help maintainers and the community understand the bug or feature, and fix or implement them more quickly.

## Writing Code

Don't know where to begin? You can try looking at the list of [issues](https://github.com/chamburr/modmail/issues). We use the tags `bug` and `enhancement` to differientiate between bugs and features.

If you want to implement a new feature, you should always create an issue about it first. This will prevent situations where contributions are not helpful.

### Development Environment

To set up your local development environment, follow the self-hosting guide [here](https://github.com/chamburr/modmail/blob/master/README.md). When you successfully self-host the bot, your development environment should more or less be ready.

[Flake8](https://gitlab.com/pycqa/flake8) is a useful code analysis tool you may want to use.

### Coding Style

We use [black](https://github.com/psf/black) for code style and enforce a maximum of 120 characters per line. We also use [isort](https://github.com/timothycrosley/isort) to sort imports and keep them neat. Therefore, please always run `format.sh` before submitting a pull request.

### Submitting Pull Requests

When submitting a pull request, please write a clear title and description as it will help in the reviewing process. If your pull request fixes a bug or implements a feature in the issue tracker, please link that issue.

Take note that verbs in git commit messages should always be in present tense and use imperative mood.

## Questions

Have a question? Instead of opening an issues, please ask in our [Discord server](https://discord.gg/wjWJwJB) instead.
