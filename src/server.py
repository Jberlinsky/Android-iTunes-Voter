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
import random
import simplejson
import base64

COVER_ART_URL = "http://www.freecovers.net/api/search/%s"

def currently_playing_song(songs):
    for song in songs:
        if song.playing:
            return song
    return None

def song_with_most_votes(songs):
    max_song = None
    max_votes = 0
    chosen = False
    for song in songs:
        if song.votes > max_votes:
            max_song = song
            max_votes = song.votes
            chosen = True
    if not chosen:
        max_song = random.choice(songs)
    return max_song

def reset_votes(songs):
    for song in songs:
        song.votes = 0

def new_song():
    song = currently_playing_song(songs)
    if song is not None:
        song.playing = False
    print "Time for a new song!"
    song = song_with_most_votes(songs)
    print "Playing", song.name
    play(song)

def find_song_by_id(song_id):
    for song in songs:
        if song.sid == song_id:
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
                if song.sid == int(sid):
                    song.votes += 1
                    self.write(str(song.votes))
                    wrote = True
        if not wrote:
            self.write("-1")

class VotedOnApiHandler(cyclone.web.RequestHandler):
    def get(self):
        s = songs_with_votes(songs)
        self.write(simplejson.dumps([song.dump() for song in s]))

class SongsApiHandler(cyclone.web.RequestHandler):
    def get(self):
        self.write(simplejson.dumps([song.dump() for song in songs]))

class NowPlayingApiHandler(cyclone.web.RequestHandler):
    def get(self):
        self.write(simplejson.dumps([currently_playing_song(songs).dump()]))

class Song:
    def __init__(self, track_length=0, sid=0, name="",
            album="",artist="",votes=0,playing=False, obj=None):
        self.track_length = track_length
        self.name = name
        self.album = album
        self.artist = artist
        self.votes = votes
        self.playing = False
        self.obj = obj
        self.sid = sid
        self.image_base64 = ""

    def play(self):
        self.obj.play()

    def image_data(self):
        if self.image_base64 is not "":
            return self.image_base64
        else:
            self.image_base64 = self.imgdata()
            return self.image_base64

    def imgdata(self):
        if len(self.obj.artworks()) > 0:
            return base64.b64encode(self.obj.artworks()[0].data_.get().data)
        else:
            return ""

    def dump(self):
        dictionary = {}
        dictionary['votes'] = self.votes
        dictionary['playing'] = self.playing
        dictionary['song_id'] = self.sid
        return dictionary

    def __repr__(self):
        dictionary = {}
        dictionary['votes'] = self.votes
        dictionary['playing'] = self.playing
        dictionary['song_id'] = self.sid
        return json.dumps(dictionary)

class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
                (r"/", IndexHandler),
                (r"/vote", VoteHandler),
                (r"/voted_api", VotedOnApiHandler),
                (r"/songs_api", SongsApiHandler),
                (r"/now_playing", NowPlayingApiHandler)
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
        songs.append(Song(track_length=song.duration(), sid=song.id(), album=song.album(),
            artist=song.artist(), name=song.name(), obj=song))
    log.startLogging(sys.stdout)
    new_song()
    reactor.listenTCP(8888, Application())
    reactor.run()



