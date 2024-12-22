import simplematrixbotlib as botlib
from saucenao_api import SauceNao
from pixivpy3 import *
from pybooru import Danbooru
from pyupload.uploader import *
from pythorhead import Lemmy
from deep_translator import GoogleTranslator
from PIL import Image
from hurry.filesize import size
from hurry.filesize import alternative
from os import listdir
from langdetect import detect
from urllib.parse import urlparse

import sys
import re
import os
import json
import toml
import requests
import random
import glob
import shutil
import subprocess
import nio
import time
import threading
import pickle
import math

help_message = '''Simply send me an image, a link to an image, or link to a pixiv or danbooru page to create posts. If you configured a folder from which I can pick random files to post, use the "next" command to do this.

When not editing a post
next/N - suggest a random image to post
reject/R - reject current random suggestion
delete/D - delete current randomly suggested local file
move/M - move randomly suggested local file to the "moved" folder
select/S - select current random suggestion
status - show information about saved posts
randompost - post a random saved post
add <artist_url> - add an artist to database, provide either the url of a pixiv artist page, or the first search page of an artist danbooru tag
update <danbooru/pixiv/social> - force a complete update of danbooru, pixiv, or artist socials (the tool keeps these up to date incrementally, using this should never be needed)
stop - stop lemmytrixposter

When editing a post
T <Title> - set a post title
A <Artist> - set artist name
Tt - translate title
Ta - translate artist
L <links> - links separated by spaces to include in the post body
R - toggle post nsfw/sfw
C <communities> - communities to post to, separated by spaces, accepts partial or full community names without leading "!"
add - add current artist to database
post - post current post now
save - save current post for later
cancel - discard current post, neither posting nor saving
'''

default_config = '''# Path to a folder from which the tool can pull random images for you to make posts from.
# You can save images here to post them later, or point it to an existing stash :D
RandomSourcePath = "/path/to/a/folder"
# Whether to delete the source file that was used to create a post
# When set to true images in RandomSourcePath WILL BE DELETED as they get posted
DeleteOncePosted = false
# Whether to save a copy of the highest available quality file in a /posted folder for each image that is posted
SavePosted = true

# Whether the tool should attempt to automatically determine suitable communities, this is done using danbooru tags
# You can always override whatever is detected
AutoDetectCommunities = true

# Communities lemmytrixposter will try to keep active by finding posts for them when using "next" command
SuggestPostsFor = [
    "anime_art@ani.social",
]

# This list is used to autocomplete communites for you when their name is entered only partially.
# This makes editing posts faster, as you don't have to type the full names of communities.
# You can add any communities you want, and then easily post to them by writing just a few charachters of the name when using the "c" command.
# You can also list danbooru tags that you would like match to certain communities to auto-select images for posting to them.
# It also still possible to manually post to any community by entering the full name (without a !), even if not listed below.
[Communities]
"thighdeology@ani.social" = ['thighs', 'thick_thighs', 'thigh_focus']
"touhou@ani.social" = ['touhou']
"dungeonmeshi@ani.social" = ['dungeon_meshi']
"lycorisrecoil@reddthat.com" = ['lycoris_recoil']
"onepiece@lemmy.world" = ['one_piece']
"opm@lemmy.world" = ['one_punch_man']
"kawaii_braids@sh.itjust.works" = ['braid']
"dragonball@ani.social" = ['dragon_ball']
"mecha@lemm.ee" = ['robot', 'mecha']
"smolmoe@ani.social" = ['minigirl', 'aged_down', 'chibi', 'mini_person', ]
"murdermoe@lemmy.world" = ['yandere', 'evil_smile', 'evil_grin', 'crazy_eyes', 'blood_on_weapon']
"gothmoe@ani.social" = ['goth_fashion']
"morphmoe@ani.social" = ['personification']
"militarymoe@ani.social" = ['gun', 'military', 'body_armor']
"touch_fluffy_tail@ani.social" = ['fox_tail', 'wolf_tail', 'holding_own_tail']
"fangmoe@ani.social" = ['fang', 'fangs']
"streetmoe@ani.social" = ['streetwear', 'sneakers']
"thiccmoe@ani.social" = ['huge_breasts', 'large_breasts', 'thick_thighs', 'love_handles', 'plump', 'curvy', 'wide_hips', 'ass_focus', 'thigh_focus']
"officemoe@ani.social" = ['salaryman', 'office_lady', 'office_chair', 'office']
"meganemoe@ani.social" = ['glasses']
"chainsawfolk@lemmy.world" = ['chainsaw_man']
"helltaker@sopuli.xyz" = ['helltaker']
"bocchitherock@sopuli.xyz" = ['bocchi_the_rock!']
"overlord@sopuli.xyz" = ['overlord_(maruyama)']
"killlakill@lemmy.world" = ['kill_la_kill']
"hatsunemiku@lemmy.world" = ['hatsune_miku']
"cybermoe@ani.social" = ['cyberpunk', 'cyborg', 'science_fiction', 'mecha', 'robot', 'android']
"kemonomoe@ani.social" = ['animal_ears']
"fitmoe@lemmy.world" = ['muscular', 'toned', 'exercising', 'gym', 'weightlifting']
"midriffmoe@ani.social" = ['midriff', 'stomach']
"hololive@lemmy.world" = ['hololive']
"wholesomeyuri@reddthat.com" = ['yuri']
"frieren@ani.social" = ['sousou_no_frieren', 'frieren']
"animearmor@lemm.ee" = ['armor']
"FloatingIsFun@fedia.io" = ['floating']
"anime_art@ani.social" = []
"animepics@reddthat.com" = []
"sliceoflifeanime@lemmy.world" = []
"hitoribocchi@lemmy.world" =  ['hitoribocchi_no_marumaru_seikatsu']
"poputepipikku@lemmy.world" = ['poptepipic']

# SauceNao requires a key for API access, you can get a basic one by just making an account, the key can then be found under "api" in the account section
[SauceNao]
api_key = "keyyyyyyyyyyyyyyyyyyyyyyyy"

# Pixiv access token, to get one, create an account and follow the instructions here: https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362
[Pixiv]
token = "toooooooooooookeeeeeeeeeeen"

# Danbooru account and API key to access via API. You will need to create an account, then create an API key with post viewing privileges
[Danbooru]
username = "Username"
api_key = "keeeeeeeeeeeeeeeeeeeeeeeeey"

# Matrix details for the bot user which will be used to control the posting tool, you will need to both create the user and the room in advance.
# Once the bot is running, invite it to the room, it should then join and tell you it is ready.
[Matrix]
homeserver = "homeserv.er"
# Matrix bot user and password
bot_user = "@bot:homeserv.er"
bot_password = "passssword"
# Users that can interact with the bot (if multiple, separate entries with commas within square brackets), and the room it should operate in
user_whitelist = "@user:homeserv.er"
room = "!IIIIIIIDDDDDDDD:homeserv.er"
# Path to a folder containing matrix commander "store" folder and "creds.json"
# If you used the default credentials location (just used --login), leave as is
matrix_commander = ""

# Lemmy account credentials which will be used to create posts
[Lemmy]
instance = "instan.ce"
username = "Username"
password = "passwooooord"

# Trickle posting settings, the tool will post random saved posts, waiting a random amount
# of time between the minimum and maximum number of minutes defined here between each post
[Timer]
# Set to false to disable automated posting of saved posts
enabled = true
min_wait = 20
max_wait = 240
# Randomly post more than one post up to this burst count
rand_burst = 1
# Whether multi-community posts should have cross-posts created all at once, or to only
# create one post at a time and thereby create the cross-posts over time as their own posts
# Posts will still be cross-posts, but essentially become staggered, posted at different times
cross_post_all_at_once = false'''

default_artists = '''#This file will store artist enries. Talk to the matrix bot to add artists.'''

if not os.path.isfile(os.path.curdir+'/lemmytrixposter.toml'):
    f = open(os.path.curdir+'/lemmytrixposter.toml', 'w')
    f.write(default_config)
    f.close()
    print('Lemmytrixposter has not been configured, created sample config file')
    print('Please follow instructions within for setup')
    sys.exit()

if not os.path.isfile(os.path.curdir+'/artists.toml'):
    f = open(os.path.curdir+'/artists.toml', 'w')
    f.write(default_artists)
    f.close()

# Load configs
config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
artists_config = toml.load(open(os.path.curdir+'/artists.toml', 'r'))

# saucenao
sauce = SauceNao(config['SauceNao']['api_key'], numres=10)

# danbooru
headers = {'User-Agent': 'Danbooru user '+config['Danbooru']['username']}
danbooru = Danbooru('danbooru', username=config['Danbooru']['username'], api_key=config['Danbooru']['api_key'])

# matrix-commander
mc_path = config['Matrix']['matrix_commander']

# prepare some directories
if not os.path.exists(os.path.curdir+'/tmp'):
    os.mkdir(os.path.curdir+'/tmp')
if not os.path.exists(os.path.curdir+'/tmp/lemmytrixposter'):
    os.mkdir(os.path.curdir+'/tmp/lemmytrixposter')
if not os.path.exists(os.path.curdir+'/posted'):
    os.mkdir(os.path.curdir+'/posted')
if not os.path.exists(os.path.curdir+'/saved'):
    os.mkdir(os.path.curdir+'/saved')
if not os.path.exists(os.path.curdir+'/moved'):
    os.mkdir(os.path.curdir+'/moved')
if not os.path.exists(os.path.curdir+'/error'):
    os.mkdir(os.path.curdir+'/error')


# Load/Create the artist/post/tag table
def load_and_update_datatable(data=None):
    global artists_config
    config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
    artists_config = toml.load(open(os.path.curdir+'/artists.toml', 'r'))

    if not os.path.exists(os.path.curdir+'/data.pickle'):
        data = {'artists': {}, 'tags': {}, 'posted': {'pixiv': [], 'danbooru': [], 'catbox': []}}
    else:
        data = pickle.load(open(os.path.curdir+'/data.pickle', 'rb'))

    for artist, socials in artists_config.items():
        # Create artist entry
        if artist not in data['artists']:
            data['artists'][artist] = {}
        # Update socials
        data['artists'][artist]['socials'] = socials
        # Create danbooru table
        if 'danbooru' in socials and 'danbooru' not in data['artists'][artist]:
            data['artists'][artist]['danbooru'] = {
                'artist_tag': socials['danbooru'],
                'posted': [],
                'rejected': [],
                'unposted': {}
            }
        # Create pixiv table
        if 'pixiv' in socials and 'pixiv' not in data['artists'][artist]:
            data['artists'][artist]['pixiv'] = {
                'user_id': socials['pixiv'],
                'posted': [],
                'rejected': [],
                'unposted': []
            }

    # Delete removed artists from datatable
    to_delete = []
    for artist, details in data['artists'].items():
        if artist not in artists_config:
            to_delete.append(artist)
    for artist in to_delete:
        print('removed artist: '+artist)
        del data['artists'][artist]

    for community, tags in config['Communities'].items():
        for tag in tags:
            if tag in data['tags'] and community != data['tags'][tag]['community']:
                data['tags'][tag]['community'] = community
            if tag not in data['tags']:
                data['tags'][tag] = {
                    'community': community,
                    'posted': [],
                    'rejected': [],
                    'unposted': {}
                }

    # Load old "posted" data if present
    if os.path.isfile(os.path.curdir+'/posted.json'):
        print('Old posted.json found, loading into datatable...')

        # pixiv
        pixiv = AppPixivAPI()
        pixiv.auth(refresh_token=config['Pixiv']['token'])

        postedIDs = json.load(open(os.path.curdir+'/posted.json', 'r'))
        amount = len(postedIDs)
        entry = 0
        # printProgressBar(entry, amount, prefix = 'Loading posted.json:', suffix = 'Complete', length = 50)
        for posted_id in postedIDs:
            entry += 1
            # printProgressBar(entry, amount, prefix = 'Loading posted.json:', suffix = 'Complete', length = 50)
            if 'danbooru' in posted_id:
                danbooru_id = posted_id.replace('danbooru', '')
                if danbooru_id not in data['posted']['danbooru']:
                    data['posted']['danbooru'].append(danbooru_id)
            if 'pixiv' in posted_id:
                pixiv_id = posted_id.replace('pixiv', '')
                if pixiv_id not in data['posted']['pixiv']:
                    post = pixiv.illust_detail(pixiv_id).illust
                    if post and post.meta_single_page:
                        data['posted']['pixiv'].append(pixiv_id)
            if 'catbox' in posted_id:
                filename = posted_id.replace('catbox', '')
                if filename not in data['posted']['catbox']:
                    data['posted']['catbox'].append(filename)

    # Typecheck
    for artist in data['artists'].values():
        if 'pixiv' in artist:
            for entry in artist['pixiv']['unposted']:
                if type(entry) is not str:
                    print('there is a non string entry in pixiv unposted!')
                    sys.exit()
            for entry in artist['pixiv']['posted']:
                if type(entry) is not str:
                    print('there is a non string entry in pixiv posted!')
                    sys.exit()
            for entry in artist['pixiv']['rejected']:
                if type(entry) is not str:
                    print('there is a non string entry in pixiv posted!')
                    sys.exit()

    for artist in data['artists'].values():
        if 'danbooru' in artist:
            for entry in artist['danbooru']['unposted'].keys():
                if type(entry) != str:
                    print('there is a non string key in danbooru unposted!')
                    sys.exit()
            for entry in artist['danbooru']['posted']:
                if type(entry) != str:
                    print('there is a non string entry in danbooru posted!')
                    sys.exit()
            for entry in artist['danbooru']['rejected']:
                if type(entry) != str:
                    print('there is a non string entry in danbooru rejected!')
                    sys.exit()

    with open(os.path.curdir+'/data.pickle', 'wb') as handle:
        pickle.dump(data, handle)

    return data


# Print iterations progress
def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * min((iteration / float(total), 1.0)))
    filledLength = min(int(length * iteration // total), length)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration >= total:
        print()


def get_artist_key(postData=None, pixiv_id=None, danbooru_tag=None):
    artists_config = toml.load(open(os.path.curdir+'/artists.toml', 'r'))
    # Check pixiv
    if postData and 'pixivData' in postData and 'user' in postData['pixivData']:
        pixiv_id = postData['pixivData'].user.id
    elif postData and 'pixivID' in postData:
        config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
        pixiv = AppPixivAPI()
        pixiv.auth(refresh_token=config['Pixiv']['token'])
        illust = pixiv.illust_detail(postData['pixivID']).illust
        if illust:
            pixiv_id = illust.user.id
    if pixiv_id:
        for artist, socials in artists_config.items():
            if 'pixiv' in socials and str(pixiv_id) == socials['pixiv']:
                return artist
    # Check danbooru
    if postData and 'danbooruData' in postData:
        danbooru_tag = postData['danbooruData']['tag_string_artist']
    elif postData and 'danbooruID' in postData:
        danbooru_tag = danbooru.post_show(postData['danbooruID'])['tag_string_artist']
    if danbooru_tag:
        for artist, socials in artists_config.items():
            if 'danbooru' in socials and danbooru_tag == socials['danbooru']:
                return artist
    return False


# Add artist to the saved list
def add_artist(input_string=None, postData=None):
    global data
    global artists_config
    if not input_string:
        if 'danbooruData' in postData:
            input_string = 'https://danbooru.donmai.us/posts?tags='+postData['danbooruData']['tag_string_artist']
        elif 'pixivData' in postData:
            input_string = 'https://www.pixiv.net/en/users/'+str(postData['pixivData']['user']['id'])
    input_string = input_string.replace('%27', '\'').replace('%28', '(').replace('%29', ')').split('+')[0]
    if 'pixiv' in input_string:
        config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
        pixiv = AppPixivAPI()
        pixiv.auth(refresh_token=config['Pixiv']['token'])
        user_details = pixiv.user_detail(re.search('\d{5,9}', input_string).group(0))
        if not get_artist_key(pixiv_id=user_details.user.id):
            artists_config[user_details.user.name] = {'pixiv': str(user_details.user.id)}
            update_artist_socials(user_details.user.name.split('@')[0])
            data = load_and_update_datatable(data)
            data = update_danbooru(data, user_details.user.name.split('@')[0])
            data = update_pixiv(data, user_details.user.name)
            return('Added artist based on pixiv account: '+user_details.user.name.split('@')[0])
        else:
            return('This artist is already known!')

    if 'danbooru' in input_string and 'tags=' in input_string:
        artist_tag = input_string.split('tags=')[1].split('&')[0]
        if not get_artist_key(danbooru_tag=artist_tag):
            artists_config[artist_tag] = {'danbooru': artist_tag}
            update_artist_socials(artist_tag)
            data = load_and_update_datatable(data)
            data = update_danbooru(data, artist_tag)
            data = update_pixiv(data, artist_tag)
            return('Added artist based on danbooru artist tag: '+artist_tag)
        else:
            return('This artist is already known!')


# Add missing artist social links to a post, if they are known
def add_missing_socials(postData):
    artists_config = toml.load(open(os.path.curdir+'/artists.toml', 'r'))
    key = get_artist_key(postData)
    if key:
        socials = artists_config[key]
        for platform, url_id in socials.items():
            if platform == 'danbooru' and 'danbooruURL' not in postData:
                postData['danbooruURL'] = 'https://danbooru.donmai.us/posts?tags=rating%3Asafe+'+url_id
            if platform == 'pixiv' and 'pixivURL' not in postData:
                postData['pixivURL'] = 'https://www.pixiv.net/en/users/'+url_id
            if platform == 'artstation' and 'artstationURL' not in postData:
                postData['artstationURL'] = url_id
            if platform == 'bluesky':
                postData['blueskyURL'] = url_id
            if platform == 'twitter' and 'twitterURL' not in postData:
                postData['twitterURL'] = 'https://twitter.com/'+url_id
            if platform == 'linktree':
                postData['linktreeURL'] = url_id
            if platform == 'tumblr':
                postData['tumblrURL'] = url_id
            if platform == 'fediverse':
                postData['fediverseURL'] = url_id
            if platform == 'kofi':
                postData['kofiURL'] = url_id
            if platform == 'patreon':
                postData['patreonURL'] = url_id
            if platform == 'newgrounds':
                postData['newgroundsURL'] = url_id
    return postData


# Check whether post is repost
def check_if_repost(postData):
    try:
        artist = get_artist_key(postData)
        socials = artists_config[artist]
    except Exception:
        socials = False
    # Check know artists
    if socials:
        if 'danbooruID' in postData and 'danbooru' in socials:
            if postData['danbooruID'] in data['artists'][artist]['danbooru']['posted']:
                return True
            if postData['danbooruID'] in data['artists'][artist]['danbooru']['rejected']:
                return True
        if 'pixivID' in postData and 'pixiv' in socials:
            if postData['pixivID'] in data['artists'][artist]['pixiv']['posted']:
                return True
            if postData['pixivID'] in data['artists'][artist]['pixiv']['rejected']:
                return True
    # Check in tags
    if 'danbooruData' in postData:
        for tag in postData['danbooruData']['tag_string'].split():
            if tag in data['tags']:
                if postData['danbooruID'] in data['tags'][tag]['posted']:
                    return True
                if postData['danbooruID'] in data['tags'][tag]['rejected']:
                    return True
    # Check other posts
    if 'danbooruID' in postData and postData['danbooruID'] in data['posted']['danbooru']:
        return True
    if 'pixivID' in postData and postData['pixivID'] in data['posted']['pixiv']:
        return True
    if 'postURL' in postData and postData['postURL'] in data['posted']['catbox']:
        return True


# Attempt to update the socials of an artist/all artists
def update_artist_socials(artist_to_update=None):
    global artists_config
    print('Trying to find all links for artist socials...')

    # pixiv
    config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
    pixiv = AppPixivAPI()
    pixiv.auth(refresh_token=config['Pixiv']['token'])

    # load artists
    artist_amount = len(artists_config)
    this_artist = 0
    for artist, socials in artists_config.items():
        this_artist += 1
        if not artist_to_update:
            printProgressBar(this_artist, artist_amount, prefix = 'Updating artist socials:', suffix = 'Complete - '+artist+'                        ', length = 50)
        if not artist_to_update or artist_to_update == artist:
            if 'pixiv' in socials:
                if 'twitter' not in artists_config[artist] or 'fediverse' not in artists_config[artist]:
                    for i in range(6):
                        pixiv_user = pixiv.user_detail(socials['pixiv'])
                        if pixiv_user and 'profile' in pixiv_user:
                            pixiv_user_posts = pixiv_user['profile']['total_illusts']
                            break
                        if pixiv_user and 'error' in pixiv_user:
                            break
                        time.sleep(20)

                    if pixiv_user and pixiv_user.profile:

                        if 'twitter' not in artists_config[artist] and pixiv_user.profile.twitter_account:
                            artists_config[artist]['twitter'] = pixiv_user.profile.twitter_account
                            print('Updated ' + artist + ' with twitter handle: ' + artists_config[artist]['twitter']+'                                                               ')

                        if 'fediverse' not in artists_config[artist] and pixiv_user.profile.pawoo_url:
                            response = requests.get(pixiv_user.profile.pawoo_url)
                            if response.ok:
                                artists_config[artist]['fediverse'] = response.url
                                print('Updated ' + artist + ' with fediverse url: ' + artists_config[artist]['fediverse']+'                                                               ')
                    else:
                        print('invalid pixiv artist entry: '+artist+'/'+socials['pixiv']+'                                                               ')
                        print(pixiv_user)

                if 'danbooru' not in artists_config[artist]:
                    danbooru_artist = danbooru.artist_list(url='https://www.pixiv.net/en/users/'+socials['pixiv'])
                    if len(danbooru_artist) == 1:
                        artists_config[artist]['danbooru'] = danbooru_artist[0]['name']
                        print('Updated ' + artist + ' with danbooru tag: ' + artists_config[artist]['danbooru']+'                                                               ')

            if 'danbooru' in socials:
                danbooru_artist = danbooru.artist_list(name=socials['danbooru'])
                if len(danbooru_artist) > 0:
                    for entry in danbooru_artist:
                        if entry['name'] == socials['danbooru']:
                            danbooru_artist = [entry]
                            break
                if len(danbooru_artist) == 1:
                    artist_urls = danbooru.artist_urls(danbooru_artist[0]['id'])
                    for entry in artist_urls:
                        if entry['is_active']:
                            if 'fediverse' not in artists_config[artist]:
                                if 'pawoo.net/@' in entry['url'] or 'misskey.io/@' in entry['url'] or 'mastodon.social/@' in entry['url']:
                                    artists_config[artist]['fediverse'] = entry['url']
                                    print('Updated ' + artist + ' with fediverse url: ' + artists_config[artist]['fediverse']+'                                                               ')

                            if 'pixiv' not in artists_config[artist] and 'pixiv.net/users' in entry['url']:
                                artists_config[artist]['pixiv'] = re.search('\d{5,9}', entry['url']).group(0)
                                print('Updated ' + artist + ' with pixiv id: ' + artists_config[artist]['pixiv']+'                                                               ')

                            if 'tumblr' not in artists_config[artist] and 'tumblr' in entry['url']:
                                artists_config[artist]['tumblr'] = entry['url']
                                print('Updated ' + artist + ' with tumblr url: ' + artists_config[artist]['tumblr']+'                                                               ')

                            if 'bluesky' not in artists_config[artist] and 'bsky.app' in entry['url'] and 'did:plc:' not in entry['url']:
                                artists_config[artist]['bluesky'] = entry['url']
                                print('Updated ' + artist + ' with bluesky url: ' + artists_config[artist]['bluesky']+'                                                               ')

                            if 'twitter' not in artists_config[artist] and 'twitter.com' in entry['url'] and 'user' not in entry['url']:
                                artists_config[artist]['twitter'] = entry['url'].split('.com/')[1].split('/')[0]
                                print('Updated ' + artist + ' with twitter handle: ' + artists_config[artist]['twitter']+'                                                               ')

                            if 'deviant' not in artists_config[artist] and 'deviantart.com' in entry['url']:
                                artists_config[artist]['deviant'] = entry['url']
                                print('Updated ' + artist + ' with deviant url: ' + artists_config[artist]['deviant']+'                                                               ')

                            if 'linktree' not in artists_config[artist] and 'linktr.ee' in entry['url']:
                                artists_config[artist]['linktree'] = entry['url']
                                print('Updated ' + artist + ' with linktree url: ' + artists_config[artist]['linktree']+'                                                               ')

                            if 'artstation' not in artists_config[artist] and 'artstation.com' in entry['url']:
                                artists_config[artist]['artstation'] = entry['url']
                                print('Updated ' + artist + ' with artstation url: ' + artists_config[artist]['artstation']+'                                                               ')

                            if 'patreon' not in artists_config[artist] and 'patreon.com' in entry['url']:
                                artists_config[artist]['patreon'] = entry['url']
                                print('Updated ' + artist + ' with patreon url: ' + artists_config[artist]['patreon']+'                                                               ')

                            if 'kofi' not in artists_config[artist] and 'ko-fi.com' in entry['url']:
                                artists_config[artist]['kofi'] = entry['url']
                                print('Updated ' + artist + ' with ko-fi url: ' + artists_config[artist]['kofi']+'                                                               ')

                            if 'newgrounds' not in artists_config[artist] and 'newgrounds.com' in entry['url']:
                                artists_config[artist]['newgrounds'] = entry['url']
                                print('Updated ' + artist + ' with newgrounds url: ' + artists_config[artist]['newgrounds']+'                                                               ')
                else:
                    print('invalid danbooru artist entry: '+artist+'/'+socials['danbooru']+'                                                               ')

    with open(os.path.curdir+'/artists.toml', 'w') as handle:
        toml.dump(artists_config, handle)


# Mark a post as posted
def mark_as_posted(postData, write=True):
    print('attempting to mark a post as posted')
    global data
    artist = get_artist_key(postData)
    if artist:
        socials = artists_config[artist]
        if 'danbooru' in socials and 'danbooruID' in postData:
            print('unposted before: '+str(len(data['artists'][artist]['danbooru']['unposted'])))
            print('posted before: '+str(len(data['artists'][artist]['danbooru']['posted'])))
            print('successfully marked danbooru item as posted in artist data: '+artist+'/'+postData['danbooruID'])
            print('the post id is a '+str(type(postData['danbooruID'])))
            for key in data['artists'][artist]['danbooru']['unposted'].keys():
                if type(key) == str:
                    print('this key is a string')
                    break
            for key in data['artists'][artist]['danbooru']['unposted'].keys():
                if type(key) == int:
                    print('this key is an int')
                    break
            if postData['danbooruID'] in data['artists'][artist]['danbooru']['unposted']:
                del data['artists'][artist]['danbooru']['unposted'][postData['danbooruID']]
                print('danbooru key entry was deleted')
            data['artists'][artist]['danbooru']['posted'].append(postData['danbooruID'])
            print('unposted after: '+str(len(data['artists'][artist]['danbooru']['unposted'])))
            print('posted after: '+str(len(data['artists'][artist]['danbooru']['posted'])))

        if 'pixiv' in socials and 'pixivID' in postData:
            print('successfully marked pixiv item as posted in artist data: '+artist+'/'+postData['pixivID'])
            if postData['pixivID'] in data['artists'][artist]['pixiv']['unposted']:
                data['artists'][artist]['pixiv']['unposted'].remove(postData['pixivID'])
                print('pixiv key entry was deleted')
            data['artists'][artist]['pixiv']['posted'].append(postData['pixivID'])

    if 'danbooruTags' in postData:
        for tag in data['tags'].keys():
            if tag in postData['danbooruTags']:
                print('successfully marked tag item as posted in tag data: '+tag)
                if postData['danbooruID'] in data['tags'][tag]['unposted']:
                    del data['tags'][tag]['unposted'][postData['danbooruID']]
                    print('tag key entry was deleted')
                data['tags'][tag]['posted'].append(postData['danbooruID'])

    data['posted']['catbox'].append(os.path.basename(postData['postURL']))
    if not artist:
        print('successfully marked item as posted outside artist entry')
        if 'danbooruID' in postData:
            data['posted']['danbooru'].append(postData['danbooruID'])
        if 'pixivID' in postData:
            data['posted']['pixiv'].append(postData['pixivID'])

    if write:
        with open(os.path.curdir+'/data.pickle', 'wb') as handle:
            pickle.dump(data, handle)


# Mark a post as rejected
def mark_as_rejected(postData):
    print('attempting to mark a post as rejected')
    global data
    artist = get_artist_key(postData)
    if 'rejected' in postData and postData['rejected']:
        return
    postData['rejected'] = True
    if artist:
        socials = artists_config[artist]
        if 'danbooru' in socials and 'danbooruID' in postData:
            print('unposted before: '+str(len(data['artists'][artist]['danbooru']['unposted'])))
            print('rejected before: '+str(len(data['artists'][artist]['danbooru']['rejected'])))
            print('successfully marked danbooru item as rejected in artist data: '+artist+'/'+str(postData['danbooruID']))
            if postData['danbooruID'] in data['artists'][artist]['danbooru']['unposted']:
                del data['artists'][artist]['danbooru']['unposted'][postData['danbooruID']]
                print('danbooru key entry was deleted')
            data['artists'][artist]['danbooru']['rejected'].append(postData['danbooruID'])
            print('unposted after: '+str(len(data['artists'][artist]['danbooru']['unposted'])))
            print('rejected after: '+str(len(data['artists'][artist]['danbooru']['rejected'])))

        if 'pixiv' in socials and 'pixivID' in postData:
            print('successfully marked pixiv item as rejected in artist data: '+artist+'/'+postData['pixivID'])
            if postData['pixivID'] in data['artists'][artist]['pixiv']['unposted']:
                data['artists'][artist]['pixiv']['unposted'].remove(postData['pixivID'])
                print('pixiv key entry was deleted')
            data['artists'][artist]['pixiv']['rejected'].append(postData['pixivID'])

    if 'danbooruTags' in postData:
        for tag in data['tags'].keys():
            if tag in postData['danbooruTags']:
                print('successfully marked tag item as rejected in tag data: '+tag)
                if postData['danbooruID'] in data['tags'][tag]['unposted']:
                    del data['tags'][tag]['unposted'][postData['danbooruID']]
                    print('tag key entry was deleted')
                data['tags'][tag]['rejected'].append(postData['danbooruID'])

    with open(os.path.curdir+'/data.pickle', 'wb') as handle:
        pickle.dump(data, handle)


# Completely purge any entries related to a post from the db
def delete_post(postData):
    global data
    artist = get_artist_key(postData)
    if artist:
        socials = artists_config[artist]
        if 'danbooru' in socials and 'danbooruID' in postData:
            if postData['danbooruID'] in data['artists'][artist]['danbooru']['unposted']:
                del data['artists'][artist]['danbooru']['unposted'][postData['danbooruID']]
            if postData['danbooruID'] in data['artists'][artist]['danbooru']['rejected']:
                data['artists'][artist]['danbooru']['rejected'].remove(postData['danbooruID'])
            if postData['danbooruID'] in data['artists'][artist]['danbooru']['posted']:
                data['artists'][artist]['danbooru']['posted'].remove(postData['danbooruID'])


        if 'pixiv' in socials and 'pixivID' in postData:
            print('successfully marked pixiv item as rejected in artist data: '+artist+'/'+postData['pixivID'])
            if postData['pixivID'] in data['artists'][artist]['pixiv']['unposted']:
                data['artists'][artist]['pixiv']['unposted'].remove(postData['pixivID'])
            if postData['pixivID'] in data['artists'][artist]['pixiv']['rejected']:
                data['artists'][artist]['pixiv']['rejected'].remove(postData['pixivID'])
            if postData['pixivID'] in data['artists'][artist]['pixiv']['posted']:
                data['artists'][artist]['pixiv']['posted'].remove(postData['pixivID'])

    if 'danbooruTags' in postData:
        for tag in data['tags'].keys():
            if tag in postData['danbooruTags']:
                print('successfully marked tag item as rejected in tag data: '+tag)
                if postData['danbooruID'] in data['tags'][tag]['unposted']:
                    del data['tags'][tag]['unposted'][postData['danbooruID']]
                if postData['danbooruID'] in data['tags'][tag]['rejected']:
                    data['tags'][tag]['rejected'].remove(postData['danbooruID'])
                if postData['danbooruID'] in data['tags'][tag]['posted']:
                    data['tags'][tag]['posted'].remove(postData['danbooruID'])


    with open(os.path.curdir+'/data.pickle', 'wb') as handle:
        pickle.dump(data, handle)


def does_pixiv_exist(details, image_id):
    if image_id in details['pixiv']['rejected']:
        return True
    if image_id in details['pixiv']['posted']:
        return True
    if image_id in details['pixiv']['unposted']:
        return True
    return False


# Update pixiv posts
def update_pixiv(data, artist_to_update=None):

    # pixiv
    config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
    pixiv = AppPixivAPI()
    pixiv.auth(refresh_token=config['Pixiv']['token'])

    artist_amount = len(data['artists'])
    this_artist = 0

    if not artist_to_update:
        printProgressBar(this_artist, artist_amount, prefix = 'Updating pixiv artists:', suffix = 'Complete', length = 50)
    for artist, details in data['artists'].items():
        this_artist += 1
        if not artist_to_update:
            printProgressBar(this_artist, artist_amount, prefix = 'Updating pixiv artists:', suffix = 'Complete - '+artist+'                        ', length = 50)
        if not artist_to_update or artist_to_update == artist:
            if 'pixiv' not in details:
                continue
            to_replace = []
            for post_id in details['pixiv']['posted']:
                if post_id not in to_replace:
                    to_replace.append(post_id)
            data['artists'][artist]['pixiv']['posted'] = to_replace
            to_replace = []
            for post_id in details['pixiv']['unposted']:
                if post_id not in to_replace:
                    to_replace.append(post_id)
            data['artists'][artist]['pixiv']['unposted'] = to_replace
            to_replace = []
            for post_id in details['pixiv']['rejected']:
                if post_id not in to_replace:
                    to_replace.append(post_id)
            data['artists'][artist]['pixiv']['rejected'] = to_replace

            pixiv_user_posts = 30
            known_user_posts = 0
            for post_id in details['pixiv']['posted']:
                if '_' not in post_id or '_p0' in post_id:
                    known_user_posts += 1
            for post_id in details['pixiv']['unposted']:
                if '_' not in post_id or '_p0' in post_id:
                    known_user_posts += 1
            for post_id in details['pixiv']['rejected']:
                if '_' not in post_id or '_p0' in post_id:
                    known_user_posts += 1

            for i in range(6):
                pixiv_user = pixiv.user_detail(details['pixiv']['user_id'])
                if pixiv_user and 'profile' in pixiv_user:
                    pixiv_user_posts = pixiv_user['profile']['total_illusts']
                    break
                if pixiv_user and 'error' in pixiv_user:
                    break
                time.sleep(20)

            if pixiv_user_posts > known_user_posts:
                posts = []
                next_qs = {'user_id': details['pixiv']['user_id'], 'type': 'illust'}
                while next_qs is not None:
                    for i in range(6):
                        user_illusts = pixiv.user_illusts(**next_qs)
                        if user_illusts and 'illusts' in user_illusts:
                            next_qs = pixiv.parse_qs(user_illusts.next_url)
                            break
                        time.sleep(20)
                    if user_illusts and 'illusts' in user_illusts:
                        for illust in user_illusts['illusts']:
                            if illust not in posts:
                                posts.append(illust)
                    elif user_illusts and 'error' in user_illusts:
                        print('invalid pixiv ID for '+artist+'                                                        ')
                        break
                    else:
                        print('failed to avoid rate limiting                                                          ')
                    if len(posts)+known_user_posts >= pixiv_user_posts:
                        break

                if posts:
                    for post in posts:
                        if post.meta_single_page:
                            if does_pixiv_exist(details, str(post.id)):
                                continue
                            else:
                                data['artists'][artist]['pixiv']['unposted'].append(str(post.id))
                        else:
                            for image in post.meta_pages:
                                image_id = os.path.basename(image.image_urls.original).split('.')[0]
                                if does_pixiv_exist(details, image_id):
                                    continue
                                else:
                                    data['artists'][artist]['pixiv']['unposted'].append(image_id)
                else:
                    print('unable to update pixiv for '+artist+'                                                                   ')

            # Move any posted posts to posted
            to_remove = []
            for post_id in data['artists'][artist]['pixiv']['unposted']:
                if post_id in data['posted']['pixiv'] or post_id in data['artists'][artist]['pixiv']['posted']:
                    print('marked post '+post_id+' as posted for '+artist+'                                                                   ')
                    to_remove.append(post_id)
            for post_id in to_remove:
                if post_id not in data['artists'][artist]['pixiv']['posted']:
                    data['artists'][artist]['pixiv']['posted'].append(post_id)
                while post_id in data['artists'][artist]['pixiv']['unposted']:
                    data['artists'][artist]['pixiv']['unposted'].remove(post_id)

    with open(os.path.curdir+'/data.pickle', 'wb') as handle:
        pickle.dump(data, handle)
    return data


# Update new unposted posts for each/an artist
def update_danbooru(data, artist_to_update=None):
    artist_amount = len(data['artists'])
    this_artist = 0
    if not artist_to_update:
        printProgressBar(this_artist, artist_amount, prefix = 'Updating danbooru artists:', suffix = 'Complete', length = 50)
    for artist, details in data['artists'].items():
        this_artist += 1
        if not artist_to_update:
            printProgressBar(this_artist, artist_amount, prefix = 'Updating danbooru artists:', suffix = 'Complete - '+artist+'                        ', length = 50)
        if not artist_to_update or artist_to_update == artist:
            if 'danbooru' not in details:
                continue

            added = 0
            processed = 0
            update_complete = False
            amount = danbooru.count_posts('-rating:explicit, '+details['danbooru']['artist_tag'])['counts']['posts']
            amount_known = len(details['danbooru']['rejected'])+len(details['danbooru']['posted'])+len(details['danbooru']['unposted'])
            page = math.ceil(amount / 100) - math.floor(amount_known / 100)
            if amount_known < amount:
                while (True):
                    posts = danbooru.post_list(limit=100, page=page, tags='-rating:explicit, '+details['danbooru']['artist_tag'])
                    page -= 1
                    for post in posts:
                        processed += 1
                        if str(post['id']) in details['danbooru']['rejected'] or str(post['id']) in details['danbooru']['posted'] or str(post['id']) in details['danbooru']['unposted']:
                            if amount_known+added >= amount:
                                update_complete = True
                                break
                            continue
                        else:
                            if 'animated' in post['tag_string_general'].split():
                                data['artists'][artist]['danbooru']['rejected'].append(str(post['id']))
                            else:
                                data['artists'][artist]['danbooru']['unposted'][str(post['id'])] = post['tag_string'].split()
                                added += 1

                    if page <= 0 or update_complete:
                        with open(os.path.curdir+'/data.pickle', 'wb') as handle:
                            pickle.dump(data, handle)
                        break

            # Move any posted posts to posted
            to_mark_posted = []
            for post_id, tags in data['artists'][artist]['danbooru']['unposted'].items():
                if post_id in data['posted']['danbooru'] or post_id in data['artists'][artist]['danbooru']['posted']:
                    print('marked post '+post_id+' as posted for '+artist+'                                                               ')
                    to_mark_posted.append(post_id)
            for post_id in to_mark_posted:
                data['artists'][artist]['danbooru']['posted'].append(post_id)
                del data['artists'][artist]['danbooru']['unposted'][post_id]

            to_mark_rejected = []
            # Move any rejected posts to rejected
            for post_id, tags in data['artists'][artist]['danbooru']['unposted'].items():
                if post_id in data['artists'][artist]['danbooru']['rejected']:
                    print('marked post '+post_id+' as rejected for '+artist+'                                                               ')
                    to_mark_rejected.append(post_id)
            # Move any animated content to rejected
            for post_id, tags in data['artists'][artist]['danbooru']['unposted'].items():
                if 'animated' in tags:
                    print('removed post '+post_id+' for '+artist+' because it is an animation                                             ')
                    to_mark_rejected.append(post_id)

            for post_id in to_mark_rejected:
                data['artists'][artist]['danbooru']['rejected'].append(post_id)
                del data['artists'][artist]['danbooru']['unposted'][post_id]

    with open(os.path.curdir+'/data.pickle', 'wb') as handle:
        pickle.dump(data, handle)
    return data


# Update new unposted posts for each/a tag
def update_tags(data, full_update=False, tag_to_update=None):
    tag_amount = len(data['tags'])
    this_tag = 0
    if not tag_to_update:
        printProgressBar(this_tag, tag_amount, prefix = 'Updating danbooru tags:', suffix = 'Complete', length = 50)
    for tag, details in data['tags'].items():
        this_tag += 1
        if not tag_to_update:
            printProgressBar(this_tag, tag_amount, prefix = 'Updating danbooru tags:', suffix = 'Complete - '+tag+'                        ', length = 50)
        if not tag_to_update or tag_to_update == tag:
            if details['community'] not in config['SuggestPostsFor'] or len(details['unposted']) > 400:
                continue

            to_replace = []
            for post_id in details['posted']:
                if post_id not in to_replace:
                    to_replace.append(post_id)
            data['tags'][tag]['posted'] = to_replace
            to_replace = []
            for post_id in details['rejected']:
                if post_id not in to_replace:
                    to_replace.append(post_id)
            data['tags'][tag]['rejected'] = to_replace

            added = 0
            processed = 0
            update_complete = False
            amount = min(danbooru.count_posts('-rating:explicit, score:>10, '+tag)['counts']['posts'], 100000)
            amount_known = len(details['rejected'])+len(details['posted'])+len(details['unposted'])
            page = math.ceil(amount / 100) - math.floor(amount_known / 100)
            if amount_known < amount:
                while (True):
                    try:
                        if full_update:
                            posts = danbooru.post_list(limit=100, page=page, tags='-rating:explicit, score:>10, '+tag)
                        else:
                            posts = danbooru.post_list(limit=50, page=random.randint(1, math.ceil(amount / 50)), tags='-rating:explicit, score:>10, '+tag)
                    except Exception:
                        page -= 1
                        continue
                    page -= 1
                    for post in posts:
                        processed += 1
                        if str(post['id']) in details['rejected'] or str(post['id']) in details['posted'] or str(post['id']) in details['unposted']:
                            if amount_known+added >= amount:
                                update_complete = True
                                break
                            continue
                        else:
                            if 'animated' in post['tag_string_meta'].split():
                                data['tags'][tag]['rejected'].append(str(post['id']))
                            else:
                                data['tags'][tag]['unposted'][str(post['id'])] = post['tag_string_general'].split()
                            added += 1

                    if full_update and page % 20:
                        with open(os.path.curdir+'/data.pickle', 'wb') as handle:
                            pickle.dump(data, handle)

                    if page <= 0 or update_complete or (not full_update and added >= 25) or (not full_update and processed >= 50):
                        with open(os.path.curdir+'/data.pickle', 'wb') as handle:
                            pickle.dump(data, handle)
                        break

            # Move any posted posts to posted
            to_mark_posted = []
            for post_id, tags in data['tags'][tag]['unposted'].items():
                if post_id in data['posted']['danbooru'] or post_id in data['tags'][tag]['posted']:
                    print('marked post '+post_id+' as posted for '+tag+'                                                               ')
                    to_mark_posted.append(post_id)
            for post_id in to_mark_posted:
                data['tags'][tag]['posted'].append(post_id)
                del data['tags'][tag]['unposted'][post_id]

            to_mark_rejected = []
            # Move any rejected posts to rejected
            for post_id, tags in data['tags'][tag]['unposted'].items():
                if post_id in data['tags'][tag]['rejected']:
                    print('marked post '+post_id+' as rejected for '+tag+'                                                               ')
                    to_mark_rejected.append(post_id)
            # Move any animated content to rejected
            for post_id, tags in data['tags'][tag]['unposted'].items():
                if 'animated' in tags:
                    print('removed post '+post_id+' for '+tag+' because it is an animation                                             ')
                    to_mark_rejected.append(post_id)

            for post_id in to_mark_rejected:
                data['tags'][tag]['rejected'].append(post_id)
                del data['tags'][tag]['unposted'][post_id]

    with open(os.path.curdir+'/data.pickle', 'wb') as handle:
        pickle.dump(data, handle)
    return data


# Return community with fewest posts queued
def select_community():
    files = listdir(os.path.curdir+'/saved')
    breakdown = {}
    for community in config['SuggestPostsFor']:
        breakdown[community] = 0

    for post in files:
        data = json.load(open(os.path.curdir+'/saved/'+post, 'r'))
        for community in data['postCommunities'].keys():
            if community not in breakdown:
                continue
            else:
                breakdown[community] += 1
    sorted_breakdown = sorted(breakdown.items(), key=lambda x: x[1])
    if sorted_breakdown[0][1] >= 30:
        return False
    return sorted_breakdown[0][0]


# Return postData with danbooru details added
def get_danbooru_details(postData):
    if 'danbooruID' not in postData and postData['providedInput']:
        postData['danbooruID'] = re.search(r'\d+', postData['providedInput']).group(0)
    if 'danbooruID' in postData:
        postData['danbooruURL'] = 'https://danbooru.donmai.us/posts/'+postData['danbooruID']
        postData['danbooruData'] = danbooru.post_show(postData['danbooruID'])
        if postData['danbooruData']['is_banned'] or 'animated' in postData['danbooruData']['tag_string'].split():
            delete_post(postData)
            postData['danbooruFail'] = True
            print('invalid danbooru post, cannot be used to create a post')
            return postData
        postData['danbooruFile'] = download_image(postData['danbooruData']['file_url'])
        postData['danbooruFileURL'] = postData['danbooruData']['file_url']
        postData['danbooruTags'] = postData['danbooruData']['tag_string'].split()
        postData['danbooruRating'] = postData['danbooruData']['rating']
        if 'imageFile' not in postData:
            postData['imageFile'] = postData['danbooruFile']
    return postData


# Return postData with pixiv details added
def get_pixiv_details(postData, tmp_path='/lemmytrixposter'):
    # pixiv
    config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
    pixiv = AppPixivAPI()
    pixiv.auth(refresh_token=config['Pixiv']['token'])

    if 'pixivID' not in postData and 'providedInput' in postData:
        potential_id = re.search('\d{8,9}_{0,1}p{0,1}\d{0,2}', postData['providedInput']).group(0)
        if potential_id:
            postData['pixivID'] = potential_id
    if 'pixivID' in postData:
        postData['pixivData'] = pixiv.illust_detail(postData['pixivID'].split('_')[0]).illust
        if postData['pixivData'] and 'error' not in postData['pixivData'] and 'visible' in postData['pixivData'] and postData['pixivData'].visible:
            postData['pixivURL'] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id='+str(postData['pixivID'].split('_')[0])
            if postData['pixivData'].type != 'ugoira':
                print('Downloading image from pixiv...')
                if postData['pixivData'].meta_single_page:
                    downloadURL = postData['pixivData'].meta_single_page.original_image_url
                else:
                    postData['pixivDefault'] = False
                    if '_p' not in postData['pixivID']:
                        postData['pixivID'] += '_p0'
                        postData['pixivDefault'] = True
                    downloadURL = postData['pixivData'].meta_pages[int(postData['pixivID'].split('_p')[1])].image_urls.original
                pixiv.download(downloadURL, path=os.path.curdir+'/tmp'+tmp_path)
                postData['pixivFile'] = os.path.curdir+'/tmp'+tmp_path+'/'+os.path.basename(downloadURL)
                if 'imageFile' not in postData:
                    postData['imageFile'] = postData['pixivFile']
        else:
            if postData['pixivData'] and 'user' in postData['pixivData']:
                postData['pixivURL'] = 'https://www.pixiv.net/en/users/'+str(postData['pixivData'].user.id)
            del postData['pixivData']
    return postData


# Select a "random" post from database
async def pick_random(room):
    global data
    least_posts = select_community()
    postData = {}
    postData['randomInfoMessages'] = []

    if least_posts and random.randint(1, 3) != 3:
        print('attempting to activity balance for: '+least_posts)
        tags = {}
        known_posts = {}
        for tag, details in data['tags'].items():
            if details['community'] == least_posts and len(details['unposted']) > 0:
                tags[tag] = details

        # Get posts if there aren't any
        for tag in tags:
            if len(data['tags'][tag]['unposted']) == 0:
                print(str(len(data['tags'][tag]['unposted']))+' posts remaining, updating tag: '+tag)
                data = update_tags(data, tag_to_update=tag)

        for artist, details in data['artists'].items():
            if 'danbooru' in details:
                for post, post_tags in details['danbooru']['unposted'].items():
                    for tag in tags:
                        if tag in post_tags:
                            known_posts[post] = post_tags
        postData['randomInfoMessages'].append(str(len(known_posts))+' artist/tag matches for '+str(list(tags.keys())))

        if known_posts and random.randint(1, 2) != 2:
            danbooruID = random.choice(list(known_posts.keys()))
            print('using a random post by known artist')
        elif tags:
            posts = tags[random.choice(list(tags.keys()))]['unposted']
            danbooruID = random.choice(list(posts.keys()))
            print('using a random post with related tag')
        if 'danbooruID' in locals():
            postData['providedInput'] = 'https://danbooru.donmai.us/posts/'+str(danbooruID)
            postData['danbooruID'] = str(danbooruID)
            postData = get_danbooru_details(postData)
        postData['randomInfoMessages'].append('activity balancing for '+least_posts)

        # Update tags that are low on potential posts
        for tag in tags:
            if len(data['tags'][tag]['unposted']) < 200:
                print(str(len(data['tags'][tag]['unposted']))+' posts remaining, updating tag: '+tag)
                data = update_tags(data, tag_to_update=tag)
    else:
        print('finding a completely random post')
        post_types = []
        randomFiles = glob.glob(config['RandomSourcePath']+'/**/*.*', recursive=True)

        if randomFiles:
            post_types.append('local folder')
        for artist, details in data['artists'].items():
            if 'danbooru' in details and len(details['danbooru']['unposted']) > 0:
                post_types.append('danbooru')
                break
        for artist, details in data['artists'].items():
            if 'pixiv' in details and len(details['pixiv']['unposted']) > 0:
                post_types.append('pixiv')
                break

        if post_types:
            while True:
                post_type = random.choice(post_types)
                print('post type: '+post_type)
                if post_type != 'local folder':
                    potential_artists = {}
                    for artist, details in data['artists'].items():
                        if post_type in details and len(details[post_type]['unposted']) > 0:
                            potential_artists[artist] = details[post_type]['unposted']
                    postID = random.choice(list(potential_artists[random.choice(list(potential_artists.keys()))]))

                if post_type == 'danbooru':
                    postData['providedInput'] = 'https://danbooru.donmai.us/posts/'+str(postID)
                    postData['danbooruID'] = str(postID)
                    postData = get_danbooru_details(postData)
                    if 'danbooruFail' in postData:
                        del postData['danbooruFail']
                        del postData['danbooruID']
                        del postData['danbooruData']
                        continue

                if post_type == 'pixiv':
                    postData['providedInput'] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id='+postID
                    postData['pixivID'] = postID
                    postData = get_pixiv_details(postData)

                if post_type == 'local folder':
                    postData['providedInput'] = random.choice(randomFiles)
                    postData['imageFile'] = postData['providedInput']

                postData['randomInfoMessages'].append('suggested post from '+post_type)
                artist_key = get_artist_key(postData)
                # Update artist if they are low on potential posts
                if artist_key:
                    if 'danbooru' in data['artists'][artist]:
                        if len(data['artists'][artist]['danbooru']['unposted']) < 20:
                            print('updating artist danbooru: '+artist_key)
                            data = update_danbooru(data, artist_to_update=artist)
                    if 'pixiv' in data['artists'][artist]:
                        if len(data['artists'][artist]['pixiv']['unposted']) < 20:
                            print('updating artist pixiv: '+artist_key)
                            data = update_pixiv(data, artist_to_update=artist)
                break

    if 'imageFile' in postData:
        size = 1000, 1000
        with Image.open(postData['imageFile']) as image:
            if image.mode == "RGBA":
                no_alpha = Image.new("RGB", image.size, (255, 255, 255))
                no_alpha.paste(image, mask=image.split()[3]) # 3 is the alpha channel
                no_alpha.thumbnail(size)
                no_alpha.save(os.path.curdir+'/tmp/lemmytrixposter/rand_thumb.jpg', 'JPEG')
            else:
                no_alpha = image.convert('RGB')
                no_alpha.thumbnail(size)
                no_alpha.save(os.path.curdir+'/tmp/lemmytrixposter/rand_thumb.jpg', 'JPEG')
        postData['randomThumb'] = os.path.curdir+'/tmp/lemmytrixposter/rand_thumb.jpg'
        message = ''
        for line in postData['randomInfoMessages']:
            message += line+'\n'
        await matrix.api.send_text_message(room.room_id, message, msgtype="m.notice")
        await matrix.api.send_image_message(room.room_id,image_filepath=postData['randomThumb'])
        if os.path.isfile(postData['providedInput']):
            await matrix.api.send_markdown_message(room.room_id, '**[Select/Next/Move/Delete]**')
        else:
            await matrix.api.send_markdown_message(room.room_id, '**[Select/Next/Reject]**')
        return postData

    print(postData)
    await matrix.api.send_markdown_message(room.room_id, '**ERROR**')
    return False  # Return false if no random post options available


# Status command
def get_status():
    files = listdir(os.path.curdir+'/saved')
    amount = str(len(files))
    artists = str(len(artists_config))
    breakdown = {}
    for post in files:
        postData = json.load(open(os.path.curdir+'/saved/'+post, 'r'))
        for community in postData['postCommunities'].keys():
            if community not in breakdown:
                breakdown[community] = 1
            else:
                breakdown[community] += 1
    unposted = 0
    for artist, details in data['artists'].items():
        if 'pixiv' in details:
            unposted += len(details['pixiv']['unposted'])
        if 'danbooru' in details:
            unposted += len(details['danbooru']['unposted'])
    message = 'There are '+artists+' saved artists, with '+str(unposted)+' saved posts'
    message += '\nThere are '+amount+' saved posts'
    for entry, amount in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
        message += '\n'+str(amount)+' for '+entry
    return message


def edit_communities(communities):
    new_communities = {}
    config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
    for community in communities:
        if '@' in community:
            new_communities[community] = 'default'
        else:
            for confcom in config['Communities']:
                if community in confcom:
                    new_communities[confcom] = 'default'
    return new_communities


# Parse links into a markdown string
def edit_links(links):
    new_links = ''
    for link in links.split():
        new_links += ' | '
        if 'danbooru' in link:
            new_links += '[danbooru]'
        elif 'x.com' in link:
            new_links += '[twitter]'
        else:
            new_links += '['+urlparse(link).netloc.split('.')[-2]+']'
        new_links += '('+link+')'
    return new_links


# Check that the post has communities to post to
def check_communities(postData):
    if len(postData['postCommunities']) > 0:
        return True
    return False


# Download image from URL and return filepath
def download_image(url):
    with open(os.path.curdir+'/tmp/lemmytrixposter/'+os.path.basename(url), 'wb') as handler:
        response = requests.get(url, headers=headers)
        if not response.ok:
            return None
        handler.write(response.content)
        return os.path.curdir+'/tmp/lemmytrixposter/'+os.path.basename(url)


# Upload image to image host and add file link/s to postdata
def upload_image(postData):
    if 'postURL' in postData:
        return postData
    response = requests.get('https://catbox.moe', headers=headers)
    if not response.ok:
        return postData
    # For big files, create a wepb for post
    final_size = 1800, 1800
    if os.path.getsize(postData['imageFile']) > 1048576:
        print('Creating high quality thumbnail for post...')
        with Image.open(postData['imageFile']) as image:
            image.thumbnail(final_size)
            image.save(os.path.curdir+'/tmp/lemmytrixposter/final_thumb.webp', 'WEBP')
        postData['largeFile'] = postData['imageFile']
        postData['imageFile'] = os.path.curdir+'/tmp/lemmytrixposter/final_thumb.webp'
        largeWidth, largeHeight = Image.open(postData['largeFile']).size

    # Host image on catbox
    print('Uploading image to catbox...')
    postData['postURL'] = format(CatboxUploader(postData['imageFile']).execute())

    # Handle failed upload
    response = requests.get(postData['postURL'], headers=headers)
    if not response.ok:
        del postData['postURL']
        return postData

    print('Image uploaded: ' + postData['postURL'])

    if 'largeFile' in postData:
        if 'danbooruFile' not in postData or os.path.getsize(postData['largeFile']) > os.path.getsize(postData['danbooruFile']):
            print('Uploading large image to catbox...')
            largeImageURL = format(CatboxUploader(postData['largeFile']).execute())
            print('Image uploaded: ' + largeImageURL)
            postData['postBody'] += '\n\nFull quality: ['+os.path.splitext(largeImageURL)[1]+' '+size(os.path.getsize(postData['largeFile']), system=alternative)+']('+largeImageURL+') ('+str(largeWidth)+' × '+str(largeHeight)+')'
        else:
            postData['postBody'] += '\n\nFull quality: ['+os.path.splitext(postData['danbooruFileURL'])[1]+' '+size(os.path.getsize(postData['danbooruFile']), system=alternative)+']('+postData['danbooruFileURL']+') ('+str(largeWidth)+' × '+str(largeHeight)+')'

    # Save max quality file to /posted
    if config['SavePosted']:
        if 'largeFile' in postData and 'posted' not in postData['largeFile']:
            shutil.copy(postData['largeFile'], os.path.curdir+'/posted')
        elif 'posted' not in postData['imageFile']:
            shutil.copy(postData['imageFile'], os.path.curdir+'/posted')
    # Clear temporary files
    for f in listdir(os.path.curdir+'/tmp/lemmytrixposter'):
        os.remove(os.path.curdir+'/tmp/lemmytrixposter/'+f)
    # Delete source file used to create post
    if config['DeleteOncePosted'] and os.path.isfile(postData['providedInput']):
        os.remove(postData['providedInput'])
    return postData


def postdata_from_input(providedInput=None, tmp_path='/lemmytrixposter'):
    if type(providedInput) != str:
        postData = providedInput
        if 'providedInput' not in postData:
            return None
    else:
        postData = {'providedInput': providedInput.split('?')[0]}

    # pixiv
    config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
    pixiv = AppPixivAPI()
    pixiv.auth(refresh_token=config['Pixiv']['token'])

    if os.path.isfile(postData['providedInput']):
        postData['imageFile'] = postData['providedInput']
    else:
        # Detect pixiv link or file
        if 'fanbox' not in postData['providedInput']:
            if 'pixiv.net' in postData['providedInput'] or 'pximg.net' in postData['providedInput']:
                if 'pixivID' not in postData and 'pixivData' not in postData:
                    postData = get_pixiv_details(postData)
                print('Pixiv ID detected: ' + postData['pixivID'])

        # Detect danbooru link
        if 'danbooru.donmai.us/posts/' in postData['providedInput'] or 'danbooru.donmai.us/post/show/' in postData['providedInput']:
            print('Downloading image from danbooru...')
            if 'danbooruData' not in postData:
                postData = get_danbooru_details(postData)

        # Detect/download image from URL
        if 'imageFile' not in postData and re.search('https:\/\/.*\/.*\.\w{3,4}', postData['providedInput']):
            print('Downloading image...')
            postData['imageFile'] = download_image(postData['providedInput'])

    if 'imageFile' not in postData:
        return 'Unable to find an image file using input'

    # Create thumbnail for use with saucenao and messaging
    print('Creating thumbnail...')
    if 'randomThumb' in postData:
        postData['imageThumb'] = postData['randomThumb']
    else:
        size = 1000, 1000
        with Image.open(postData['imageFile']) as image:
            if image.mode == "RGBA":
                no_alpha = Image.new("RGB", image.size, (255, 255, 255))
                no_alpha.paste(image, mask=image.split()[3]) # 3 is the alpha channel
                no_alpha.thumbnail(size)
                no_alpha.save(os.path.curdir+'/tmp/lemmytrixposter/sauce_thumb.jpg', 'JPEG')
            else:
                no_alpha = image.convert('RGB')
                no_alpha.thumbnail(size)
                no_alpha.save(os.path.curdir+'/tmp/lemmytrixposter/sauce_thumb.jpg', 'JPEG')
        postData['imageThumb'] = os.path.curdir+'/tmp/lemmytrixposter/sauce_thumb.jpg'

    # Grab info from saucenao
    print('Getting sources from saucenao...')
    saucenao_check = requests.get('https://saucenao.com', headers=headers)
    if not saucenao_check.ok:
        return 'SauceNao is unavailable, wait a moment'
    try:
        results = sauce.from_file(postData['imageThumb'])
    except Exception:
        return 'SauceNao unavailable, ratelimit probably exceeded'
    postData['rateLimit'] = str(results.long_remaining)

    for result in results:
        if result.similarity > 65 and result.author != 'Unknown':
            if 'postTitle' not in postData or postData['postTitle'] == '':
                print('Using saucenao title: '+result.title)
                postData['postTitle'] = result.title
            if 'artist' not in postData or postData['artist'] == '':
                if type(result.author) is str:
                    print('Using saucenao name: '+result.author)
                    postData['artist'] = result.author
            for url in result.urls:
                print('Source found: '+url)
                if 'fanbox' not in url and 'pixivURL' not in postData and 'pixivID' not in postData:
                    if 'pixiv.net' in url or 'pximg.net' in url:
                        potential_id = re.search('\d{8,9}_{0,1}p{0,1}\d{0,2}', url).group(0)
                        if potential_id:
                            postData['pixivID'] = potential_id
                if 'twitter' in url and 'twitterURL' not in postData:
                    postData['twitterURL'] = url
                if 'artstation' in url and 'artstationURL' not in postData:
                    postData['artstationURL'] = url
                if 'danbooru' in url and 'danbooruURL' not in postData:
                    postData['danbooruURL'] = url
                    postData['danbooruID'] = url.split('/')[-1].split('?q=')[0]
                if 'deviantart' in url and 'deviantURL' not in postData:
                    postData['deviantURL'] = url
            try:
                print('Source found: '+result.raw['data']['source'])
                if 'fanbox' not in result.raw['data']['source'] and 'pixivURL' not in postData and 'pixivID' not in postData:
                    if 'pixiv.net' in result.raw['data']['source'] or 'pximg.net' in result.raw['data']['source']:
                        potential_id = re.search('\d{8,9}_{0,1}p{0,1}\d{0,2}', result.raw['data']['source']).group(0)
                        if potential_id:
                            postData['pixivID'] = potential_id
                if 'twitter' in result.raw['data']['source'] and 'twitterURL' not in postData:
                    postData['twitterURL'] =  result.raw['data']['source']
                if 'artstation' in  result.raw['data']['source'] and 'artstationURL' not in postData:
                    postData['artstationURL'] =  result.raw['data']['source']
                if 'deviantart' in  result.raw['data']['source'] and 'deviantURL' not in postData:
                    postData['deviantURL'] =  result.raw['data']['source']
            except Exception:
                pass

    if 'danbooruData' not in postData and 'danbooruID' in postData:
        postData = get_danbooru_details(postData)

    if 'pixivData' not in postData and 'pixivID' in postData:
        postData = get_pixiv_details(postData)

    # See if pixivfile is bigger than current imageFile
    if 'pixivFile' in postData and os.path.getsize(postData['pixivFile']) > os.path.getsize(postData['imageFile']):
        if 'pixivDefault' not in postData or ('pixivDefault' in postData and not postData['pixivDefault']):
            print('switching to image file from pixiv')
            postData['imageFile'] = postData['pixivFile']
    # See if danbooruFile is bigger than current imageFile
    if 'danbooruFile' in postData and os.path.getsize(postData['danbooruFile']) > os.path.getsize(postData['imageFile']):
        print('switching to image file from danbooru')
        postData['imageFile'] = postData['danbooruFile']

    # Translate title
    if 'pixivData' in postData:
        print('Using pixiv title')
        postData['postTitle'] = postData['pixivData'].title
    try:
        lang = detect(postData['postTitle'])
    except Exception:
        lang = None
    if 'postTitle' in postData and postData['postTitle'] != '':
        if lang == 'ja' or lang == 'zh':
            translation = GoogleTranslator(source='auto', target='en').translate(postData['postTitle'])
            if type(translation) == str:
                print('Translated title: '+translation)
                postData['postTitle'] = translation.title()
    if 'postTitle' not in postData:
        postData['postTitle'] = ''
    else:
        postData['postTitle'] = postData['postTitle'].title()

    # Set best possible artist name
    if 'danbooruData' in postData:
        print('Using danbooru name')
        postData['artist'] = postData['danbooruData']['tag_string_artist'].replace('_', ' ').split(' (')[0].title()
    elif 'artist' not in postData and 'pixivData' in postData and 'pixivData' in postData and postData['pixivData'].visible:
        print('Using pixiv name')
        postData['artist'] = postData['pixivData'].user.name.split('@')[0]
    if 'artist' not in postData or postData['artist'] == '':
        postData['artist'] = 'Unknown'
    elif postData['artist'][0].islower():
        postData['artist'] = postData['artist'].title()

    # Create post body string
    postData = add_missing_socials(postData)
    postData['postBody'] = 'Artist: **'+postData['artist']+'**'
    if 'fediverseURL' in postData:
        postData['postBody'] += ' | [fediverse]('+postData['fediverseURL']+')'
    if 'pixivURL' in postData:
        postData['postBody'] += ' | [pixiv]('+postData['pixivURL']+')'
    if 'twitterURL' in postData:
        postData['postBody'] += ' | [twitter]('+postData['twitterURL']+')'
    if 'newgroundsURL' in postData:
        postData['postBody'] += ' | [newgrounds]('+postData['newgroundsURL']+')'
    if 'artstationURL' in postData:
        postData['postBody'] += ' | [artstation]('+postData['artstationURL']+')'
    if 'tumblrURL' in postData:
        postData['postBody'] += ' | [tumblr]('+postData['tumblrURL']+')'
    if 'deviantURL' in postData:
        postData['postBody'] += ' | [deviantart]('+postData['deviantURL']+')'
    if 'linktreeURL' in postData:
        postData['postBody'] += ' | [linktree]('+postData['linktreeURL']+')'
    if 'kofiURL' in postData:
        postData['postBody'] += ' | [ko-fi]('+postData['kofiURL']+')'
    if 'patreonURL' in postData:
        postData['postBody'] += ' | [patreon]('+postData['patreonURL']+')'
    if 'danbooruURL' in postData:
        postData['postBody'] += ' | [danbooru]('+postData['danbooruURL']+')'

    # Set NSFW rating based on danbooru rating if possible
    postData['postNSFW'] = False
    try:
        if postData['danbooruRating'] == 'e' or postData['danbooruRating'] == 'q':
            postData['postNSFW'] = True
    except Exception:
         pass

    # Determine communities to post to
    postData['postCommunities'] = {}
    if config['AutoDetectCommunities'] and 'danbooruTags' in postData:
        for community in config['Communities']:
            for tag in config['Communities'][community]:
                if tag in postData['danbooruTags'] and community not in postData['postCommunities']:
                    postData['postCommunities'][community] = 'default'

    return postData


def compose_preview(postData):
    if type(postData['postTitle']) is str and postData['postTitle'] != '':
        preview = '**Title:** ' + postData['postTitle'] + ' (by '+postData['artist']+')'
    else:
        preview = '**Title:** (by '+postData['artist']+')'
    preview += '\n**Body:** ' + postData['postBody']
    if postData['postNSFW']:
        preview += '\n**NSFW:** Yes'
    else:
        preview += '\n**NSFW:** No'
    preview += '\n**Communities:** ' + ' '.join(postData['postCommunities'].keys())
    if get_artist_key(postData):
        preview += '\n_artist is known_'
    if check_if_repost(postData):
        preview += '\n**_this has already been posted_**'
    preview += '\nEdit? **[T/Tt/A/Ta/L/R/C/Post/Save/Cancel]**'
    return preview


def create_posts(postData, force = False):
    postData = upload_image(postData)
    if 'postURL' not in postData:
        return postData
    if not force and check_if_repost(postData):
        return 'repost'

    if postData['postTitle'] == '':
        postData['postTitle'] = '(by ' + postData['artist'] + ')'
    else:
        postData['postTitle'] += ' (by ' + postData['artist'] + ')'
    if 'deviantart' in postData['postBody']:
        postData['postBody'] = re.sub(' \| \[deviantart[^\)]*\)', '', postData['postBody'])

    print('Creating post/s...')
    message = 'Created post/s...'
    for community, account in postData['postCommunities'].items():
        communityID = lemmy.discover_community(community)
        post = lemmy.post.create(communityID, postData['postTitle'], url=postData['postURL'], body=postData['postBody'], nsfw=postData['postNSFW'])
        if post:
            print(f"Successfully posted ({post['post_view']['post']['ap_id']})")
            message += '\n'+post['post_view']['post']['ap_id']
        else:
            print('Failed to post to ' + community)
            message += '\nFailed to post to ' + community
    mark_as_posted(postData)
    postData['message'] = message
    return postData


def save_posts(postData, force = False):
    postData = upload_image(postData)
    if 'postURL' not in postData:
        return postData
    if not force and check_if_repost(postData):
        return 'repost'

    if postData['postTitle'] == '':
        postData['postTitle'] = '(by ' + postData['artist'] + ')'
    else:
        postData['postTitle'] += ' (by ' + postData['artist'] + ')'

    if not os.path.exists(os.path.curdir+'/saved'):
        os.mkdir(os.path.curdir+'/saved')
    while True:
        fileName = os.path.curdir+'/saved/' + str(random.randint(100000, 999999))+'post.json'
        if not os.path.exists(fileName):
            break
    with open(fileName, 'w') as postDict:
        json.dump(postData, postDict)
    print('Post saved for later')
    mark_as_posted(postData)
    return postData


last_posted = []
last_files = []


def post_random_saved(post_to=None):
    global last_posted
    global last_files
    fileList = listdir(os.path.curdir+"/saved")
    fileList.sort(key=lambda f: os.path.getmtime(os.path.curdir+"/saved/"+f))
    message = ''
    links = []
    posted = []
    failed = []
    if len(fileList) == 0:
        return "there are no saved posts"

    response = requests.get('https://catbox.moe', headers=headers)
    if not response.ok:
        return "catbox is down at the moment"

    while (len(last_posted) > 6):
        last_posted.pop(0)
    while (len(last_files) > 6):
        last_files.pop(0)

    # Find suitable post if posting to defined community
    if post_to:
        potentialFileList = []
        for confcom in config['Communities']:
            if post_to in confcom:
                post_to = confcom
                break
        for f in fileList:
            thisFile = os.path.curdir+"/saved/"+f
            with open(thisFile, "r") as pf:
                thisPost = json.load(pf)
            if post_to in thisPost["postCommunities"]:
                potentialFileList.append(thisFile)
        if potentialFileList:
            postFile = random.choice(potentialFileList)
            for filepath in potentialFileList:
                if random.randint(1, 20) == 1:
                    postFile = filepath
                    break
            with open(postFile, "r") as pf:
                postData = json.load(pf)
        else:
            message = 'There are no saved posts for !'+post_to

    # Load some posts and rank them by how recently the target communities have been posted to
    else:
        potentialPosts = {}
        loop = 0
        while (loop < 7 and loop < len(fileList)):
            loop += 1
            # This only loops until a file without at borked URL is found
            for f in fileList:
                # Loop through files in order of age, randomply picking one in order to bias selection towards older saved posts
                for f in fileList:
                    if random.randint(1, 20) == 1:
                        postFile = os.path.curdir+"/saved/"+f
                        break
                # Select a random file if iterated through all posts with none selected
                if 'postFile' not in locals():
                    postFile = os.path.curdir+"/saved/"+random.choice(fileList)

                with open(postFile, "r") as pf:
                    postData = json.load(pf)
                try:
                    response = requests.get(postData['postURL'], headers=headers)
                    if not response.ok:
                        print('Post with invalid catbox link found')
                        shutil.copy(postFile, os.path.curdir+"/error")
                        os.remove(postFile)
                except Exception:
                    print('Post with invalid catbox link found')
                    shutil.copy(postFile, os.path.curdir+"/error")
                    os.remove(postFile)
                if postFile not in last_files and postFile not in potentialPosts:
                    break

            # Create dict with potential posts and how recently their communities have been posted to
            if config['Timer']['cross_post_all_at_once']:
                for community, account in postData["postCommunities"].items():
                    if community in last_posted:
                        if postFile in potentialPosts and potentialPosts[postFile] > last_posted.index(community):
                            continue
                        else:
                            potentialPosts[postFile] = last_posted.index(community)
                    else:
                        potentialPosts[postFile] = -1
            elif list(postData["postCommunities"])[0] in last_posted:
                potentialPosts[postFile] = last_posted.index(list(postData["postCommunities"])[0])
            else:
                potentialPosts[postFile] = -1

        # Load post for the least recently posted to community
        postFile = sorted(potentialPosts.items(), key=lambda x: x[1])[0][0]
        with open(postFile, "r") as pf:
            postData = json.load(pf)

    if 'postData' in locals():
        if 'deviantart' in postData['postBody']:
            postData['postBody'] = re.sub(' \| \[deviantart[^\)]*\)', '', postData['postBody'])
        # Create post/posts
        print("Connecting to lemmy...")
        lemmy = Lemmy('https://'+config['Lemmy']['instance'],request_timeout=30)
        lemmy.log_in(config['Lemmy']['username'], config['Lemmy']['password'])
        print("Creating post/s...")
        for community, account in postData["postCommunities"].items():
            if post_to:
                community = post_to
            if community not in last_posted:
                last_posted.append(community)
            communityID = lemmy.discover_community(community)
            post = lemmy.post.create(communityID, postData["postTitle"], url=postData["postURL"], body=postData["postBody"], nsfw=postData["postNSFW"])
            if post:
                print(f"Successfully posted ({post['post_view']['post']['ap_id']})")
                links.append('Posted to [!'+community+']('+post['post_view']['post']['ap_id']+')')
                posted.append(community)
            else:
                print("Failed to post to " + community + " ("+postFile+")")
                failed.append(community)
            if not config['Timer']['cross_post_all_at_once'] or post_to:
                break

        # Update postfile by removing any communities that were successfully posted, and deleting it if none are left
        for community in posted:
            del postData["postCommunities"][community]
        if len(postData["postCommunities"]) != 0:
            with open(postFile, 'w') as postDict:
                json.dump(postData, postDict)
            last_files.append(postFile)
        else:
            os.remove(postFile)

    # Return report message string
    for link in links:
        message += link+'  \n'
    files = str(len(fileList))
    for fail in failed:
        message += 'Post to !'+community+' failed  \n'
    message += 'There are '+files+' saved posts left.'
    eventData = {}
    eventData['message'] = message
    eventData['links'] = links
    eventData['remaining'] = files
    eventData['failed'] = failed
    return eventData


def timer_post_thread():
    if config['Timer']['enabled'] is False:
        return
    message = 'trickleposting is enabled...'
    while (True):
        sleeptime = random.randint(config['Timer']['min_wait'], config['Timer']['max_wait'])
        message += '  \nnext post in '+str(sleeptime)+' minutes'
        try:
            if mc_path != '':
                subprocess.run(['matrix-commander', '-n', '-z', '-m', message, '-s', mc_path+'/store/', '-c', mc_path+'/creds.json'])
            else:
                subprocess.run(['matrix-commander', '-n', '-z', '-m', message])
        except Exception:
            print('ERROR matrix-commander unavailable')
            pass

        time.sleep(sleeptime*60)
        savedPosts = len(listdir(os.path.curdir+"/saved"))
        try:
            message = "I tried posting something!"
            for post in range(random.randint(1, min(savedPosts, config['Timer']['rand_burst']))):
                eventData = post_random_saved()
                for link in eventData['links']:
                    message += "  \n"+link
                for fail in eventData['failed']:
                    message += "  \n"+'Post to !'+fail+' failed'
                time.sleep(20)
            message += '  \nThere are '+eventData['remaining']+' saved posts left.'
        except Exception:
            message = "timer posting ran but there were errors"
        if "no saved posts" in message:
            message = "tried to post something, but there were no saved posts"


def full_update_danbooru():
    global data
    data = update_danbooru(data)
    data = update_tags(data)

def full_update_pixiv():
    global data
    data = update_pixiv(data)

data = load_and_update_datatable()

print('Spinning off autoposting thread')
timerposter = threading.Thread(target=timer_post_thread)
timerposter.daemon = True

if __name__ == '__main__':
    # Lemmy
    print('Logging into lemmy instance...')
    lemmy = Lemmy('https://'+config['Lemmy']['instance'], request_timeout=30)
    lemmy.log_in(config['Lemmy']['username'], config['Lemmy']['password'])

    # matrix
    print('Connecting to matrix...')
    matrix = botlib.Bot( botlib.Creds("https://"+config['Matrix']['homeserver'], config['Matrix']['bot_user'], config['Matrix']['bot_password']))
    botconfig = botlib.Config()
    botconfig.allowlist = [config['Matrix']['user_whitelist']]
    # This is the room ID of the only room in which the bot is allowed to function
    allowedRoom = config['Matrix']['room']

    # globals
    botState = 'ready'
    postData = {}
    randomFile = ''

    @matrix.listener.on_startup
    async def room_joined(room_id):
        await matrix.api.send_text_message(room_id, 'lemmytrixposter has started and is ready', msgtype="m.notice")

    @matrix.listener.on_custom_event(nio.RoomEncryptedImage)
    async def image_receive(room, message):
        global botState
        global postData
        match = botlib.MessageMatch(room, message, matrix)

        if match.is_not_from_this_bot() and room.room_id == allowedRoom:
            if botState == 'ready':
                await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                for f in listdir(os.path.curdir+'/tmp/lemmytrixposter'):
                    os.remove(os.path.curdir+'/tmp/lemmytrixposter/'+f)
                try:
                    if mc_path != '':
                        subprocess.run(['matrix-commander', '--download-media', os.path.curdir+'/tmp/lemmytrixposter/', '--tail', '2', '-s', mc_path+'/store', '-c', mc_path+'/creds.json'])
                    else:
                        subprocess.run(['matrix-commander', '--download-media', os.path.curdir+'/tmp/lemmytrixposter/', '--tail', '2'])
                    inputFile = os.path.curdir+'/tmp/lemmytrixposter/'+listdir(os.path.curdir+'/tmp/lemmytrixposter')[0]
                except Exception:
                    await matrix.api.send_text_message(room.room_id, 'unable to receive file', msgtype="m.notice")
                    return
                if 'inputFile' in locals():
                    postData = postdata_from_input(inputFile)
                    if postData:
                        await matrix.api.send_markdown_message(room.room_id, compose_preview(postData))
                        botState = 'editing'
                else:
                    await matrix.api.send_text_message(room.room_id, 'invalid input', msgtype="m.notice")

    @matrix.listener.on_message_event
    async def autoposter(room, message):
        global botState
        global postData
        global randomPostData
        match = botlib.MessageMatch(room, message, matrix)

        if match.is_not_from_this_bot() and room.room_id == allowedRoom:
            if match.command('stop') or match.command('Stop'):
                await matrix.api.send_text_message(room.room_id, 'Stopping...', msgtype="m.notice")
                sys.exit()

            if botState == 'ready':

                if match.command('add') or match.command('Add'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    await matrix.api.send_text_message(room.room_id, add_artist(message.body[2:]), msgtype="m.notice")

                elif match.command('update') or match.command('Update'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    if 'danbooru' in message.body[2:]:
                        full_update_danbooru()
                        await matrix.api.send_text_message(room.room_id, 'Danbooru update complete', msgtype="m.notice")
                    if 'pixiv' in message.body[2:]:
                        full_update_pixiv()
                        await matrix.api.send_text_message(room.room_id, 'Pixiv update complete', msgtype="m.notice")
                    if 'social' in message.body[2:]:
                        update_artist_socials()
                        await matrix.api.send_text_message(room.room_id, 'Socials update complete', msgtype="m.notice")

                elif match.command('delete') or match.command('Delete') or match.command('d') or match.command('D'):
                    if os.path.isfile(randomPostData['providedInput']):
                        os.remove(randomPostData['providedInput'])
                        await matrix.api.send_text_message(room.room_id, 'deleted '+randomPostData['providedInput'], msgtype="m.notice")
                    else:
                        await matrix.api.send_text_message(room.room_id, randomPostData['providedInput']+' already deleted or moved', msgtype="m.notice")
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    randomPostData = await pick_random(room)

                elif match.command('reject') or match.command('Reject')or match.command('r')or match.command('R'):
                    mark_as_rejected(randomPostData)
                    await matrix.api.send_text_message(room.room_id, 'post rejected, it will not be suggested again, working...', msgtype="m.notice")
                    randomPostData = await pick_random(room)

                elif match.command('move') or match.command('Move') or match.command('m') or match.command('M'):
                    if os.path.isfile(randomPostData['providedInput']):
                        shutil.copy(randomPostData['providedInput'], os.path.curdir+'/moved')
                        os.remove(randomPostData['providedInput'])
                        await matrix.api.send_text_message(room.room_id, 'moved '+randomPostData['providedInput'], msgtype="m.notice")
                    else:
                        await matrix.api.send_text_message(room.room_id, randomPostData['providedInput']+' already deleted or moved', msgtype="m.notice")
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    randomPostData = await pick_random(room)

                elif match.command('randompost') or match.command('Randompost'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    if len(message.body) > 10:
                        await matrix.api.send_markdown_message(room.room_id, post_random_saved(post_to=message.body[11:])['message'], msgtype="m.notice")
                    else:
                        await matrix.api.send_markdown_message(room.room_id, post_random_saved()['message'], msgtype="m.notice")

                elif match.command('n') or match.command('N') or match.command('next') or match.command('Next'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    randomPostData = await pick_random(room)

                elif match.command('select') or match.command('Select') or match.command('s') or match.command('S'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    postData = postdata_from_input(randomPostData)
                    if type(postData) == str:
                        await matrix.api.send_text_message(room.room_id, postData, msgtype="m.notice")
                    else:
                        await matrix.api.send_markdown_message(room.room_id, compose_preview(postData))
                        botState = 'editing'

                elif match.command('status') or match.command('Status'):
                    await matrix.api.send_text_message(room.room_id, get_status(), msgtype="m.notice")

                elif match.command('help') or match.command('Help'):
                    await matrix.api.send_text_message(room.room_id, help_message, msgtype="m.notice")

                else:
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    postData = postdata_from_input(message.body)
                    if type(postData) == str:
                        await matrix.api.send_text_message(room.room_id, postData, msgtype="m.notice")
                    else:
                        await matrix.api.send_image_message(room.room_id, image_filepath=postData['imageThumb'])
                        await matrix.api.send_markdown_message(room.room_id, compose_preview(postData))
                        botState = 'editing'

            elif botState == 'editing':
                if match.command('add') or match.command('Add'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    await matrix.api.send_text_message(room.room_id, add_artist(postData=postData), msgtype="m.notice")

                elif match.command('post') or match.command('Post'):
                    if check_communities(postData):
                        await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                        post = create_posts(postData)
                        if post == 'repost':
                            botState = 'checking'
                            await matrix.api.send_markdown_message(room.room_id, 'this is a repost, post anyway? **[Yes/No]**', msgtype="m.notice")
                            return
                        elif 'postURL' not in post:
                            await matrix.api.send_markdown_message(room.room_id, '**CATBOX UPLOAD ERROR**', msgtype="m.notice")
                            return
                        else:
                            await matrix.api.send_markdown_message(room.room_id, post['message']+'\n'+postData['rateLimit']+' dailysaucenao uses left', msgtype="m.notice")
                        botState = 'ready'
                    else:
                        await matrix.api.send_markdown_message(room.room_id, '**ERROR** post must have target communities before posting', msgtype="m.notice")
                    return

                elif match.command('save') or match.command('Save'):
                    if check_communities(postData):
                        await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                        post = save_posts(postData)
                        if post == 'repost':
                            botState = 'savechecking'
                            await matrix.api.send_markdown_message(room.room_id, 'this is a repost, save anyway? **[Yes/No]**', msgtype="m.notice")
                            return
                        elif 'postURL' not in post:
                            await matrix.api.send_markdown_message(room.room_id, '**CATBOX UPLOAD ERROR**', msgtype="m.notice")
                            return
                        files = str(len(listdir(os.path.curdir+'/saved')))
                        await matrix.api.send_text_message(room.room_id, 'post saved for later, '+files+' saved posts, '+postData['rateLimit']+' daily saucenao uses left', msgtype="m.notice")
                        botState = 'ready'
                    else:
                        await matrix.api.send_markdown_message(room.room_id, '**ERROR** post must have target communities before saving', msgtype="m.notice")
                    return

                elif match.command('cancel') or match.command('Cancel'):
                    botState = 'ready'
                    await matrix.api.send_text_message(room.room_id, 'cancelled, nothing was posted or saved, '+postData['rateLimit']+' daily saucenao uses left', msgtype="m.notice")
                    return

                elif match.command('t') or match.command('T'):
                    postData['postTitle'] = message.body[2:]
                    await matrix.api.send_markdown_message(room.room_id, '**Title:** '+postData['postTitle'])
                elif match.command('tt') or match.command('Tt'):
                    postData['postTitle'] = GoogleTranslator(source='auto', target='en').translate(postData['postTitle'])
                    await matrix.api.send_markdown_message(room.room_id, '**Translated Title:** '+postData['postTitle'])
                elif match.command('a') or match.command('A'):
                    postData['artist'] = message.body[2:]
                    postData['postBody'] = re.sub('\*\*.*\*\*',  '**'+postData['artist']+'**', postData['postBody'])
                    await matrix.api.send_markdown_message(room.room_id, '**Artist:** '+postData['artist'])
                elif match.command('ta') or match.command('Ta'):
                    postData['artist'] = GoogleTranslator(source='auto', target='en').translate(postData['artist'])
                    postData['postBody'] = re.sub('\*\*.*\*\*',  '**'+postData['artist']+'**', postData['postBody'])
                    await matrix.api.send_markdown_message(room.room_id, '**Translated Artist:** '+postData['artist'])
                elif match.command('l') or match.command('L'):
                    postData['postBody'] = postData['postBody'].split(' | ')[0]+edit_links(message.body[2:])
                    await matrix.api.send_markdown_message(room.room_id, '**Body:** '+postData['postBody'])
                elif match.command('r') or match.command('R'):
                    postData['postNSFW'] = not postData['postNSFW']
                    if postData['postNSFW']:
                        await matrix.api.send_markdown_message(room.room_id, '**NSFW:** Yes')
                    else:
                        await matrix.api.send_markdown_message(room.room_id, '**NSFW:** No')
                elif match.command('c') or match.command('C'):
                    postData['postCommunities'] = edit_communities(message.body[2:].split())
                    await matrix.api.send_markdown_message(room.room_id, '**Communities:** ' + ' '.join(postData['postCommunities'].keys()))

            elif botState == 'checking':
                if match.command('yes') or match.command('Yes'):
                    await matrix.api.send_text_message(room.room_id, 'posting anyway...', msgtype="m.notice")
                    post = create_posts(postData, True)
                    if 'postURL' not in post:
                        await matrix.api.send_markdown_message(room.room_id, '**CATBOX UPLOAD ERROR**', msgtype="m.notice")
                        return
                    await matrix.api.send_text_message(room.room_id, post['message']+'\n'+postData['rateLimit']+' dailysaucenao uses left', msgtype="m.notice")
                else:
                    await matrix.api.send_text_message(room.room_id, 'cancelled, nothing was posted or saved', msgtype="m.notice")
                botState = 'ready'

            elif botState == 'savechecking':
                if match.command('yes') or match.command('Yes'):
                    await matrix.api.send_text_message(room.room_id, 'saving anyway...', msgtype="m.notice")
                    post = save_posts(postData, True)
                    if 'postURL' not in post:
                        await matrix.api.send_markdown_message(room.room_id, '**CATBOX UPLOAD ERROR**', msgtype="m.notice")
                        return
                    files = str(len(listdir(os.path.curdir+'/saved')))
                    await matrix.api.send_text_message(room.room_id, 'post saved for later, '+files+' saved posts', msgtype="m.notice")
                else:
                    await matrix.api.send_text_message(room.room_id, 'cancelled, nothing was posted or saved', msgtype="m.notice")
                botState = 'ready'

    timerposter.start()
    time.sleep(2)
    matrix.run()
