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

help_message = '''Simply send me an image, a link to an image, or link to a pixiv or danbooru page to create posts. If you configured a folder from which I can pick random files to post, use the "next" command to do this.

next/rand/r - suggest a random image to post
status - show information about saved posts
T <Title> - set a post title
A <Artist> - set artist name
Tt - translate title
Ta - translate artist
L <links> - links separated by spaces to include in the post body
R - toggle post nsfw/sfw
C <communities> - communities to post to, separated by spaces, accepts partial or full community names without leading "!"
Post - post current post now
Save - save current post for later
Cancel - discard current post, neither posting nor saving
Randompost - post a random saved post
Stop - stop lemmytrixposter
'''

default_config = '''# Path to a folder from which the tool can pull random images for you to make posts from, save images here to post them later,
# or point it to your existing stash :D
RandomSourcePath = "/path/to/a/folder"
# Whether to delete the source file that was used to create a post
# When set to true images in RandomSourcePath WILL BE DELETED as they get posted
DeleteOncePosted = true
# Whether to save a copy of the highest available quality file in the /posted folder for each image that is posted
SavePosted = true

# Whether the tool should attempt to automatically determine suitable communities, this is done using danbooru tags
# You can always override whatever is detected
AutoDetectCommunities = true

# This list is used to autocomplete communites for you when their name is entered only partially.
# This makes editing posts faster, as you don't have to type the full names of communities.
# You can add any communities you want, and then easily post to them by writing just a few charachters of the name when using the "c" command.
# You can also list danbooru tags that you would like match to certain communities to auto-select images for posting to them.
[Communities]
"fitmoe@lemmy.world" = ['muscular', 'toned', 'excercice']
"murdermoe@lemmy.world" = ['yandere', 'evil_smile', 'evil_grin', 'crazy_eyes', 'blood_on_weapon']
"fangmoe@ani.social" = ['fang', 'fangs']
"cybermoe@ani.social" = ['cyberpunk', 'cyborg', 'science_fiction', 'mecha', 'robot', 'android']
"kemonomoe@ani.social" = ['animal_ears']
"midriffmoe@ani.social" = ['midriff', 'stomach']
"streetmoe@ani.social" = ['streetwear']
"thiccmoe@ani.social" = ['huge_breasts', 'large_breasts', 'thick_thighs', 'love_handles', 'plump', 'curvy', 'wide_hips']
"officemoe@ani.social" = ['salaryman', 'office_lady', 'office_chair', 'office']
"meganemoe@ani.social" = ['glasses']
"chainsawfolk@lemmy.world" = ['chainsaw_man']
"helltaker@sopuli.xyz" = ['helltaker']
"bocchitherock@sopuli.xyz" = ['bocchi_the_rock!']
"overlord@sopuli.xyz" = ['overlord_(maruyama)']
"killlakill@lemmy.world" = ['kill_la_kill']
"dungeonmeshi@ani.social" = ['dungeon_meshi']
"lycorisrecoil@reddthat.com" = ['lycoris_recoil']
"onepiece@lemmy.world" = ['one_piece']
"opm@lemmy.world" = ['one_punch_man']
"hatsunemiku@lemmy.world" = ['hatsune_miku']
"hololive@lemmy.world" = ['hololive']
"gothmoe@ani.social" = ['goth_fashion']
"morphmoe@ani.social" = ['personification']
"militarymoe@ani.social" = ['gun', 'military']
"wholesomeyuri@reddthat.com" = ['yuri']
"frieren@ani.social" = ['sousou_no_frieren', 'frieren']
"animearmor@lemm.ee" = ['armor']
"touch_fluffy_tail@ani.social" = ['fox_tail', 'wolf_tail', 'holding_own_tail']
"FloatingIsFun@fedia.io" = []
"anime_art@ani.social" = []
"animepics@reddthat.com" = []
"sliceoflifeanime@lemmy.world" = []
"gameart@sopuli.xyz" = []
"vgartwork@lemmy.zip" = []

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
# Users that can interact with the bot (if multiple, serparate with commas, like communities above), and the room it should operate in
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

if not os.path.isfile(os.path.curdir+'/lemmytrixposter.toml'):
    f = open( os.path.curdir+'/lemmytrixposter.toml', 'w' )
    f.write( default_config )
    f.close()
    print('Lemmytrixposter has not been configured, created sample config file')
    print('Please follow instructions within for setup')
    sys.exit()

# Load configs
config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))

# saucenao
sauce = SauceNao(config['SauceNao']['api_key'])

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


def save_for_repost_check(postData):
    postedIDs = []
    if os.path.isfile(os.path.curdir+'/posted.json'):
        postedIDs = json.load(open(os.path.curdir+'/posted.json', 'r'))
    if 'danbooruID' in postData:
        postedIDs.append('danbooru'+postData['danbooruID'])
    if 'pixivID' in postData:
        postedIDs.append('pixiv'+postData['pixivID'])
    if 'html' not in os.path.basename(postData['postURL']):
        postedIDs.append('catbox'+os.path.basename(postData['postURL']))
    with open(os.path.curdir+'/posted.json', 'w') as posted:
        json.dump(postedIDs, posted)


def check_repost(postData):
    if os.path.isfile(os.path.curdir+'/posted.json'):
        postedIDs = json.load(open(os.path.curdir+'/posted.json', 'r'))
    else:
        return False
    if 'danbooruID' in postData and 'danbooru'+postData['danbooruID'] in postedIDs:
        return True
    if 'pixivID' in postData and 'pixiv'+postData['pixivID'] in postedIDs:
        return True
    if 'postURL' in postData and 'catbox'+os.path.basename(postData['postURL']) in postedIDs:
        return True
    else:
        return False


def get_status():
    files = listdir(os.path.curdir+'/saved')
    amount = str(len(files))
    breakdown = {}
    for post in files:
        data = json.load(open(os.path.curdir+'/saved/'+post, 'r'))
        for community in data['postCommunities'].keys():
            if community not in breakdown:
                breakdown[community] = 1
            else:
                breakdown[community] += 1
    message = 'There are '+amount+' saved posts'
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


def edit_links(links):
    new_links = ''
    for link in links.split():
        new_links += ' | '
        if 'danbooru' in link:
            new_links += '[danbooru]'
        else:
            new_links += '['+urlparse(link).netloc.split('.')[-2]+']'
        new_links += '('+link+')'
    return new_links


def pick_random():
    randomSourcePath = config['RandomSourcePath']
    return random.choice(glob.glob(randomSourcePath+'/**/*.*', recursive=True))


def check_communities(postData):
    if len(postData['postCommunities']) > 0:
        return True
    return False


def download_image(url):
    with open(os.path.curdir+'/tmp/lemmytrixposter/'+os.path.basename(url), 'wb') as handler:
        response = requests.get(url, headers=headers)
        if not response.ok:
            return None
        handler.write(response.content)
        return os.path.curdir+'/tmp/lemmytrixposter/'+os.path.basename(url)


def upload_image(postData):
    if 'postURL' in postData:
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


def postdata_from_input(providedInput, tmp_path='/lemmytrixposter'):
    if type(providedInput) != str:
        return None

    providedInput = providedInput.split('?')[0]

    # pixiv
    config = toml.load(open(os.path.curdir+'/lemmytrixposter.toml', 'r'))
    pixiv = AppPixivAPI()
    pixiv.auth(refresh_token=config['Pixiv']['token'])

    postData = {}
    postData['providedInput'] = providedInput
    if os.path.isfile(providedInput):
        postData['imageFile'] = providedInput
    else:
        # Detect pixiv link or file
        if 'fanbox' not in providedInput and re.search('pixiv.net\/.*\d{8,9}|\d{8,9}_p[0-9]*.jpg|\d{8,9}_p[0-9]*.png', providedInput):
            postData['pixivID'] = re.search('\d{8,9}', providedInput).group(0)
            postData['pixivURL'] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id='+postData['pixivID']
            print('Pixiv ID detected: '+ postData['pixivID'])
            pixivData = pixiv.illust_detail(postData['pixivID'])
            if not 'error' in pixivData:
                # Download full quality image from pixiv, if link
                if re.search('pixiv.net\/.*\d{8,9}', providedInput) and pixivData.illust.type != 'ugoira':
                    print('Downloading image from pixiv...')
                    if pixivData.illust.page_count == 1:
                        downloadURL = pixivData.illust.meta_single_page.original_image_url
                    else:
                        downloadURL = pixivData.illust.meta_pages[0].image_urls.original
                    pixiv.download(downloadURL, path=os.path.curdir+'/tmp'+tmp_path )
                    postData['pixivFile'] = os.path.curdir+'/tmp'+tmp_path+'/'+os.path.basename(downloadURL)
                    postData['imageFile'] = postData['pixivFile']

        # Detect danbooru link
        if re.search('danbooru.donmai.us\/.*post.*\/\d\d*', providedInput):
            print('Downloading image from danbooru...')
            postData['danbooruID'] = re.search( r'\d+', providedInput ).group(0)
            danbooruData = danbooru.post_show(postData['danbooruID'])
            postData['danbooruFile'] = download_image(danbooruData['file_url'])
            postData['danbooruFileURL'] = danbooruData['file_url']
            postData['imageFile'] = postData['danbooruFile']

        # Detect/download image from URL
        if re.search('https:\/\/.*\/.*\.\w{3,4}', providedInput):
            print('Downloading image...')
            postData['imageFile'] = download_image(providedInput)

    if 'imageFile' not in postData:
        return 'Unable to find an image file using input'

    # Create thumbnail for use with saucenao and messaging
    sauce_size = 600, 600
    print('Creating thumbnail...')
    with Image.open(postData['imageFile'] ) as image:
        image.thumbnail(sauce_size)
        image.save(os.path.curdir+'/tmp'+tmp_path+'/sauce_thumb.webp', 'WEBP')
    postData['imageThumb'] = os.path.curdir+'/tmp'+tmp_path+'/sauce_thumb.webp'

    # Grab info from saucenao
    print('Getting sources from saucenao...')
    try:
        results = sauce.from_file(postData['imageThumb'])
    except Exception:
        return 'SauceNao ratelimit exceeded'
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
                if 'fanbox' not in url and re.search('pixiv|pximg', url) and 'pixivURL' not in postData:
                    postData['pixivID'] = re.search('\d+', url.split('https')[-1]).group(0)
                    postData['pixivURL'] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id='+postData['pixivID']
                if 'twitter' in url and 'twitterURL' not in postData:
                    postData['twitterURL'] = url
                if 'artstation' in url and 'artstationURL' not in postData:
                    postData['artstationURL'] = url
                if 'danbooru' in url and 'danbooruURL' not in postData:
                    postData['danbooruURL'] = url
                    postData['danbooruID'] = re.search( r'\d+', url.split('https')[-1] ).group(0)
                if 'deviantart' in url and 'deviantURL' not in postData:
                    postData['deviantURL'] = url
            try:
                print('Source found: '+result.raw['data']['source'])
                if 'fanbox' not in result.raw['data']['source'] and re.search('pixiv|pximg', result.raw['data']['source']) and 'pixivURL' not in postData:
                    postData['pixivID'] = re.search('\d{8,9}', result.raw['data']['source']).group(0)
                    postData['pixivURL'] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id='+postData['pixivID']
                if 'twitter' in result.raw['data']['source'] and 'twitterURL' not in postData:
                    postData['twitterURL'] =  result.raw['data']['source']
                if 'artstation' in  result.raw['data']['source'] and 'artstationURL' not in postData:
                    postData['artstationURL'] =  result.raw['data']['source']
                if 'deviantart' in  result.raw['data']['source'] and 'deviantURL' not in postData:
                    postData['deviantURL'] =  result.raw['data']['source']
            except Exception:
                pass

    if 'danbooruData' not in locals() and 'danbooruID' in postData:
        danbooruData = danbooru.post_show(postData['danbooruID'])
        print('Getting image data from danbooru...')
    if 'danbooruData' in locals():
        danbooruTags = danbooruData['tag_string'].split()
        danbooruRating = danbooruData['rating']

    # Get possibly higher quality image files
    if 'pixivFile' not in postData and 'pixivID' in postData:
        if 'pixivData' not in locals():
            pixivData = pixiv.illust_detail(postData['pixivID'])
        if 'illust' in pixivData:
            if re.search('pixiv.net\/.*\d{8,9}', providedInput) and pixivData.illust.page_count == 1 and pixivData.illust.type != 'ugoira':
                print('Downloading image from pixiv...')
                downloadURL = pixivData.illust.meta_single_page.original_image_url
                pixiv.download(downloadURL, path=os.path.curdir+'/tmp'+tmp_path )
                postData['pixivFile'] = os.path.curdir+'/tmp'+tmp_path+'/'+os.path.basename(downloadURL)
                if os.path.getsize(postData['pixivFile']) > os.path.getsize(postData['imageFile']):
                    postData['imageFile'] = postData['pixivFile']

    if 'danbooruFile' not in postData and 'danbooruID' in postData:
        print('Downloading image from danbooru...')
        postData['danbooruFile'] = download_image(danbooruData['file_url'])
        postData['danbooruFileURL'] = danbooruData['file_url']
        if os.path.getsize(postData['danbooruFile']) > os.path.getsize(postData['imageFile']):
            postData['imageFile'] = postData['danbooruFile']

    # Translate title
    if 'pixivData' in locals() and 'illust' in pixivData and pixivData.illust.visible:
        print('Using pixiv title')
        postData['postTitle'] = pixivData.illust.title
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
    if 'danbooruData' in locals():
        print('Using danbooru name')
        postData['artist'] = danbooruData['tag_string_artist'].replace('_', ' ').split(' (')[0].title()
    elif 'artist' not in postData and 'pixivData' in locals() and 'illust' in pixivData and pixivData.illust.visible:
        print('Using pixiv name')
        postData['artist'] = pixivData.illust.user.name.split('@')[0]
    if 'artist' not in postData or postData['artist'] == '':
        postData['artist'] = 'Unknown'
    elif postData['artist'][0].islower():
        postData['artist'] = postData['artist'].title()

    # Create post body string
    postData['postBody'] = 'Artist: **' + postData['artist'] + '**'
    if 'pixivURL' in postData and 'illust' in pixivData:
        if pixivData.illust.visible:
            postData['postBody'] += ' | [pixiv]('+postData['pixivURL']+')'
        else:
            postData['postBody'] += ' | [pixiv](https://www.pixiv.net/users/'+str(pixivData.illust.user.id)+')'
    if 'twitterURL' in postData:
        postData['postBody'] += ' | [twitter]('+postData['twitterURL']+')'
    if 'artstationURL' in postData:
        postData['postBody'] += ' | [artstation]('+postData['artstationURL']+')'
    if 'deviantURL' in postData:
        postData['postBody'] += ' | [deviantart]('+postData['deviantURL']+')'
    if 'danbooruURL' in postData:
        postData['postBody'] += ' | [danbooru]('+postData['danbooruURL']+')'

    # Get post NSFW status from user or determine based on danbooru rating
    postData['postNSFW'] = False
    try:
        if danbooruRating == 'e' or danbooruRating == 'q':
            postData['postNSFW'] = True
    except Exception:
         pass

    # Determine communities to post to
    postData['postCommunities'] = {}
    if config['AutoDetectCommunities'] and 'danbooruTags' in locals():
        for community in config['Communities']:
            for tag in config['Communities'][community]:
                if tag in danbooruTags and community not in postData['postCommunities']:
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
    preview += '\nEdit? **[T/Tt/A/Ta/L/R/C/Post/Save/Cancel]**'
    return preview


def create_posts(postData, force = False):
    postData = upload_image(postData)
    if '?' in postData['postURL'] or 'html' in postData['postURL']:
        return 'catbox error'
    if not force and check_repost(postData):
        return 'repost'

    if postData['postTitle'] == '':
        postData['postTitle'] = '(by ' + postData['artist'] + ')'
    else:
        postData['postTitle'] += ' (by ' + postData['artist'] + ')'

    print('Creating post/s...')
    message = 'Created post/s...'
    for community, account in postData['postCommunities'].items():
        communityID = lemmy.discover_community(community)
        post = lemmy.post.create(communityID, postData['postTitle'], url=postData['postURL'], body=postData['postBody'], nsfw=postData['postNSFW'])
        if post:
            print(f"Successfully posted ({post['post_view']['post']['ap_id']})")
            message += '\n'+post['post_view']['post']['ap_id']
        else:
            print('Failed to post to ' + community + ' using ' + account)
            message += '\nFailed to post to ' + community
    save_for_repost_check(postData)
    return message


def save_posts(postData, force = False):
    postData = upload_image(postData)
    if '?' in postData['postURL'] or 'html' in postData['postURL']:
        return 'catbox error'
    if not force and check_repost(postData):
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
    save_for_repost_check(postData)


last_posted = []
last_files = []


def post_random_saved():
    global last_posted
    global last_files
    fileList = listdir(os.path.curdir+"/saved")
    potentialPosts = {}
    if len(fileList) == 0:
        return "there are no saved posts"

    while (len(last_posted) > 6):
        last_posted.pop(0)
    while (len(last_files) > 6):
        last_files.pop(0)

    # Load some posts and rank them by how recently the target communities have been posted to
    loop = 0
    while (loop < 7 and loop < len(fileList)):
        loop += 1

        for f in fileList:
            postFile = os.path.curdir+"/saved/"+random.choice(fileList)
            with open(postFile, "r") as pf:
                postData = json.load(pf)
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

    # Create post/posts
    print("Connecting to lemmy...")
    lemmy = Lemmy('https://'+config['Lemmy']['instance'],request_timeout=30)
    lemmy.log_in(config['Lemmy']['username'], config['Lemmy']['password'])
    links = []
    posted = []
    failed = []
    print("Creating post/s...")
    for community, account in postData["postCommunities"].items():
        if community not in last_posted:
            last_posted.append(community)
        communityID = lemmy.discover_community(community)
        post = lemmy.post.create(communityID, postData["postTitle"], url=postData["postURL"], body=postData["postBody"], nsfw=postData["postNSFW"])
        if post:
            print(f"Successfully posted ({post['post_view']['post']['ap_id']})")
            links.append('Posted to [!'+community+']('+post['post_view']['post']['ap_id']+')')
            posted.append(community)
        else:
            print("Failed to post to " + community)
            failed.append(community)
        if not config['Timer']['cross_post_all_at_once']:
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
    message = ""
    for link in links:
        message += link+'  \n'
    files = str(len(fileList)-1)
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


timerposter = threading.Thread(target=timer_post_thread)
timerposter.daemon = True

if __name__ == '__main__':
    # Lemmy
    lemmy = Lemmy('https://'+config['Lemmy']['instance'], request_timeout=30)
    lemmy.log_in(config['Lemmy']['username'], config['Lemmy']['password'])

    # matrix
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
    async def autoposter(room, message):
        global botState
        global postData
        match = botlib.MessageMatch(room, message, matrix)

        if match.is_not_from_this_bot() and room.room_id == allowedRoom:
            if botState == 'ready':
                for f in listdir(os.path.curdir+'/tmp/lemmytrixposter'):
                    os.remove(os.path.curdir+'/tmp/lemmytrixposter/'+f)
                try:
                    if mc_path != '':
                        subprocess.run(['matrix-commander', '--download-media', os.path.curdir+'/tmp/lemmytrixposter/', '--tail', '1', '-s', mc_path+'/store/', '-c', mc_path+'/creds.json'])
                    else:
                        subprocess.run(['matrix-commander', '--download-media', os.path.curdir+'/tmp/lemmytrixposter/', '--tail', '1'])
                    inputFile = os.path.curdir+'/tmp/lemmytrixposter/'+listdir(os.path.curdir+'/tmp/lemmytrixposter')[0]
                except Exception:
                    await matrix.api.send_text_message(room.room_id, 'unable to receive file', msgtype="m.notice")
                await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                postData = postdata_from_input(inputFile)
                if postData != None:
                    await matrix.api.send_markdown_message(room.room_id, compose_preview(postData))
                    botState = 'editing'
                else:
                    await matrix.api.send_text_message(room.room_id, 'invalid input', msgtype="m.notice")


    @matrix.listener.on_message_event
    async def autoposter(room, message):
        global botState
        global postData
        global randomFile
        match = botlib.MessageMatch(room, message, matrix)

        if match.is_not_from_this_bot() and room.room_id == allowedRoom:
            if match.command('stop') or match.command('Stop'):
                await matrix.api.send_text_message(room.room_id, 'Stopping...', msgtype="m.notice")
                sys.exit()

            if botState == 'ready':

                if match.command('delete') or match.command('Delete'):
                    if os.path.isfile(randomFile):
                        os.remove(randomFile)
                        await matrix.api.send_text_message(room.room_id, 'deleted '+randomFile, msgtype="m.notice")
                    else:
                        await matrix.api.send_text_message(room.room_id, randomFile+' already deleted', msgtype="m.notice")
                    randomFile = pick_random()
                    size = 600, 600
                    with Image.open(randomFile) as image:
                        image.thumbnail(size)
                        image.save(os.path.curdir+'/tmp/lemmytrixposter/rand_thumb.webp', 'WEBP')
                    randomThumb= os.path.curdir+'/tmp/lemmytrixposter/rand_thumb.webp'
                    await matrix.api.send_image_message(room.room_id,image_filepath=randomThumb)
                    await matrix.api.send_markdown_message(room.room_id, '**[Select/Next/Delete]**')

                elif match.command('randompost') or match.command('Randompost'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    await matrix.api.send_markdown_message(room.room_id, post_random_saved()['message'], msgtype="m.notice")

                elif match.command('rand') or match.command('Rand') or match.command('r') or match.command('R') or match.command('next') or match.command('Next'):
                    randomFile = pick_random()
                    size = 600, 600
                    with Image.open(randomFile) as image:
                        image.thumbnail(size)
                        image.save(os.path.curdir+'/tmp/lemmytrixposter/rand_thumb.webp', 'WEBP')
                    randomThumb= os.path.curdir+'/tmp/lemmytrixposter/rand_thumb.webp'
                    await matrix.api.send_image_message(room.room_id,image_filepath=randomThumb)
                    await matrix.api.send_markdown_message(room.room_id, '**[Select/Next/Delete]**')

                elif match.command('select') or match.command('Select'):
                    await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                    postData = postdata_from_input(randomFile)
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
                if match.command('post') or match.command('Post'):
                    if check_communities(postData):
                        await matrix.api.send_text_message(room.room_id, 'working...', msgtype="m.notice")
                        post = create_posts(postData)
                        if post == 'repost':
                            botState = 'checking'
                            await matrix.api.send_markdown_message(room.room_id, 'this is a repost, post anyway? **[Yes/No]**', msgtype="m.notice")
                            return
                        elif post == 'catbox error':
                            await matrix.api.send_markdown_message(room.room_id, '**CATBOX UPLOAD ERROR**', msgtype="m.notice")
                        else:
                            await matrix.api.send_markdown_message(room.room_id, post+'\n'+postData['rateLimit']+' dailysaucenao uses left', msgtype="m.notice")
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
                        elif post == 'catbox error':
                            await matrix.api.send_text_message(room.room_id, '**CATBOX UPLOAD ERROR**', msgtype="m.notice")
                            botState = 'ready'
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
                    postData['postBody'] = re.sub('\*\*.*\*\*',  '**'+postData['artist']+'**', postData['postBody'] )
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
                    await matrix.api.send_text_message(room.room_id, create_posts(postData, True), msgtype="m.notice")
                else:
                    await matrix.api.send_text_message(room.room_id, 'cancelled, nothing was posted or saved', msgtype="m.notice")
                botState = 'ready'

            elif botState == 'savechecking':
                if match.command('yes') or match.command('Yes'):
                    await matrix.api.send_text_message(room.room_id, 'saving anyway...', msgtype="m.notice")
                    post = save_posts(postData, True)
                    files = str(len(listdir(os.path.curdir+'/saved')))
                    await matrix.api.send_text_message(room.room_id, 'post saved for later, '+files+' saved posts', msgtype="m.notice")
                else:
                    await matrix.api.send_text_message(room.room_id, 'cancelled, nothing was posted or saved', msgtype="m.notice")
                botState = 'ready'

    timerposter.start()
    time.sleep(2)
    matrix.run()
