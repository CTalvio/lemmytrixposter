# Lemmytrixposter

This is a matrix/lemmy bot for creating and saving lemmy posts. Run this as a systemd service, or some other way that keeps it always running, and you will then be able to control the bot via a matrix chat room whenever and wherever.

Simply send it an image, a link to an image, or link to a pixiv or danbooru page to create posts. You can also configure a folder from which the bot can pick random files to post using the "next" command.

### How does it work?

To create post, you send the matrix bot an image file or a link to an image file. You can also send a pixiv or danbooru URL.

The bot will reverse search the image using saucenao, and find the highest quality source image available.

If the file is more than 1MB, the image will be thumbnailed for the post, while the full file will still be linked in the post body.

A post title, artists credit, and a post body with social links will be generated, and suitable communities for the post will be pre-selected.

At this point you may edit any aspect of the post, post it once satisfied, save it to post later, or discard it.

Lemmytrixpster will host the image for the post on catbox.moe.

Lemmytrixposter keeps track of what you have already posted, and will notify you and ask for confirmation if you go to post something a second time without remembering.

Saved posts can be posted later using a command, or automatically, over time.

### Matrix bot usage

- Next/Rand/R - suggest a random image to post
- Status - show information about saved posts
- T *Title* - set a post title
- A *Artist* - set artist name
- Tt - translate title
- Ta - translate artist
- L *links* - links separated by spaces to include in the post body
- R - toggle post nsfw/sfw
- C *communities* - communities to post to, separated by spaces, accepts partial or full community names without leading "!"
- Post - post current post now
- Save - save current post for later
- Cancel - discard current post, neither posting nor saving
- Randompost - post a random saved post
- Stop - stop lemmytrixposter

When multiple communities are selected for a post, the bot will cross-post to them all.

## Quick start

Download the compiled executable for your platform from [releases](https://github.com/CTalvio/lemmytrixposter/releases).

Create a folder for lemmytrixposter and place the executable inside, run it once to create the `lemmytrixposter.toml` config file. Open it and edit it.

Once you have edited the config file, run the executable to start lemmytrixposter. To stop it, send "stop" in the matrix room.


### Running in python environment

Alternatively, you can run the tool in a python 3.10 environment. You will need:

- pythorhead
- langdetect
- hurry.filesize
- saucenao_api
- Pybooru
- pixivpy3
- pyupload
- deep_translator
- pillow

The pip commands to install these:
```
pip install pythorhead langdetect hurry.filesize Pybooru pixivpy3 pyupload deep_translator pillow simplematrixbotlib
```
```
pip install saucenao_api
```
Note that saucenao_api must have [this fix](https://github.com/nomnoms12/saucenao_api/pull/20) applied before it will work.

### Config

The tool is configured by editing `lemmytrixposter.toml`. If the file is missing, run lemmytrixposter once to create it.

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
