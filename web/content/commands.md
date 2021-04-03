# General

## help

Show the help menu.

- Alias: about, info, commands

## ping

Show the bot latency.

## stats

Show the bot statistics.

- Alias: statistics

## dashboard

Get a link to the dashboard.

- Alias: website

## invite

Get a link to invite the bot.

## support

Get a link to the support server.

- Alias: server

## prefix

View or change the bot prefix.

- Usage: `[new prefix]`
- Permission: Manage Server

# Core

## connect

Have the bot connect to your channel.

- Alias: join

## disconnect

Have the bot disconnect from your channel.

- Alias: leave, dc
- Permission: Manage Player

## play

Play a song or add it to the queue.

- Usage: `<query>`
- Alias: p
- Permission: Add to Queue

## playfile

Play a song or add it to the queue from file upload.

- Alias: pf
- Permission: Add to Queue

## nowplaying

Display the currently playing track.

- Alias: np, playing

## queue

Display the queue.

- Alias: q

## effects

Display the player effects.

- Alias: filters

## equalizer

Display the player equalizer.

- Alias: eq

## lyrics

Display the lyrics for the current track.

- Alias: l

# Player

## pause

Pause the player.

- Alias: stop
- Permission: Manage Player

## resume

Resume the player.

- Alias: unpause, continue
- Permission: Manage Player

## forward

Fast forward the player.

- Usage: `<amount>`
- Alias: fw, fwd
- Permission: Manage Player

## rewind

Rewind the player.

- Usage: `<amount>`
- Alias: rw, rwd
- Permission: Manage Player

## seek

Seek the player to a position.

- Usage: `<position>`
- Permission: Manage Player

## loop

Change the player loop.

- Permission: Manage Player

## volume

Change the volume of the player.

- Usage: `<loudness>`
- Alias: vol
- Permission: Manage Player

# Queue

## next

Skip to the next track.

- Alias: skip, s
- Permission: Manage Player

## previous

Go back to the previous track.

- Alias: back, prev
- Permission: Manage Player

## jump

Jump to a certain track.

- Usage: `<item>`
- Alias: goto, j
- Permission: Manage Player

## remove

Remove a track from the queue.

- Usage: `<item>`
- Alias: rm, delete, del
- Permission: Manage Queue

## shuffle

Shuffle the tracks in the queue.

- Alias: shuf
- Permission: Manage Queue

## clear

Remove all the tracks in the queue.

- Permission: Manage Queue

# Playlist

## playlists

View the server's playlists.

- Alias: playlist, pl

## playlist create

Create a new playlist.

- Usage: `<name>`
- Alias: pl create, playlist new, pl new
- Permission: Manage Playlist

## playlist delete

Delete a playlist.

- Usage: `<name>`
- Alias: pl delete, playlist del, pl del
- Permission: Manage Playlist

## playlist show

Show the tracks in a playlist.

- Usage: `<name>`
- Alias: pl show, playlist view, pl view

## playlist load

Load a playlist into the queue.

- Usage: `<name>`
- Alias: pl load
- Permission: Add to Queue
