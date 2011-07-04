import random
import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from gevent import Greenlet
import jingo
from redis import Redis
import simplejson as json

from sumo.utils import redis_client
from sumo.helpers import urlparams


@require_GET
def chat(request):
    """Display the current state of the chat queue."""
    nonce = None
    new_room = make_nonce()
    if 'room' in request.GET and is_nonce(request.GET['room']):
        room = request.GET['room']
    else:
        response = HttpResponseRedirect('chat')
        response['Location'] = urlparams(response['Location'], room=new_room)
        return response
    if request.user.is_authenticated():
        nonce = make_nonce()
        redis_client('chat').setex('chatnonce:{n}'.format(n=nonce), 
                                   request.user.username, 60)
    return jingo.render(request, 'chat/chat.html', {'nonce': nonce, 'room': room})


@never_cache
@require_GET
def queue_status(request):
    """Dump the queue status out of the cache.

    See chat.crons.get_queue_status.

    """
    xml = cache.get(settings.CHAT_CACHE_KEY)
    status = 200
    if not xml:
        xml = ''
        status = 503
    return HttpResponse(xml, mimetype='application/xml', status=status)


def make_nonce():
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz234567')
                   for _ in xrange(10))

def is_nonce(nonce):
    p = re.compile('^[a-z2-7]{10}$')
    return p.match(nonce)

def map_sid_to_nick(nonce, sid):
    user_nick = redis_client('chat').get('chatnonce:{n}'.format(n=nonce))
    if user_nick is not None:
        redis_client('chat').set('chatsid:{n}'.format(n=sid), user_nick)
        return True
    else:
        return False

def nick_from_chat_sid(sid):
    nick = redis_client('chat').get('chatsid:{n}'.format(n=sid))
    return nick or sid

def chat_socketio(io):
    CHANNEL = 'world'
    error_occurred = False

    def subscriber(io):
        try:
            redis_in = redis_client('chat')
            redis_in.subscribe(CHANNEL)
            redis_in_generator = redis_in.listen()

            # io.connected() never becomes false for some reason.
            while io.connected():
                for from_redis in redis_in_generator:
                    print 'Incoming: %s' % from_redis
                    if from_redis['type'] == 'message':  # There are also subscription notices.
                        io.send(from_redis['data'])
        finally:
            print "EXIT SUBSCRIBER %s" % io.session

    if io.on_connect():
        print "CONNECT %s" % io.session
    else:
        print "SOMETHING OTHER THAN CONNECT!"  # I have never seen this happen.

    for i in range(0, 20):
        message = io.recv()
        if message:
            joinmsg = json.loads(message[0])
            if joinmsg['type'] == 'joined':
                if is_nonce(joinmsg['room']):
                    CHANNEL = joinmsg['room']
                    # Hanging onto this might keep it from the GC:
                    in_greenlet = Greenlet.spawn(subscriber, io)
                    if map_sid_to_nick(joinmsg['payload'], io.session.session_id) is False:
                        error_occurred = True
                        io.send('You have been disconnected for inactivity. Please refresh the page.')
                        break
                    redis_client('chat').publish(CHANNEL, nick_from_chat_sid(io.session.session_id) + ' has joined')
                    break
                else:
                    error_occured = True
        if i == 20:
            error_occurred = True
    

    # Until the client disconnects, listen for input from the user:
    while io.connected() and not error_occurred:
        message = io.recv()
        if message:  # Always a list of 0 or 1 strings, I deduce from the source code
            to_redis = json.loads(message[0])
            # On the chance that a user disconnects (loss of internet) and socketio
            # autoreconnects, a new session_id is given. However, the nonce is still
            # the same since the page hasn't been reloaded. There's a slim case where
            # getting the username via nonce fails (expired), so the username defaults
            # to the session ID, at the moment.
            # TODO: In the above case, XHR request a new nonce and update?
            # TODO: Replace flat strings with JSON objects (etc). 
            if to_redis['type'] == 'joined':  # Runs on reconnect
                if map_sid_to_nick(to_redis['payload'], io.session.session_id) is False:
                    io.send('You have been disconnected for inactivity. Please refresh the page.')
                    break
            else:
                print 'Outgoing: %s' % to_redis
                redis_client('chat').publish(CHANNEL, nick_from_chat_sid(io.session.session_id) + ': ' + to_redis['payload'])

    print "EXIT %s" % io.session

    if error_occurred:
        print "ERROR OCCURED!!!"

    # Clean up cache.
    redis_client('chat').delete(io.session.session_id)

    # Each time I close the 2nd chat window, wait for the old socketio() view
    # to exit, and then reopen the chat page, the number of Incomings increases
    # by one. The subscribers are never exiting. This fixes that behavior:
    in_greenlet.kill()

    redis_client('chat').publish(CHANNEL, nick_from_chat_sid(io.session.session_id) + ' has disconnected')

    return HttpResponse()
