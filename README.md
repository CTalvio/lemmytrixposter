# Lemmytrixposter

This is a matrix/lemmy bot for creating and saving lemmy posts. Run this as a systemd service, or some other way that keeps it always running, and you will then be able to control the bot via a matrix chat room whenever and wherever.

Simply send it an image, a link to an image, or link to a pixiv or danbooru page to create posts. You can also configure a folder from which the bot can pick random files to post using the "next" command.

### Matrix bot usage

- next/rand/r - suggest a random image to post
- status - show information about saved posts
- t *Title* - set a post title
- a *Artist* - set artist name
- tt - translate title
- ta - translate artist
- r - toggle post nsfw/sfw
- c *communities* - communities to post to, separated by spaces, accepts partial or full community names without leading "!"
- post - post current post now
- save - save current post for later
- cancel - discard current post, neither posting nor saving
- stop - stop lemmytrixposter

When multiple communities are selected for a post, the bot will cross-post to them all.

# Setup

You can run the tool in a python 3.10 environment.

Alternatively download the compiled executable for your platform from [releases](https://github.com/CTalvio/lemmytrixposter/releases).

Download and place lemmytrixposter.py or the executable in a folder. Other folders and files will be created at this location, so placing it in a folder on its own is a good idea.

### Running in python environment

Skip section if you're using the executable.

- pythorhead
- langdetect
- hurry.filesize
- saucenao_api
- Pybooru
- pixivpy3
- pyupload
- deep_translator
- pillow

You can copy the commands below to install them all if running in a python environment.
```
pip install pythorhead langdetect hurry.filesize Pybooru pixivpy3 pyupload deep_translator pillow simplematrixbotlib
```
```
pip install saucenao_api
```
Note that saucenao_api must have [this fix](https://github.com/nomnoms12/saucenao_api/pull/20) applied before it will work.

### Config

Run the executable once to create the `lemmytrixposter.toml` config file. Open it and edit it.

You will need a matrix account for yourself, and another for the bot to use. Create these on any matrix instance you like.

Create a matrix room using your own account, and grab the room ID. Invite the bot user to the room.

Other things you will need:

- Lemmy account
- SauceNao API key
- Pixiv user token
- Danbooru API key

### Matrix-commander

Matrix commander is used to do a couple things simplebotlib is unable to do, it is not required, but is needed for the tool to be able to receive image files and send notifications when the bot creates posts on its own.

Set up is as follows:
```
pip install matrix-commander
```
Then configure it with the bot user and room that you've already set up by running:
```
matrix-commander --login
```

### Execution

To start the tool simply run the lemmytrixposter executable or python file.

To stop it, send "stop" in the chat room.
