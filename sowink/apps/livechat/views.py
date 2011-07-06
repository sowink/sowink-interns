#TODO: 
#   -I need to find a good time to put user's favorites into redis. ATM, I'm
#       doing it each time they open a new channel. Has the benefit of keeping
#       redis list of favorites up to date, so that if a user opens a new tab,
#       then changes favorites, the older tabs will no longer be able to start
#       new chats with former favorites. However, this won't unsubscribe them
#       from former favorites public channel. I'll need to handle this, most
#       likely in run_chat.py
#   -until it's time for code cleanup, this file will remain monolithic
#   -we may need to sanitize all the variables going into redis, in case it
#       is possible to insert spaces and execute arbitrary redis commands. I'll
#       need to double check how redis-py handles input strings
#   -Current design is not secure. It will prevent someone from impersonating
#       another, but won't stop someone from intercepting keys by sniffing.
#       Consider using SSL
#   -consider different capitalization for fns vs vars to improve readability.
#       -ClassNames
#       -functionNames
#       -variable_names
#   -I forgot the original reason I decided to mark keys as used. I think it was
#       to prevent key from being used again. But I dont think I do that anymore
#       so instead, I might set a timeout on the key. Once key is marked used,
#       remove the timeout. This will prevent unused keys from polluting redis
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
from django.http import QueryDict, Http404
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
    #NOTE: since I'm now opening new chat windows as a div inside main window,
    #   I'll have to figure out a way to instantiate a chat connection (generate
    #   keys, etc) each time a chat box is opened
    user_id = request.user.id    

    # set the control channel
    my_ctl_priv = "{u}_ctl_priv".format(u=user_id)
    
    #generate and register my_ctl_priv_key with redis
    #   create the key, register it, then mark it as init. Then in run_chat,
    #   when the session actually gets started, mark it as used
    my_ctl_priv_key = generate_chat_key( my_ctl_priv, '68LC040' )
    redis_client('livechat').hset('{u}_keys_to_{c}'.format(c=my_ctl_priv, u=user_id),
                                 my_ctl_priv_key, "init")
#     redis_client('livechat').hset(
#                                 '{u}_creds_{c}'.format(c=chat_id, u=user_id),
#                                 'chat_key',
#                                 chat_key)
    
    #register user_id->username in redis
    username = str(User.objects.get(id=user_id).username)
    redis_client('livechat').set('name_for_uid_{u}'.format(u=user_id), username)
            
    return jingo.render(
        request,
        'livechat/livechat.html',
        {'my_ctl_priv': my_ctl_priv,
        'user_id': user_id,
        "my_ctl_priv_key": my_ctl_priv_key} )

@require_POST
@login_required
def chatbox(request):
    # take an xhr post, acquire target, and perform necessary validation steps
    #NOTE: storing chat participants should be done in this function.

    user_id = request.user.id    

    # Check if user passed a target. if not, they shouldn't open this chatbox
    if 'target' not in request.POST:
        payload = { 'result': 'failure', 'message': 'no target specified'}
        return HttpResponse(json.dumps(payload), mimetype='applicaton/json')
    if 'box-id' not in request.POST:
        payload = { 'result': 'failure', 'message': 'no box-id specified'}
        return HttpResponse(json.dumps(payload), mimetype='applicaton/json')

    # get target_id
    target_id = request.POST['target']
    # get box_id
    box_id = request.POST['box-id']

    #NOTE: make sure user is allowed to chat with this person first
    if not user_can_talk_to_target(user_id, target_id):
        payload = { 'result': 'failure', 'message': 'invalid target', 'debug':'target='+target_id}
        return HttpResponse(json.dumps(payload), mimetype='applicaton/json')

    # Now that we know chat btwn these two is allowed, create the chat_id. 
    #   Given two user_ids it should always be the same fixed value
    chat_id = generate_chat_id( [user_id, target_id] )

    # generate and register my_ctl_priv_key with redis
    #   create the key, register it, then mark it as init. Then in run_chat,
    #   when the session actually gets started, mark it as used
    chat_key = generate_chat_key( chat_id, '68LC040' )
    redis_client('livechat').hset('{u}_keys_to_{c}'.format(c=chat_id, u=user_id),
                                 chat_key, 'init')
                                 
    # store chat participants ids in {c}_active if they don't exist yet (HSETNX)
    redis_client('livechat').hsetnx('{c}_active'.format(c=chat_id), user_id, 0)
    redis_client('livechat').hsetnx('{c}_active'.format(c=chat_id), target_id,0)
    
    #check if a chat queue exists for these two users in redis yet
    #NOTE: might not need to do it here. Maybe do it when grabbing chat history
#     b_chat_queue = redis_client('livechat').exists('chat_id:{c}'.format(c=chat_id))
#     if not b_chat_queue:
#         #add chat to redis
#         redis_client(
#         'livechat').rpush('chat_id:{c}'.format(c=chat_id),'CHAT_START')

    payload = { 'result': 'success',
                'chat_id': chat_id,
                'user_id': user_id,
                'target_id': target_id,
                'chat_key': chat_key,
                'box_id': box_id
                }
    return HttpResponse(json.dumps(payload), mimetype='applicaton/json')

#NOTE: stub code for verifying a user can talk to the person they targeted
#   fill in with proper code later
def user_can_talk_to_target(user_id, target_id):
    if( str(user_id) == str(target_id)
    or str(target_id) == ''
    or not user_exists(target_id) ):
        return False
    return True
    
#NOTE: stub code for verifying a chat can happen. Should incorporate
#   functionality of user_can_talk_to_target as well as user_is_online
def is_chat_session_allowed(user_id, target_id):
    #NOTE: with this implementation, permission will be attached to the user's,
    #   not the target's favorites information. Discuss with Paul which way to
    #   handle this (especially once blocking becomes enabled). Right now it's
    #   Fine since permission="allow" if target is in user's favorites. Simple.
    #NOTE: return dict{permission:value, online:t/f}? or ctl_chat_{SOMETHING}?
    #   Right now, I'll just return true/false based on a combination of
    #   permission and online status.
    
    #list of valid permissions, in case we need any others
    valid_permissions = ['allow']
    r_ufavs = '{u}_favorites'.format(u=user_id)
    permission = str(redis_client('livechat').hget(r_ufavs, target_id))
    if permission not in valid_permissions:
        return {'bool':False, 'why':'ctl_chat_deny'}
    if user_is_online(target_id):
        return {'bool':False, 'why':'ctl_chat_offline'}
    return {'bool':True, 'why':'ctl_chat_accept'}

def user_exists(user_id):
    try:
        userobj = User.objects.get(id=user_id)
    except:
        return False
    return True

#NOTE: adding this in temporarily
#   going with a list of uids in case we want to scale to multi-user chats
#   but this might require changing the conversation id when new users
#   are added.
# generate_chat_id: expect a list of user ids. handle only 2 for now
def generate_chat_id(user_id_list):
    user_id_list = [str(uid) for uid in user_id_list]
    delimiter = 'bojak' # choose something that won't be in uids
    user_id_list.sort() #sort before joining
    chat_id = delimiter.join( user_id_list ) 
    return chat_id

#check_user_valid:
#   -chat_id: chat they say they want to join
#   -user_id: as retrieved from backend
#   -target_id: person they say they want to talk to
#NOTE: it looks like I don't use this anymore in favor of verify_chat_key
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

def verify_chat_key(provided_key, user_id, chat_id):
    b_key_valid = redis_client('livechat').hget(
        '{u}_keys_to_{c}'.format(c=chat_id, u=user_id),
        provided_key)
    if b_key_valid in ['init', 'used']:
        return True
    else:
        print "------------------------------"
        print "KEY IS NOT REGISTERED!"
        print "provided key ", str(provided_key), "RETURNS", str(b_key_valid)
        return False

def user_is_online(user_id):
    b_user_online = redis_client('livechat').get(
                            '{u}_active_{u}_ctl_priv'.format(u=str(user_id)) )
    return b_user_online

def generate_chat_key(chat_id, salt):
    # make sure salt is a str before hashing it
    salt = str(salt)
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