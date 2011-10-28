import cyclone.web
import cyclone.locale
from twisted.application import service, internet
from appscript import *
import redis

def create_vote_dict(songs):
    votes = {}
    for song in songs:
        votes[song.id()] = song.name()

class IndexHandler(BaseHandler):
    def get(self):
        self.render("index.html")

    def post(self):
        song_id = self.get_argument("song_name")
        song_votes[song_id] += 1
        self.render("post_message.html")

class ApplicationHandler(cyclone.web.Application):
    def __init__(self):
        handlers = [
                (r"/", IndexHandler)
        ]

        settings = {
                "static_path": "./static",
                "template_path": "./template",
        }

        cyclone.web.Application.__init__(self, handlers, **settings)

application = service.Application("srvr")

itunes = app('itunes')

r = redis.StrictRedis(host='localhost', port=6379, db=0)
# Clear out Redis
# Read in song data
songs = itunes.tracks()
song_votes = create_vote_dict(songs)

internet.TCPServer(8888, Application(),
        interface="0.0.0.0").setServiceParent(application)

