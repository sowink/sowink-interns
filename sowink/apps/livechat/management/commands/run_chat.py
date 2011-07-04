#TODO:
#   -CRITICAL ISSUE: It keeps creating new socket instances!
#       <SocketIOServer fileno=3 address=0.0.0.0:3000>: Failed.
#       Traceback (most recent call last):
#         File ".../gevent/server.py", line 122, in _do_accept
#       error: [Errno 24] Too many open files
#
#   -unify var names (target_id, etc) across run_chat, views, and livechat.js
#   -make sure each message from the user contains the keys needed to authorize
#       each message: user_id, target_id, chat_id, chat_key
#   -make sure user is who they say they are, mostly for display purposes.
#       consider putting their username into redis and checking against chat_key
#   -make sure all keys are present to prevent key errors
#   -authorize all messages before sending them
#   -right now, validates each sent message by checking chatkey against redis
#       using verify_chat_key. Might be more efficient to use session id instead
#   -handle disconnect errors that greenlet keeps giving (broken pipe)
#   -handle when user opens chat in two different places
#
#   -right now, there is a greenlet listener and a seperate thing for sending
#       messages. If the greenlet listener drops, they can still send messages
#       but not receive them. For example, if they navigate away from the page 
#       and quickly go back, they will keep the same chat_key and it will still
#       be valid, since the chat key is instantiated when the chat page first
#       loads. This allows them to send messages before the listener finishes
#       reconnecting.
#
#       Alternately, if the user opens a new chat window, the old chat key will
#       become invalid, preventing the old chat window from sending messages.
#       but the greenlet listener is still connected, and will keep receiving
#       new messages.
#
#       This issue is mostly due to the lack of working disconnect events. For
#       some reason, disconnect messages are never sent, so I can't kill a
#       greenlet listener when a new window opens up.
#
#       Here are some possible solutions:
#           -keep the old chat key valid so that both windows can send and 
#               receive without issue.
#           -attach a chat key to the greenlet listener somehow, so that when
#               a key becomes invalid, the listener no longer publishes messages
#           -use session_id. I can probably put the session_id into redis and
#               check if the session_id is still valid each time greenlet tries
#               to publish notifications.
#           -find a way to kill the greenlet listener altogether. But I have no
#               idea how since disconnects are not being detected and I can't
#               catch the greenlet 'broken pipe' exceptions
#
#   -Store the session_id in redis when the connection is first established.
#   -redis publications are considered type: message, but they are different than
#       type: message sent from user interface. Handle this.
#   -it takes longer to establish connection (1-2s) than before. Find out why.

# Make blocking calls in socket lib non-blocking before anybody else grabs the
# socket lib:
from gevent import monkey
monkey.patch_all()

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.cache import cache
from django.core.management.base import NoArgsCommand

from socketio import SocketIOServer
from livechat.views import redis_client, check_user_valid, verify_chat_key
from gevent import Greenlet
import jingo
from redis import Redis
import simplejson as json

#dbg:
import inspect
global_debug_counter = 1
session_io_list = list()
last_socketio = None
#end dbg
#dbg:     import pdb; pdb.set_trace()

def indent(level):
    indents = ['\t' for i in range(level)]
    return ''.join(indents)
    
def authorize_msg_dest():
    pass

def dict_has_type(d):
    if 'type' in d.keys():
        return True
    return False
    
#given a dict d, check if it has all the keys required for a given type
def dict_has_required_keys(d, type):    
    # type requirements
    reqs = dict()
    reqs['message']=['type','chat_id','user_id','target','chat_key','payload']
    reqs['joined'] = ['type', 'chat_id', 'user_id', 'target', 'chat_key']

    #check if there is a definition for the passed type
    if type not in reqs:
        return False

    result = [field for field in reqs[type] if field in d]
    if result == reqs[type]:
        return True
    return False


def application(environ, start_response):
#dbg:
#     global last_socketio
#     global session_io_list
# 
#     #print "DEBUG run_chat.py:: environ = ", str(environ)
#     
#     if last_socketio is None:
#         last_socketio = environ['socketio'].__repr__()
#         
#     if last_socketio is not environ['socketio'].__repr__():
#         print "a new socketio was created for some reason!"
#         print environ['socketio'].__repr__()
#     if environ['socketio'] not in session_io_list:
#         session_io_list.append(environ['socketio'].__repr__())
#     
#     print str(len(session_io_list)), "socketio objs created so far"
#     
#     #print call stack
#     for idx, caller in enumerate(inspect.stack()):
#         print ''.join([ indent(idx), str(idx), ": ", caller[3] ])
#     
#     
#     global global_debug_counter
#     global_debug_counter += 1
#     print "global", global_debug_counter
#end dbg

    path = environ['PATH_INFO'].strip('/')

    if path.startswith('socket.io'):
        #dbg: print inspect.getmembers(environ['socketio'])    
        django_response = chat_socketio(environ['socketio'])

        # TODO: Do something rather than this stubbed-in 200:
        start_response('200 ok', [])  # What about cookies? Need 'em?
        return []
    else:
        start_response('404 Not Found', [])
        return ['<h1>Not Found</h1>']


def chat_socketio(io):
    #dbg: print session each chat_socketio call (apparently once per server hit)
    print "chat_socketio:", io.session
    #end dbg
    
    CHANNEL = 'world'
    error_occurred = False

    def subscriber(io):
        try:
            redis_in = redis_client('livechat')
            print "subscribing to channel", CHANNEL
            redis_in.subscribe(CHANNEL)
            redis_in_generator = redis_in.listen()
        
            # io.connected() never becomes false for some reason.
            while io.connected():
                print "subscriber ioconnected loop"
                for from_redis in redis_in_generator:
                    print 'SESSION %s -- Incoming: %s' % (io.session.session_id,
                                                            from_redis)
                    
                    # make sure from_redis has a type before continuing
                    if not dict_has_type(from_redis):
                        print "\tfrom_redis has no 'type' field!"
                        break

                    # check if session is still valid. Also kill this greenlet
                    #   listener if session expired.
                    # NOTE: remember to kill the listener!
                    latest_session = redis_client('livechat').hget(
                        '{u}_creds_{c}'.format(c=chat_id, u=user_id),
                        'latest_session')
                    if str(latest_session) != str(io.session.session_id):
                        print "\tThis session is expired."
                        #NOTE: tell user this chat window is no longer active,
                        #   then kill the listener
                        break

                    # verify it has the required fields for whatever type it is
                    #   claiming to be
                    if not dict_has_required_keys( from_redis,
                    from_redis['type'] ):
                        print('\tfrom_redis is missing required fields for '
                                'type %s' % from_redis['type'])

                    # finally, send message when all is good
                    if from_redis['type'] == 'message':
                        io.send(from_redis['data'])
        finally:
            print "EXIT SUBSCRIBER %s" % io.session

    #print message when first connection established
    if io.on_connect():
        print "CONNECT %s" % io.session
    else: 
        # I'll assume this is just a regular server hit but make sure to stress
        #   test it, as it might be creating a new iosocket instance on each hit
        pass
        #dbg: message = io.recv()
        #dbg: print "io.recv %s" % message

    #TAG: rangeloop (I refer to in dbg messages)
    #TODO: double check that all break statements are needed/in the right place
    for i in range(0, 20):
        recv = io.recv()
        if recv:
            recv_json = json.loads(recv[0])

            # make sure recv_json has a type
            if not dict_has_type(recv_json):
                print "rangeloop received a typeless iorecv"
                break
            
            # do a required_keys check for type before proceeding
            if not dict_has_required_keys(recv_json, recv_json['type']):
                print ("rangeloop received a " + str(recv_json['type']) + 
                        " type iorecv, but was missing fields for that type!")
                break
                
            #NOTE: might be worth putting a user validation check here before
            #   proceeding to next steps
            
            if recv_json['type'] == 'joined':
                print "rangeloop received a joined iorecv"
                print "recv_json fields = ",recv_json.keys()
                print "recv_json vals = ",recv_json.values()
                
                chat_key = recv_json['chat_key']
                user_id = recv_json['user_id']
                chat_id = recv_json['chat_id']
                

                #verify chat key
                if not verify_chat_key(chat_key, user_id, chat_id):
                    error_occurred = True
                    io.send('Error joining chat. Try reloading the page.)')
                    print('Error joining chat. '
                    'Are you trying to break something? ;)')
                    break

                # register session_id in redis under this users chat creds hash
                redis_client('livechat').hset(
                    '{u}_creds_{c}'.format(c=chat_id, u=user_id),
                    'latest_session',
                    io.session.session_id)

                # get channel
                CHANNEL = recv_json['chat_id']
                # spawn a listener for this CHANNEL:
                in_greenlet = Greenlet.spawn(subscriber, io)

                # get username from redis and publish connection notice
                username = redis_client('livechat').get(
                    'name_for_uid_{u}'.format(u=recv_json['user_id']) )
                redis_client('livechat').publish(
                    CHANNEL,
                    '%s has joined' % username)
                break
                
            elif recv_json['type'] == 'message':
                print "rangeloop received a message iorecv"                
                print "recv_json fields = ",recv_json.keys()
                print "recv_json vals = ",recv_json.values()
 
                chat_key = str(recv_json['chat_key'])
                user_id = str(recv_json['user_id'])
                CHANNEL = chat_id = str(recv_json['chat_id'])
                payload = str(recv_json['payload'])
 
                #verify chat key
                if not verify_chat_key(chat_key, user_id, chat_id):
                    error_occurred = True
                    io.send('sorry, your message was not sent.')
                    print('sorry, your message was not sent.'
                    'Are you trying to break something? ;)')
                    break
                
                # get username from redis and publish connection notice
                username = str( redis_client('livechat').get(
                    'name_for_uid_{u}'.format(u=user_id) ) )                   
                print "publishing to channel %s" % CHANNEL
                redis_client('livechat').publish(
                    CHANNEL,
                    "%s: %s" % (username, payload) )
                break
            else:
                print "rangeloop received an unanticipated iorecv"
                break
                
        if i == 20:
            error_occurred = True
            print "error occurred: i = 20"
        
    #dbg: check if io is connected still
#     if io.connected():
#         print "still connected"
#     else:
#         print "no longer connected"
    #end dbg

    #NOTE: doesn't seem to ever get to this point after io.on_connect() happens

    # Until the client disconnects, listen for input from the user:
    while io.connected() and not error_occurred:
        #dbg:
        print "\tother ioconnected loop"
        #end dbg
        
        message = io.recv()
        if message:  # Always a list of 0 or 1 strings, I deduce from the source code
            print "io.recv (other ioconnected) %s" % message            
            to_redis = json.loads(message[0])
            # On the chance that a user disconnects (loss of internet) and socketio
            # autoreconnects, a new session_id is given. However, the nonce is still
            # the same since the page hasn't been reloaded. There's a slim case where
            # getting the username via nonce fails (expired), so the username defaults
            # to the session ID, at the moment.
            # TODO: In the above case, XHR request a new nonce and update?
            # TODO: Replace flat strings with JSON objects (etc). 
            if to_redis['type'] == 'joined':  # Runs on reconnect
                #this used to take to_redis['payload'] (aka nonce)
                #if map_sid_to_nick(to_redis['payload'], io.session.session_id) is False:
                #    io.send('You have been disconnected for inactivity. Please refresh the page.')
                #    break
                if not verify_chat_key(joinmsg['chat_key'], 
                joinmsg['user_id'], joinmsg['chat_id']):
                    io.send('Error joining chat. '
                    'Are you trying to break something? ;)')                    
            else:
                print 'Outgoing: %s' % to_redis
                redis_client('livechat').publish(CHANNEL, "USERIDPLACEHOLDER" + ': ' + to_redis['payload'])

    print "EXIT %s" % io.session

    if error_occurred:
        print "ERROR OCCURED!!!"

    # Clean up cache.
    #redis_client('livechat').delete(io.session.session_id)

    # Each time I close the 2nd chat window, wait for the old socketio() view
    # to exit, and then reopen the chat page, the number of Incomings increases
    # by one. The subscribers are never exiting. This fixes that behavior:
    in_greenlet.kill()

    redis_client('livechat').publish(CHANNEL, "USERIDPLACEHOLDER" + ' has disconnected')

    return HttpResponse()


class Command(NoArgsCommand):
    help = 'Start the chat server.'

    def handle_noargs(self, *args, **kwargs):
        """Turn this process into the chat server."""
        print 'Listening on http://127.0.0.1:%s and on port 843 (flash policy server)' % settings.CHAT_PORT
        SocketIOServer(('', settings.CHAT_PORT), application, resource='socket.io', policy_server=False).serve_forever()
