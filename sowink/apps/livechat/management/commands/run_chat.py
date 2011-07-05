#HELP: see the readme in redis-py for documentation on the various python
#   implementations of redis commands
#
#TODO:
#   -When a user sends a ctl_chat_req, it should be sent as part of a json,
#       along with some unique identifier (maybe no?) so that the responder can
#       send a ctl_chat_accept along with the unique ident to the requester's
#       priv channel. The backend can check to see if this is a valid ident.
#       this way, a user won't be bothered by unsolicited ctl_chat_accept that
#       could still have permission to be published on their channel.
#   -I believe this can be changed to use only 1 socket per user, regardless of
#       how many open chat windows they have. Simply make the main loop do the
#       legwork of deciding which chat windows receive which messages. Most of
#       the code would need to be rewritten, but it might be worth it if we find
#       we're running out of sockets or some other stresses on the system.
#   -code cleanup (dbg, notes, etc)
#       -unify var names (user_id, etc) across run_chat, views, and livechat.js
#       -so many nested ifs and loops. consider putting stuff into functions
#   -make some terms more generic
#   -right now, validates each sent message by checking chatkey against redis
#       using verify_chat_key. Might be more efficient to use sessionid instead
#   -better presentation of connect message for when you connect (you connected)
#   -show green dot when connection becomes active
#   -raise error_occurred flags where appropriate
#   -replace dict_has_type with dict_has_required_keys
#   -instead of using a master_user_id variable, consider storing user_id with
#       session in redis and grabbing it that way
#   -make sure to unsubscribe after breaks. Find out best places for this
#   -decide whether to lpush or rpush chatter. Important for when we retrieve
#       chat history, as I'll likely use rpoplpush to restore the hist.
#   -push chatter onto redis as json formatted string
#   -get timestamps onto each message
#   -fix auto reconnect
#   -Check user's provided chat_key against what is stored in redis. Will be
#       more efficient this way.
#   -for control listener, I'll need to figure out how to handle when a user
#       changes their favorites while a control channel is open
#   -implement a check for users blocking other users
#   -enforce a maximum number of open chat windows
#   -change all messages to send data as JSON instead of str
#   -log timestamps with ALL JSON messages
#   -pull chat history when new window opens
#   -keep track of all volatile redis vars that we want purged at the end of a
#       a session. there's a volatiles_to_purge dict that should be put to use
#   -prevent chat flood (keep users from opening too many chats too frequently
#   -do test cases for the following:
#       -user enters bad credentials (chat_key, user_id, etc) on js side
#       -too many open windows
#       -failed connection terminations
#------------------------------------------------------------------------------
#FIXED Stuff (I think...):
#   -CRITICAL ISSUE: It keeps creating new socket instances!
#       <SocketIOServer fileno=3 address=0.0.0.0:3000>: Failed.
#       Traceback (most recent call last):
#         File ".../gevent/server.py", line 122, in _do_accept
#       error: [Errno 24] Too many open files
#   -!!!!!! MAKE USE OF io.session.session_id !!!!!!
#   -keep all tabs connected, possibly setting a max number open
#   -don't tell user that I connected every single time I open a new tab
#   -some sort of user_is_online() function needs to be implemented so that we
#       can send ctl_chat_fail if user tries to chat with offline target
#
#   -Store the session_id in redis when the connection is first established.
#   -redis publications are considered type:message, but they are different 
#       than type:message sent from user interface. Handle this.
#   -it takes longer to establish connection (1-2s) than before. Find out why.
#   -make sure each message from the user contains the keys needed to authorize
#       each message: user_id, target_id, chat_id, chat_key
#   -make sure user is who they say they are, mostly for display purposes.
#       consider putting their username into redis and checking against chat_key
#   -authorize all messages before sending them
#   -make sure all keys are present to prevent key errors
#   -handle disconnect errors that greenlet keeps giving (broken pipe)
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
#   -Store the session_id in redis when the connection is first established.
#   -handle when user opens chat in two different places (WENT WITH METHOD 1)
#       +method 1: store multiple valid chat keys that clear out on disconnect.
#           This will require moving chat_key storage into a new redis variable
#       -method 2: tell views.py to assign the same key to new windows if user
#           still has at least 1 chat window open for a given chat_id. This can
#           be accomplished by using redis increment on each open session and
#           decrement on close, and consider key valid as long as counter > 0


# Make blocking calls in socket lib non-blocking before anybody else grabs the
# socket lib:
from gevent import monkey
monkey.patch_all()

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.cache import cache
from django.core.management.base import NoArgsCommand
from django.http import HttpResponse, HttpResponseRedirect

from socketio import SocketIOServer
from livechat.views import redis_client, user_is_online, verify_chat_key
from gevent import Greenlet
import jingo
from redis import Redis
import simplejson as json

#dbg:
# import inspect
# global_debug_counter = 1
# session_io_list = list()
# last_socketio = None
#end dbg
#dbg:     import pdb; pdb.set_trace()

def indent(level):
    indents = ['\t' for i in range(level)]
    return ''.join(indents)

#NOTE: this can be absorbed into dict_has_required_keys by creating a definition
#   for 'type' and making sure the dict has a type field. Once this is done,
#   replace all refs to this.
def dict_has_type(d):
    if 'type' in d.keys():
        return True
    return False
    
#given a dict d, check if it has all the keys required for a given type
#NOTE: need to add definition for message (from redis version)
def dict_has_required_keys(d, type):    
    # type requirement definitions. dicts of a given type must have these keys
    reqs = dict()
    reqs['chatter'] = ['type','chat_id','user_id','target','chat_key','payload']
    reqs['joined'] = ['type', 'chat_id', 'user_id', 'target', 'chat_key']
    reqs['reconnect'] = reqs['joined']
    reqs['disconnect'] = reqs['joined']
    reqs['subscribe'] = ['pattern', 'type', 'channel', 'data'] # redis notice
    reqs['message'] = reqs['subscribe'] # redis message
    reqs['auth'] = ['type','chat_id','user_id','chat_key'] # general auth
    reqs['has_type'] = ['type'] # for checking if dict has a type field
    
    # control
    reqs['ctl_init'] = ['type', 'chat_id', 'user_id', 'chat_key']
    reqs['ctl_pub'] = ['type', 'chat_id', 'user_id', 'chat_key', 'payload']
    reqs['ctl_priv'] = reqs['ctl_pub']
    reqs['ctl_chat_req'] = ['type', 'chat_id', 'user_id', 'target', 'chat_key']

    #check if there is a definition for the passed type
    if type not in reqs:
        return False
    #check if the passed dict has all the fields required for it's claimed type
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
#     if last_socketio != environ['socketio'].__repr__():
#         print "a new socketio was created!"
#         print environ['socketio'].__repr__()
#     if environ['socketio'] not in session_io_list:
#         session_io_list.append(environ['socketio'].__repr__())
#     
#    print str(len(session_io_list)), "socketio objs created so far"
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
        django_response = chat_socketio(environ['socketio'])

        # TODO: Do something rather than this stubbed-in 200:
        start_response('200 ok', [])  # What about cookies? Need 'em?
        return []
    else:
        start_response('404 Not Found', [])
        return ['<h1>Not Found</h1>']


def chat_socketio(io):
    #dbg:
    print "chat_socketio begin!"
    #end dbg
    
    CHANNEL = 'world'
    master_user_id = None #needed for disconnect messages, though I suppose I
        #can grab it from redis if I store user_id with session_id.
    error_occurred = False

    #keep track of these so that they are only purged if they get set.
    volatiles_to_purge = dict()

    def subscriber(io):
        try:
            redis_in = redis_client('livechat')
            redis_in.subscribe(CHANNEL)
            print "subscribing to channel", CHANNEL
            redis_in_generator = redis_in.listen()
        
            # io.connected() never becomes false for some reason.
            while io.connected():
                #dbg:
                #print "in subscriber while io.connected() loop"
                #end dbg
                for from_redis in redis_in_generator:
                    print 'SESSION %s -- Incoming: %s' % (io.session.session_id,
                                                            from_redis)
                    
                    # make sure from_redis has a type before continuing
                    if not dict_has_type(from_redis):
                        print "\tfrom_redis has no 'type' field!"
                        break
                    
                    #NOTE: is there any danger of type being overwritten later?
                    type = str(from_redis['type'])

                    #NOTE: I no longer need this block.
                    # check if session is still valid. Also kill this greenlet
                    #   listener if session expired or just unsubscribe.
                    #NOTE: this shouldnt work without a chat_id, user_id...
                    #NOTE: I'll want to change this as soon as we allow multiple
                    #   simultaneous chat windows
#                     latest_session = redis_client('livechat').hget(
#                         '{u}_creds_{c}'.format(c=chat_id, u=user_id),
#                         'latest_session')
#                     if str(latest_session) != str(io.session.session_id):
#                         print "\tThis session is expired."
#                         io.send('your chat session has expired.')
#                         redis_client('livechat').unsubscribe()
#                         break

                    # verify it has the required fields for its alleged type
                    if not dict_has_required_keys( from_redis, type ):
                        print('\tfrom_redis is missing required fields for '
                                'type %s' % type)

                    # finally, send message when all is good
                    #NOTE: might need to modify this to handle different redis
                    #   message intents. Right now assumes all redis messages
                    #   are to be printed to user. True for actual chat, but for
                    #   ctls, it might want to do something else.
                    if type == 'message':
                        print "subscriber received a redis message"
                        io.send(from_redis['data'])
                        
                    #NOTE: here would be a good place to put an additional if
                    #   block to listen for subscription messages from redis
        finally:
            print "EXIT SUBSCRIBER %s" % io.session

    # print message when connection established. This point shoudld only be
    #   reached once. after that, it goes to main loop
    if io.on_connect():
        print "CONNECT %s" % io.session
    else:
        print "SOMETHING OTHER THAN CONNECT!" # Shouldn't, if code is healthy...

    #NOTE: -double check that all break statements are needed/in the right place
    #      -examine behavior of the error_occurred flag, and make sure they are
    #           where they need to be
    #TAG: joinloop (I refer to in dbg messages)
    for i in range(0, 20):
        print "in joinloop %i" % i
        recv = io.recv()
        if recv:            
            joinmsg = json.loads(recv[0])

            # make sure joinmsg has a type
            #NOTE: replace this with dict_has_required_keys
            if not dict_has_type(joinmsg):
                error_occurred = True
                print "joinloop received a typeless iorecv"
                print "joinmsg fields = ",joinmsg.keys()
                print "joinmsg vals = ",joinmsg.values()
                break

            #NOTE: is there any danger of type being overwritten later?    
            type = str(joinmsg['type'])
            
            # do a required_keys check for type before proceeding
            if not dict_has_required_keys(joinmsg, type):
                error_occurred = True
                print "joinloop: iorecv with missing fields for type %s" % type
                print "joinmsg fields = ",joinmsg.keys()
                print "joinmsg vals = ",joinmsg.values()
                break
            
            # validate user's chat key before continuing. Two step process:
            #   -make sure this recv has the fields needed for auth
            #   -verify_chat_key using said fields
            #NOTE: figure out what to tell the user when auth fails. When this
            #   routine was in the type check blocks, it would print context
            #   specific messages. Now it needs to raise a flag or something.
            #   if I do it that way, don't break on failed verify here. Let the
            #   type check blocks handle sending message and breaking.
            if not dict_has_required_keys(joinmsg, 'auth'):
                error_occurred = True
                print 'trying to do auth, but required fields were not passed'
                print "joinmsg fields = ",joinmsg.keys()
                print "joinmsg vals = ",joinmsg.values()
                break
            #Grab fields required to do auth
            chat_key = joinmsg['chat_key']
            user_id = joinmsg['user_id']
            chat_id = joinmsg['chat_id']
            if not verify_chat_key(chat_key, user_id, chat_id):
                error_occurred = True
                io.send('sorry, an error occurred. Try refreshing the page')
                print 'User\'s chat_key failed auth test'
                break

            #otherwise, continue with grabbing fields
            #NOTE: consider storing session and user_id in redis instead
            #NOTE: for control types, chat_id=ctl_chan
            master_user_id = user_id
            CHANNEL = chat_id
            username = redis_client('livechat').get(
                    'name_for_uid_{u}'.format(u=joinmsg['user_id']) )

            if type == 'joined' or type == 'reconnect':
                print "joinloop received a joined iorecv"
                print "joinmsg vals = ",joinmsg.values()
                                
                # register sessionid in redis along with users chat_key
                #NOTE: also store count of how many connections user has open
                #   on a given channel. That way, we only publish dis/connect
                #   messages if count = 0
                redis_client('livechat').set(
                    'session_{s}_key'.format(s=io.session.session_id),
                    chat_key)
                print 'registering session %s' % io.session.session_id
                redis_client('livechat').hset('{u}_keys_to_{c}'.format(
                    c=chat_id, u=user_id),
                    chat_key, "used")
                print 'marking key as used %s' % chat_key
                active_chats = redis_client('livechat').incr(
                    '{u}_active_{c}'.format(c=chat_id, u=user_id) )
                print '(open){u}_active_{c} count: {a}'.format(c=chat_id, u=user_id, a=active_chats)

                # spawn a listener for this instance:
                in_greenlet = Greenlet.spawn(subscriber, io)

                # publish connection notice
                #NOTE: fix so that it only publishes notice on first connection
                #   We don't want to know each time a chat window is opened up.
                if active_chats == 1:
                    redis_client('livechat').publish(
                        CHANNEL, '%s has joined' % username)
                    print 'publishing user join msg on %s' % CHANNEL
                break

            #handle controls here
            elif type == 'ctl_init':
                print "joinloop received a ctl_init iorecv"
                print "joinmsg vals = ",joinmsg.values()
                #NOTE: may or may not need to implement all the same session
                #   storing techniques that were used for 'joined'
                redis_client('livechat').set(
                    'session_{s}_key'.format(s=io.session.session_id),
                    chat_key)
                print 'registering ctl session %s' % io.session.session_id
                redis_client('livechat').hset('{u}_keys_to_{c}'.format(
                    c=chat_id, u=user_id),
                    chat_key, "used")
                print 'marking key as used %s' % chat_key
                active_ctls = redis_client('livechat').incr(
                    '{u}_active_{c}'.format(c=chat_id, u=user_id) )
                print '(open){u}_active_{c} count: {a}'.format(c=chat_id, u=user_id, a=active_ctls)

                # spawn a greenlet listener for your ctl_priv_in channel. This
                #   assumes that $chat_id is the name of your ctl_priv_in
                priv_greenlet = Greenlet.spawn(subscriber, io)
                                
                # grab list of fav ctl channels they want to listen to and spawn
                #   a greenlet subscriber for each. Then poll redis to find out
                #   which friends are currently online
                favorites = redis_client('livechat').hgetall(
                    '{u}_favorites'.format(u=user_id) )
                currently_online = list()
                fav_greenlet = dict()
                for fav, permission in favorites.items():
                    if permission == "allow":
                        CHANNEL = str(fav)+"_ctl_pub"
                        fav_greenlet[fav] = Greenlet.spawn(subscriber, io)
                        # who is already online?
                        if user_is_online(fav):
                            currently_online.append(fav)
                
                #NOTE: once favorites walk is done, publish the currently_online
                #   list to {u}_ctl_priv. Make sure there is something on client
                #   side to handle this type of message
                #   ALSO, store this, and other pub notices, as json
                redis_client('livechat').publish(
                    "{u}_ctl_priv".format(u=user_id), 
                    "currently online %s" % str(currently_online) )
                        
                # broadcast on your own control channel that you have connected
                #NOTE: should be some notice, not necessarily human readable
                if active_ctls == 1:
                    redis_client('livechat').publish(
                        "{u}_ctl_pub".format(u=user_id), "online")
                    print 'publish to {u}_ctl_pub: "online"'.format(u=user_id)
                break
            else:
                error_occurred = True
                print "joinloop got an unexpected joinmsg of type %s" % type
                print "joinmsg fields = ",joinmsg.keys()
                print "joinmsg vals = ",joinmsg.values()
                break
                
        if i == 20:
            error_occurred = True
            print "error occurred: i = 20"
    
    # Until the client disconnects, listen for input from the user:
    #TAG: mainloop
    while io.connected() and not error_occurred:
        #dbg:
        #print "in mainloop (while io.connected())"
        #end dbg
        
        recv = io.recv()
        if recv: #Always a list of 0 or 1 strings, I deduce from the source code
            to_redis = json.loads(recv[0])

            # make sure to_redis has a type
            if not dict_has_type(to_redis):
                error_occurred = True
                print "mainloop received a typeless iorecv!"
                print "to_redis fields = ",to_redis.keys()
                print "to_redis vals = ",to_redis.values()
                break

            # do a required_keys check for type before proceeding
            if not dict_has_required_keys(to_redis, to_redis['type']):
                error_occurred = True
                print "mainloop: iorecv with missing fields for type %s" % type
                print "to_redis fields = ",to_redis.keys()
                print "to_redis vals = ",to_redis.values()
                break

            # validate user's chat key before continuing. Two step process:
            #   -make sure this recv has the fields needed for auth
            #   -verify_chat_key using said fields
            #NOTE: figure out what to tell the user when auth fails. When this
            #   routine was in the type check blocks, it would print context
            #   specific messages. Now it needs to raise a flag or something.
            #   if I do it this way, don't break on failed verify here. Let the
            #   type check blocks handle sending message and breaking.
            if not dict_has_required_keys(to_redis, 'auth'):
                error_occurred = True
                print 'trying to do auth, but required fields were not passed'
                print "joinmsg fields = ",to_redis.keys()
                print "joinmsg vals = ",to_redis.values()
                break
            #Grab fields required to do auth
            chat_key = to_redis['chat_key']
            user_id = to_redis['user_id']
            chat_id = to_redis['chat_id']
            if not verify_chat_key(chat_key, user_id, chat_id):
                error_occurred = True
                io.send('sorry, an error occurred. Try refreshing the page')
                print 'User failed validation'
                break

            #otherwise, continue with grabbing fields
            #NOTE: consider storing session and user_id in redis instead
            master_user_id = user_id
            CHANNEL = chat_id
            username = redis_client('livechat').get(
                    'name_for_uid_{u}'.format(u=user_id) )

            #NOTE: what's the point of this block?
            if to_redis['type'] == 'reconnect':
                print "mainloop received a reconnect iorecv"
                print "to_redis vals = ",to_redis.values()
                payload = str(to_redis['payload'])
                
                #NOTE: if I raise a flag on bad user auth above, then handle
                #   printing context specific message to user and breaking here

#                 if not verify_chat_key(chat_key, user_id, chat_id):
#                     error_occurred = True
#                     io.send('Error joining chat. Try reloading the page.)')
#                     print('Error joining chat. '
#                     'Are you trying to break something? ;)')
#                     break
                    
            #NOTE: this looks like a good place to do a session check...
            
            elif to_redis['type'] == 'chatter':
                print "mainloop received a chatter iorecv"  
                print "to_redis vals = ",to_redis.values()
                payload = str(to_redis['payload'])
 
                #NOTE: if I raise a flag on bad user auth above, then handle
                #   printing context specific message to user and breaking here

#                 if not verify_chat_key(chat_key, user_id, chat_id):
#                     error_occurred = True
#                     io.send('sorry, your message was not sent.')
#                     print('sorry, your message was not sent.'
#                     'Are you trying to break something? ;)')
#                     break
                
                #NOTE: remember to make a timestamp as well
                # publish chatter and lpush
                print 'Channel::%s, Outgoing to Redis: %s' % (CHANNEL, to_redis)
                redis_client('livechat').publish(
                    CHANNEL, "{u}: {p}".format(u=username, p=payload) )
                #NOTE: Replace strings with JSON objects and store timestamps
                #   Also, consider storing user_id in case username ever changes
                #   in the future.
                redis_client('livechat').lpush(
                    'chat_id:{c}'.format(c=chat_id),
                    '{u}: {p}'.format(u=username, p=payload) )

            #NOTE: best way to handle ctl is to think of the auth step as just
            #   user verification. If they pass this, then they are indeed who 
            #   they claim to be. Allow them to listen to any favs ctl_pub chan
            #   and publish to any ctl_priv chan allowed for user
            elif to_redis['type'] == 'ctl_chat_req':
                print "mainloop received a ctl_chat_req iorecv"  
                print "to_redis vals = ",to_redis.values()
                target = str(to_redis['target'])
                
                # so if userA wants to send userB a message, they will send a 
                # ctl_priv type. One of the fields should be target:userB.
                # Auth verified that they are userA. Now we must check if UserB
                # is in their favorites. If so, publish chat request to userB's
                # B_priv_in channel
                                
                # verify that user can send chat requests to requested user
                #NOTE: Will have to also verify that the user is online. Might
                #   need to add a check before here to see if user online
                target_permission = str(redis_client('livechat').hget(
                    '{u}_favorites'.format(u=user_id), target))
                if target_permission == 'allow':
                    #NOTE: this is a good place to add a user online check.
                    if user_is_online(target):
                        # publish the chat request to target. It will show up 
                        # on their ctl_priv chan as redis data:"ctl_chat_req"
                        redis_client('livechat').publish('{t}_ctl_priv'.format(
                            t=target), 'ctl_chat_req')
                        print ("user is can chat with target. sending"
                                "ctl_chat_req to target's %s_ctl_priv" % target)
                    else:
                        #target offline. let user know it is not deny or reject
                        redis_client('livechat').publish('{u}_ctl_priv'.format(
                            u=user_id), 'ctl_chat_offline')
                        print ("target is offline. sending ctl_chat_offline"
                                "to user's %s_ctl_priv" % user_id)
                        
                elif target_permission in ['deny', None, 'None']:
                    # target blocked or is not even in their favorites.
                    # tell user they arent allowed to talk to their target
                    redis_client('livechat').publish('{u}_ctl_priv'.format(
                        u=user_id), 'ctl_chat_deny')
                    print "ctl_chat_deny sent to user on {u}_ctl_priv".format(
                        u=user_id)
                else:
                    # some special permission that isn't implemented yet
                    redis_client('livechat').publish('{u}_ctl_priv'.format(
                        u=user_id), 'ctl_chat_unkn')
                    print "permission %s not yet implemented" % target_permission
                    print "ctl_chat_unkn sent to user on {u}_ctl_priv".format(
                        u=user_id)
                    
                    
            else: #NOTE: should I raise an error? should I break here?
                error_occurred = True
                print "mainloop: unexpected recv of type %s" % to_redis['type']
                print "to_redis fields = ",to_redis.keys()
                print "to_redis vals = ",to_redis.values()
                break

    print "EXIT %s" % io.session

    if error_occurred:
        print "ERROR OCCURED!!!"

    # Clean up volatiles
    #NOTE: should probably purge $uid_creds_$chatid, name_for_uid_$uid
    #   Also, remove the key from list of valids
    #   Also, maybe I should just purge this after I have published all the
    #   messages I need, so that I don't have to grab from redis again...

    # Each time I close the 2nd chat window, wait for the old socketio() view
    # to exit, and then reopen the chat page, the number of Incomings increases
    # by one. The subscribers are never exiting. This fixes that behavior:
    try:
        in_greenlet.kill()
    except:
        print "final: no Greenlet to kill"

    
    #NOTE: if volatiles are cleaned up above, then I'll need to have grabbed the
    #   user_id and put it somewhere persistent. Consider using redis to store
    #   the user_id with the session_id ahead of time. Or better yet, wait till
    #   after this point to purge volatiles. yea, that's what I'll do.
    #   Also, don't forget to replace master_user_id below

    
    # remove key from this user's list of valid keys
    key_to_purge = redis_client('livechat').get('session_{s}_key'.format(s=io.session.session_id) )
    redis_client('livechat').hdel('{u}_keys_to_{c}'.format(u=master_user_id, c=CHANNEL), key_to_purge)
    print "removing key %s" % key_to_purge

    # remove session
    redis_client('livechat').delete('session_{s}_key'.format(s=io.session.session_id) )
    print "removing session %s" % io.session.session_id

    # decrement active chat counter
    #NOTE: make sure it only decr if count > 0. It should never be less than
    #   1 at this point, but just double check for rogue cases and report them
    active_chats = redis_client('livechat').decr(
        '{u}_active_{c}'.format(c=CHANNEL, u=master_user_id) )
    print '(close){u}_active_{c} count: {a}'.format(c=CHANNEL, u=master_user_id, a=active_chats)

    # publish disconnect msg if last remaining open chat for user in this room.
    # This should only happen when counter = 0
    if active_chats == 0:
        username = redis_client('livechat').get('name_for_uid_{u}'.format(u=master_user_id) )
        redis_client('livechat').publish(CHANNEL, '%s has disconnected' % username)
        #remove the variable entirely
        redis_client('livechat').delete('{u}_active_{c}'.format(c=CHANNEL, u=master_user_id) )
        print 'remove {u}_active_{c}'.format(c=CHANNEL, u=master_user_id)
        print "publishing disconnect message on channel %s" % CHANNEL
    
    return HttpResponse()


class Command(NoArgsCommand):
    help = 'Start the chat server.'

    def handle_noargs(self, *args, **kwargs):
        """Turn this process into the chat server."""
        print 'Listening on http://127.0.0.1:%s and on port 843 (flash policy server)' % settings.CHAT_PORT
        SocketIOServer(('', settings.CHAT_PORT), application, resource='socket.io', policy_server=True).serve_forever()
