import cyclone.web
import cyclone.locale
from twisted.python import log
from twisted.internet import reactor
import sys
from twisted.application import service, internet
from appscript import *
import redis
import unicodedata
import struct
import json
from json import JSONEncoder
import select
import urllib
import threading
#from lxml import etree

COVER_ART_URL = "http://www.freecovers.net/api/search/%s %s"

def song_with_most_votes(songs):
    max_song = None
    max_votes = -1
    for song in songs:
        if song.votes > max_votes:
            max_song = song
            max_votes = song.votes
    return max_song

def reset_votes(songs):
    for song in songs:
        song.votes = 0

def new_song():
    print "Time for a new song!"
    song = song_with_most_votes(songs)
    print "Playing", song.name
    play(song)

def find_song_by_id(song_id):
    for song in songs:
        if song.id == song_id:
            return song
    return None

def play(song):
    song.playing = True
    # Set a counter to fire after the duration.
    song.play()
    t = threading.Timer(song.track_length, function=new_song)
    t.daemon = True
    t.start()
    song.votes = 0

def songs_with_votes(songs):
    results = []
    for song in songs:
        if song.votes != 0:
            results.append(song)
    return results

class SongJSONEncoder(JSONEncoder):
    def default(self, o):
        return repr(o)

class IndexHandler(cyclone.web.RequestHandler):
    def get(self):
        self.render("index.html")

class VoteHandler(cyclone.web.RequestHandler):
    def get(self):
        self.render("vote.html", songs=songs)

    def post(self):
        wrote = False
        sid = unicodedata.normalize('NFKD',
                self.get_argument("song_list")).encode('ascii', 'ignore')
        if sid is not '':
            for song in songs:
                if song.id == int(sid):
                    song.votes += 1
                    self.write(str(song.votes))
                    wrote = True
        if not wrote:
            self.write("-1")

class VotedOnApiHandler(cyclone.web.RequestHandler):
    def get(self):
        s = [song for song in songs_with_votes(songs)]
        self.write(json.dumps(SongJSONEncoder().encode(s)))

class SongsApiHandler(cyclone.web.RequestHandler):
    def get(self):
        self.write(SongJSONEncoder().encode(songs))

class Song:
    def __init__(self, track_length=0, id=0, name="",
            album="",artist="",votes=0,playing=False, obj=None):
        self.track_length = track_length
        self.name = name
        self.album = album
        self.artist = artist
        self.votes = votes
        self.playing = False
        self.obj = obj
        self.id = id

    def play(self):
        self.obj.play()

    def imgurl(self):
        # Lazy load from an API
        url = COVER_ART_URL % (self.album, self.name)
        #tree = etree.parse(urllib.urlopen(url))
        return "http://placehold.it/50x50"
# tree.xpath("/rsp/title/covers/cover[type='front']/url")[0].text

    def __repr__(self):
        dictionary = {}
        dictionary['votes'] = self.votes
        dictionary['playing'] = self.playing
        dictionary['song_id'] = self.id
        return json.dumps(dictionary)

class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
                (r"/", IndexHandler),
                (r"/vote", VoteHandler),
                (r"/voted_api", VotedOnApiHandler),
                (r"/songs_api", SongsApiHandler)
        ]

        settings = {
                "static_path": "./static",
                "template_path": "./template",
        }

        cyclone.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    itunes = app('itunes')

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    # Clear out Redis
    # Read in song data
    songs = []
    tmp_songs = itunes.tracks()
    for song in tmp_songs:
        songs.append(Song(track_length=song.duration(), id=song.id(), album=song.album(),
            artist=song.artist(), name=song.name(), obj=song))
    log.startLogging(sys.stdout)
    new_song()
    reactor.listenTCP(8888, Application())
    reactor.run()



