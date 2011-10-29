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
import pybonjour

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
    play(song)

def find_song_by_id(song_id):
    for song in songs:
        if song.id == song_id:
            return song
    return None

def play(song):
    song.playing = True
    # Set a counter to fire after the duration.
    t = threading.Timer(song.duration, function=new_song)
    t.daemon = True
    t.start()
    reset_votes(songs)

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
        sid = unicodedata.normalize('NFKD',
                self.get_argument("song_list")).encode('ascii', 'ignore')
        if sid is not '':
            for song in songs:
                if song.id == sid:
                    song.votes += 1
        self.render("vote.html", songs=songs)

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

    def play(self):
        self.obj.play()

    def __repr__(self):
        dictionary = {}
        dictionary['name'] = self.name
        dictionary['track_length'] = self.track_length
        dictionary['album'] = self.album
        dictionary['artist'] = self.artist
        dictionary['votes'] = self.votes
        dictionary['playing'] = self.playing
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

def register_callback(sdRef, flags, errorCode, name, regtype, domain):
    if errorCode == pybonjour.kDNSServiceErr_NoError:
        print "Successfully registered as a Bonjour service!"

if __name__ == "__main__":
    # Register as a Bonjour service
    sdRef = pybonjour.DNSServiceRegister(name="",
                                        regtype="_test._tcp",
                                        port=1092,
                                        callBack=register_callback)

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
    reactor.listenTCP(8888, Application())
    reactor.run()



