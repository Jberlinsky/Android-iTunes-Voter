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
        slist = unicodedata.normalize('NFKD',
                self.get_argument("song_list")).encode('ascii', 'ignore')
        song_ids = slist.split(",")
        for sid in song_ids:
            if sid is not '':
                for song in songs:
                    if song.id == sid:
                        song.votes += 1
        self.render("vote.html", songs=songs)

        """
        song_ids = self.get_argument("song_ids")
        print song_ids
        for sid in song_ids:
            song_votes[sid] += 1
        self.render("post_vote_message.html")
        """

class VotedOnApiHandler(cyclone.web.RequestHandler):
    def get(self):
        s = [song for song in songs_with_votes(songs)]
        self.write(json.dumps(SongJSONEncoder().encode(s)))

class SongsApiHandler(cyclone.web.RequestHandler):
    def get(self):
        self.write(SongJSONEncoder().encode(songs))

class Song:
    def __init__(self, track_length=0, id=0, name="",
            album="",artist="",votes=0,playing=False):
        self.track_length = track_length
        self.name = name
        self.album = album
        self.artist = artist
        self.votes = votes
        self.playing = False

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

if __name__ == "__main__":
    itunes = app('itunes')

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    # Clear out Redis
    # Read in song data
    songs = []
    tmp_songs = itunes.tracks()
    for song in tmp_songs:
        songs.append(Song(track_length=song.duration(), id=song.id(), album=song.album(),
            artist=song.artist(), name=song.name()))
    log.startLogging(sys.stdout)
    reactor.listenTCP(8888, Application())
    reactor.run()



