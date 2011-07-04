#TODO: 
#   -until it's time for code cleanup, will remain monolithic
#   -figure out some way to make use of io.session.session_id
#   -we may need to sanitize all the variables going into redis, in case it
#       is possible to insert spaces and execute redis commands...
#   -Current design is not secure. It will prevent someone from impersonating
#       another, but won't stop someone from intercepting keys by sniffing.
#       Consider using https
#   -consider different capitalization for fns vs vars to improve readability
#   -when I open a chat and inspect with firebug, net shows that something is
#       referencing looking for http://localhost:8000/socket.io/lib/
#                                       vendor/web-socket-js/WebSocketMain.swf
#       figure out what is doing this and why
import random
import re
import hashlib
#NOTE: pulled from sumo helpers for monolith
import urlparse
#end NOTE
from datetime import datetime
from time import time

from django.conf import settings
from django.core.cache import cache
from django.core.cache import parse_backend_uri
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
#NOTE: pulled from sumo helpers for monolith
from django.http import QueryDict
from django.utils.http import urlencode
#end NOTE

#NOTE: import either the kitsune access/decorators or use built in django
#   decorators for login_required.
# also import the user auth models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
#end NOTE
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

from gevent import Greenlet
import jingo
from redis import Redis
import simplejson as json

#NOTE: pulling required components instead of importing
# from sumo.utils import redis_client
# from sumo.helpers import urlparams
#end Note

#@require_GET
@login_required
def livechat(request):

    user_id = request.user.id    
        
    # Check if user targeted another user yet
    if 'target' not in request.POST:
        # Bring up prompt to select user to chat with
        return jingo.render(
            request,
            'livechat/target.html',
            {'user_id': user_id} )

    target_id = request.POST['target']

    #TODO: make sure user is allowed to chat with this person first
    if not user_can_talk_to_target(user_id, target_id):
        #die gracefully
        bad_user_selection = 'Sorry, you selected an invalid target. Try again'
        return jingo.render(
            request,
            'livechat/target.html',
            {'user_id': user_id, 'bad_user_selection': bad_user_selection} )
        return response
    
    # Now that we know chat is allowed create the chat_id. 
    # Given two user_ids it should always be the same fixed value
    chat_id = generate_chat_id( [user_id, target_id] )
    
    #register chat key with redis
    chat_key = generate_chat_key( [user_id, target_id], '68LC040' )
    redis_client('livechat').hset(
                                '{u}_creds_{c}'.format(c=chat_id, u=user_id),
                                'chat_key',
                                chat_key)
    
    #register user_id->username in redis
    username = str(User.objects.get(id=user_id).username)
    redis_client('livechat').set('name_for_uid_{u}'.format(u=user_id), username)
    
    #check if a chat queue exists for these two users in redis yet
    #NOTE: might not need to do it here. maybe later when grabbing chat history
    b_chat_queue = redis_client('livechat').exists('chat_id:{c}'.format(c=chat_id))
    if not b_chat_queue:
        #add chat to redis
        redis_client(
        'livechat').rpush('chat_id:{c}'.format(c=chat_id),'CHAT_START')
            
    return jingo.render(
        request,
        'livechat/livechat.html',
        {'chat_id': chat_id,
        'user_id': user_id,
        'target_id': target_id,
        "chat_key": chat_key} )

#stub code for verifying a user can talk to the person they targeted
#fill in with proper code later
def user_can_talk_to_target(user_id, target_id):
    if( str(user_id) == str(target_id)
    or str(target_id) == ''
    or not user_exists(target_id) ):
        return False
    return True

def user_exists(user_id):
    try:
        userobj = User.objects.get(id=user_id)
    except:
        return False
    return True


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

#NOTE: adding this in temporarily
#   going with a list of uids in case we want to scale to multi-user chats
#   but this might require changing the conversation id when new users
#   are added.
# make_conversation: expect a list of user ids. handle only 2 for now
def generate_chat_id(user_id_list):
    user_id_list = [str(uid) for uid in user_id_list]
    delimiter = 'bojak' # choose something that won't be in uids
    user_id_list.sort() #sort before joining
    chat_id = delimiter.join( user_id_list ) 
    return chat_id

#check_user_valid wants:
#   -chat_id: chat they say they want to join
#   -user_id: as retrieved from backend
#   -target_id: person they say they want to talk to
#NOTE: rename this and other refs to 'user_nick'
def check_user_valid(requested_chat_id, user_id, target_id):
    generated_chat_id = generate_chat_id( [user_id, target_id] )
    #NOTE: it might seem reduntant to check for chat_exists here, and ultimately
    #   it probably is since to get to this pt, a chat should've been created.
    #   but it will eliminate those cases where someone tries to directly inject
    #   a target without going through the proper channels (if that is possible)
    chat_exists = redis_client('livechat').exists('chat_id:{c}'.format(c=requested_chat_id))
    
    if generated_chat_id == requested_chat_id and chat_exists:
        return True
    else:
        return False
    #NOTE: chat_contents not used yet
#     chat_contents = redis_client('livechat').get('chat_id:{c}'.format(c=chat_id))
#     if chat_contents is not None:
#         #NOTE: don't need this
#         #redis_client('livechat').set('chatsid:{n}'.format(n=sid), user_nick)
#         return True
#     else:
#         return False

def verify_chat_key(provided_key, user_id, chat_id):
    required_key = redis_client('livechat').hget(
        '{u}_creds_{c}'.format(c=chat_id, u=user_id),
        'chat_key'
        )
    if required_key == provided_key:
        return True
    else:
        print "------------------------------"
        print "KEYS DON'T MATCH!"
        print provided_key
        print "vs"
        print required_key
        return False
    

def generate_chat_key(user_id_list, salt):
    # make sure salt is a str before hashing it
    salt = str(salt)
    # generating chat_id again instead of passing it as a param, but it might be
    # more efficient other way around...
    chat_id = generate_chat_id( user_id_list )
    chat_id_hash = hashlib.md5(chat_id + salt)
    time_hash = hashlib.md5( str( time() ) + salt)
    chat_key = time_hash.hexdigest() + chat_id_hash.hexdigest()
    return chat_key


#NOTE: pulled from sumo utils to add to monolith
def redis_client(name):
    """Get a Redis client.

    Uses the name argument to lookup the connection string in the
    settings.REDIS_BACKEND dict.
    """
    uri = settings.REDIS_BACKENDS[name]
    _, server, params = parse_backend_uri(uri)
    db = params.pop('db', 1)
    try:
        db = int(db)
    except (ValueError, TypeError):
        db = 1
    try:
        socket_timeout = float(params.pop('socket_timeout'))
    except (KeyError, ValueError):
        socket_timeout = None
    password = params.pop('password', None)
    if ':' in server:
        host, port = server.split(':')
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 6379
    else:
        host = 'localhost'
        port = 6379
    return Redis(host=host, port=port, db=db, password=password,
                 socket_timeout=socket_timeout)
#end NOTE

#NOTE: pulled from sumo helper to add to monolith
def urlparams(url_, hash=None, query_dict=None, **query):
    """
    Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url_ = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url_.fragment

    q = url_.query
    new_query_dict = (QueryDict(smart_str(q), mutable=True) if
                      q else QueryDict('', mutable=True))
    if query_dict:
        for k, l in query_dict.lists():
            new_query_dict[k] = None  # Replace, don't append.
            for v in l:
                new_query_dict.appendlist(k, v)

    for k, v in query.items():
        new_query_dict[k] = v  # Replace, don't append.

    query_string = urlencode([(k, v) for k, l in new_query_dict.lists() for
                              v in l if v is not None])
    new = urlparse.ParseResult(url_.scheme, url_.netloc, url_.path,
                               url_.params, query_string, fragment)
    return new.geturl()
#end NOTE