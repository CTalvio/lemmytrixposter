# Lemmytrixposter

This is a matrix/lemmy bot for creating and saving lemmy posts. Run this as a systemd service, or some other way that keeps it always running, and you will then be able to control the bot via a matrix chat room whenever and wherever.

Simply send it an image, a link to an image, or link to a pixiv or danbooru page to create posts. You can also configure a folder from which the bot can pick random files to post using the "next" command.

The latest version is now able to maintain a database of artists, keeping track of which of their works you've already posted, as well as new and unposted works by them.

### How does it work?

To create a post, you start by sending the matrix bot an image file, or a link to an image file. You can also send a pixiv or danbooru URL.

If you've already entered a bunch of artists you like, or defined communities you want to post to, you can enter the "next" command to have the tool make a random suggestion based on tags/artists.

The bot will reverse search the image using saucenao, and find the highest quality source image available.

If the file is more than 1MB, the image will be thumbnailed for the post, while the full file will be linked in the post body.

A post title, artists credit, and a post body with social links will be generated, and suitable communities for the post will be pre-selected.

At this point you may edit any aspect of the post, post it once satisfied, save it to post later, or discard it.

Lemmytrixposter will host the image for the post on catbox.moe.

Lemmytrixposter keeps track of what you have already posted, and will notify you and ask for confirmation if you go to post something a second time without remembering.

Saved posts can be posted later using a command, or automatically, over time.

**If you end up finding this useful, maybe throw me a buck or two:** [ko-fi](https://ko-fi.com/mentaledge)

### Matrix bot usage

- When not editing a post
- next/N - suggest a random image to post
- reject/R - reject current random suggestion
- delete/D - delete current randomly suggested local file
- move/M - move randomly suggested local file to the "moved" folder
- select/S - select current random suggestion
- status - show information about saved posts
- randompost - post a random saved post
- add <artist_url> - add an artist to database, provide either the url of a pixiv artist page, or the first search page of an artist danbooru tag
- update <danbooru/pixiv/social> - force a complete update of danbooru, pixiv, or artist socials (the tool keeps the db up to date incrementally, using this should never be needed)
- stop - stop lemmytrixposter

When editing a post
- T <Title> - set a post title
- A <Artist> - set artist name
- Tt - translate title
- Ta - translate artist
- L <links> - links separated by spaces to include in the post body
- R - toggle post nsfw/sfw
- C <communities> - communities to post to, separated by spaces, accepts partial or full community names without leading "!"
- add - add current artist to database
- post - post current post now
- save - save current post for later
- cancel - discard current post, neither posting nor saving

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
- simplematrixbotlib

The pip commands to install these:
```
pip install pythorhead langdetect hurry.filesize Pybooru pixivpy3 pyupload deep_translator pillow simplematrixbotlib
```
```
pip install saucenao_api
```
Note that saucenao_api must have [this fix](https://github.com/nomnoms12/saucenao_api/pull/20) applied before it will work.

### Config

The tool is configured by editing `lemmytrixposter.toml`. If the file is missing, run lemmytrixposter once to create it. Further instruction are within the file.

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
