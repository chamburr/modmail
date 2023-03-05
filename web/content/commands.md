# Configuration

## setup

Set up ModMail.

## prefix

Change the prefix or view the current prefix.

- Usage: `[new prefix]`
- Alias: setprefix

## category

Re-create the category for the ModMail channels.

- Usage: `[name]`

## accessrole

Set or clear the roles that have access to ticket related commands and replying to tickets.

- Usage: `[roles]`
- Alias: modrole, supportrole

## pingrole

Set or clear the roles mentioned when a ticket is opened. You can also use `everyone` and `here`.

- Usage: `[roles]`
- Alias: mentionrole

## logging

Toggle ticket logging and optionally in an existing channel.

- Usage: `[channel]`
- Alias: logs

## commandonly

Toggle whether commands are required to reply to a ticket.

- Alias: commandrequired

## greetingmessage

Set or clear the message that is sent when a new ticket is opened. Tags \`{username}\`, \`
{usertag}\`, \`{userid}\` and \`{usermention}\` can be used.

- Usage: `[text]`
- Alias: welcomemessage, greetmessage

## closingmessage

Set or clear the message that is sent when a ticket is closed. Tags \`{username}\`, \`{usertag}\`,
\`{userid}\` and \`{usermention}\` can be used.

- Usage: `[text]`
- Alias: goodbyemessage, closemessage

## loggingplus

Toggle advanced logging which includes messages sent and received.

- Alias: advancedlogging, advancedlogs

## anonymous

Toggle default anonymous messages.

## toggle

Toggle whether tickets can be created, optionally with reason if disabling.

- Usage: `[reason]`
- Alias: enable, disable

## viewconfig

View the configurations for the current server.

# Core

## reply

Reply to the ticket, useful when anonymous messaging is enabled.

- Usage: `<message>`

## areply

Reply to the ticket anonymously.

- Usage: `<message>`

## close

Close the channel.

- Usage: `[reason]`

## aclose

Close the channel anonymously.

- Usage: `[reason]`

## closeall

Close all of the channels.

- Usage: `[reason]`

## acloseall

Close all of the channels anonymously.

- Usage: `[reason]`

## blacklist

Blacklist a user to prevent them from creating tickets.

- Usage: `<member>`
- Alias: block

## whitelist

Whitelist a user to allow them to creating tickets.

- Usage: `<member>`
- Alias: unblock

## blacklistclear

Remove all users from the blacklist.

## viewblacklist

View the blacklist.

# Direct Message

## new

Send message to another server, useful when confirmation messages are disabled.

- Usage: `<message>`
- Alias: create, switch, change

## send

Shortcut to send message to a server.

- Usage: `<server ID> <message>`

## confirmation

Enable or disable the confirmation message.

# General

## help

Shows the help menu or information for a specific command when specified.

- Usage: `[command]`
- Alias: h, commands

## ping

Pong! Get my latency.

## stats

See some super cool statistics about me.

- Alias: statistics, info

## partners

See the amazing stuff we have partnered with.

## invite

Get a link to invite me.

## support

Get a link to my support server.

- Alias: server

## website

Get the link to ModMail's website.

## source

Get the link to ModMail's GitHub repository.

- Alias: github

# Miscellaneous

## permissions

Show a member's permission in a channel when specified.

- Usage: `[member] [channel]`
- Alias: perms

## userinfo

Show some information about yourself or the member specified.

- Usage: `[member]`
- Alias: memberinfo

## serverinfo

Get some information about this server.

- Alias: guildinfo

# Premium

## premium

Get some information about ModMail premium.

- Alias: donate, patron

## premiumstatus

Get the premium status of this server.

## viewpremium

Get a list of servers you assigned premium to.

- Alias: premiumlist

## premiumassign

Assign premium slot to a server.

- Usage: `<server ID>`

## premiumremove

Remove premium slot from a server.

- Usage: `<server ID>`

# Snippet

## snippet

Use a snippet.

- Usage: `<name>`
- Alias: s

## asnippet

Use a snippet anonymously.

- Usage: `<name>`
- Alias: as

## snippetadd

Add a snippet. Tags \`{username}\`, \`{usertag}\`, \`{userid}\` and \`{usermention}\` can be used.

- Usage: `<name> <content>`

## snippetremove

Remove a snippet.

- Usage: `<name>`

## snippetclear

Remove all the snippets.

## viewsnippet

View all the snippets or a specific one if specified.

- Usage: `[name]`
- Alias: viewsnippets, snippetlist
