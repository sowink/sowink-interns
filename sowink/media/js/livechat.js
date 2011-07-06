/* TODO: 
    -Figure out how to handle too many chat notifications. Guess this is
        dependent on ui implementation, but it might be a good idea to have a
        ctl_chat_busy that the js can send if there are too many notifications.
    -when a ctl_chat_req comes through, it should populate the needed fields for
        user to respond and open a chat. Make sure run_chat sends the following:
            -ctl_chat_req
            -who is requesting chat (user_id and username)
            -chat_id
            -request_id
        js should send the following back to run_chat:
            -ctl_chat_accept
            -user_id (grab it from the target-form)
            -chat_id (the one received above)
            -request_id     "
            -target_id (the user_id sent by the requester above)
        NOTE: if we use request_id properly on backend, we won't need to send
            chat_id and a lot of other fields.
    -Stop using IDs where they don't really need to be used.
*/
WEB_SOCKET_SWF_LOCATION = "/media/swf/WebSocketMain.swf"

//preload the chat template
var chatBoxTemplate = $('#chat-box-template'),
chatSessions = 0,
chatBoxes = $('#chat-boxes'),
chatObjects = new Array();
    
function chatFunctions()
{
    
}

//NOTE: the socket init stuff in this function is covered in initChatSocket.
//  use that instead of duplicating functionality here.
(function() {
    var my_ctl_priv = $("#target-form input[name=my-ctl-priv]").val();
    var user_id = $("#target-form input[name=user]").val();
    var target_id = $("#target-form input[name=target]");
    var chat_key = $("#target-form input[name=key]").val();

    var ctl = new io.Socket(window.location.hostname, {
      port: 3000,
      rememberTransport: false,
      resource: 'socket.io'
    });
    ctl.connect();

    ctl.addEvent('connect', function() {
        ctl.send(JSON.stringify({'type': 'ctl_init', 'chat_id': my_ctl_priv, 'user_id': user_id, 'chat_key': chat_key, 'target': target_id.val()}));
    });
    
    ctl.addEvent('reconnect', function() {
        ctl.send(JSON.stringify({'type': 'ctl_recon', 'chat_id': my_ctl_priv, 'user_id': user_id, 'target': target_id.val(), 'chat_key': chat_key }));
    });

    ctl.addEvent('disconnect', function() {
        ctl.send(JSON.stringify({'type': 'ctl_dconn', 'chat_id': my_ctl_priv, 'user_id': user_id, 'target': target_id.val(), 'chat_key': chat_key }));
    });

    /*NOTE: this should be modified to handle incomming messages. So if a user
        wants to chat, this message event should pop up a notification saying
        someone wants to chat. If a chat request fails, it should instruct
        the ui to tell user of failure. 
    ALSO: should handle chat reject (user) differently than chat deny (server)
    LASTLY: must implement a way to know which chat was allowed/denied, etc. it
        should be sent along with data when it is updated to send json vs str */
    ctl.addEvent('message', function(data)
    {
        //console.log(typeof data);
        if(data == "ctl_chat_accept")
        {
            console.log("your chat request was accepted");
            //call the function to open a new chat window
            chatboxjs();
        }
        else if(data == "ctl_chat_req")
        {
            /* NOTE: once data starts containing json say who wants to chat and 
                fill the notice hidden fields */
            console.log("someone wants to chat with you ;)");
            displayChatRequest()
        }
        else if(data == "ctl_chat_open")
        {
            /* NOTE: data should say who wants to chat, and javascript should
                open a chat window on this target's side */
            chatboxjs();
        }
        else if(data == "ctl_chat_deny")
        {
            console.log("your chat request was denied");
        }
        else if(data == "ctl_chat_reject")
        {
            console.log("your chat request was REJECTED!");
        }
        else if(data == "ctl_chat_offline")
        {
            console.log("sorry, that user is offline");
        }
        else
        {
            console.log("unknown ctl: " + data);
        }
    });
    
    /*  send chat request, and open chatbox when submit is clicked. Maybe should
        wait till after it receives a ctl message saying if it was successful
        before opening the window. */
    $('#target-form').submit(function (event)
    {
        event.preventDefault();
        /* first send the request. start some ui event that lets user know chat
           is still being negotiated. */
        if (target_id.val() !== '') {
            ctl.send(JSON.stringify({'type': 'ctl_chat_req', 'chat_id': my_ctl_priv, 'user_id': user_id, 'target': target_id.val(), 'chat_key': chat_key }));
        }
        $(this).trigger('ajaxComplete');
        return false;
    });
})();

function chatboxjs()
{
    /*NOTE: some of these fields are useless/redundant. Figure out which ones
        you really need*/
    /* create new id for this chat-box */
    var boxId = (chatSessions + 1);
    /* clone it from template */
    var chatBox = chatBoxTemplate.clone();
    /* rename this chatBox instance by appending its boxId */
    chatBox.attr('id', 'chat-box_'+boxId);
    /* set the chat-box's data.box-id */
    chatBox.data('box-id', boxId);
    /* rename its child chat-dialog */
    chatBox.find('#chat-dialog').attr('id', 'chat-dialog_'+boxId);
    /* rename its child chat-form */
    chatBox.find('#chat-form').attr('id', 'chat-form_'+boxId);
    /* rename its request-credentials */
    chatBox.find('#request-credentials').attr('id', 'request-credentials_'+boxId);
    /* set request-credentials's hidden boxId field */
    chatBox.find('#request-credentials_'+boxId).find('input[name=box-id]').val(boxId);
    /* set value of the hidden target fields */
    target_id = $("#target-form input[name=target]").val()
    chatBox.find('#chat-form').find('input[name=target]').val(target_id);
    chatBox.find('#request-credentials_'+boxId).find('input[name=target]').val(target_id);
    /* append the requestCredentials function to the form */
    chatBox.find('#request-credentials_'+boxId).submit(
        function(event){
            // request chat credentials based on target
            console.log('requesting creds');
            event.preventDefault();
            var form = $(this);
            var chatboxURL = 'livechat/chatbox'
        
            $.ajax({
                type: 'POST',
                url: chatboxURL,
                data: form.serialize(),
                success: checkCredentials,
                dataType: 'json'
            });
        }
    );

    /* append this chatBox to the chatBoxes holder div */
    chatBox.appendTo(chatBoxes);
    /* make div visible */
    chatBox.css("display","block");
    /* xhr get credentials from server */
    $('#request-credentials_'+boxId+'').submit();

    /* now comes the connection stuff. We'll need to populate these fields with
        the data received from our xhr posts */
//     var my_ctl_priv = $("#chatForm_"+boxId+" input[name=my-ctl-priv]").val();
//     var user_id = $("#chatForm_"+boxId+" input[name=user]").val();
//     var target_id = $("#chatForm_"+boxId+" input[name=target]").val();
//     var chat_key = $("#chatForm_"+boxId+" input[name=key]").val();
// 
//     chatSessions[boxId] = ''
//     var line = $('#targetForm [type=text]').val();
//     if (line !== '') {
//         $('#targetForm [type=text]').val('');
//         s.send(JSON.stringify({'type': 'ctl_chat_req', 'chat_id': my_ctl_priv, 'user_id': user_id, 'target': target_id, 'chat_key': chat_key, 'payload': line}));
//     }
//     $(this).trigger('ajaxComplete');
//     return false;
}

function requestCredentials(event)
{
}

function initChatObject(boxId)
{
    /*  NOTE: using objs until I implement a backbone js model
        NOTE: what are the consequences of a user breaking this by changing the
            ids of chat-forms? Can't be too careful with sockets
    */
    var chatObj = new Object;
    chatObj.boxId = boxId;
    chatObj.chat_id = $("#chat-form_"+boxId+" input[name=room]").val();
    chatObj.user_id = $("#chat-form_"+boxId+" input[name=user]").val();
    chatObj.target_id = $("#chat-form_"+boxId+" input[name=target]").val();
    chatObj.chat_key = $("#chat-form_"+boxId+" input[name=key]").val();
    
    chatObj.socket = new io.Socket(window.location.hostname,
    {
        port: 3000,
        transports: ['flashsocket','websocket'],
        rememberTransport: false,
        resource: 'socket.io'
    });
    chatObj.socket.connect();

    chatObj.socket.addEvent('connect', function() {
        chatObj.socket.send(
            JSON.stringify({
                'type': 'joined',
                'chat_id': chatObj.chat_id,
                'user_id': chatObj.user_id,
                'target': chatObj.target_id,
                'chat_key': chatObj.chat_key
            })
        );
    });

    chatObj.socket.addEvent('reconnect', function() {
        chatObj.socket.send(
            JSON.stringify({
                'type': 'reconnect',
                'chat_id': chatObj.chat_id,
                'user_id': chatObj.user_id,
                'target': chatObj.target_id,
                'chat_key': chatObj.chat_key
            })
        );
    });
    
    chatObj.socket.addEvent('disconnect', function() {
        chatObj.socket.send(
            JSON.stringify({
                'type': 'disconnect',
                'chat_id': chatObj.chat_id,
                'user_id': chatObj.user_id,
                'target': chatObj.target_id,
                'chat_key': chatObj.chat_key
            })
        );
    });

    chatObj.socket.addEvent('message', function(data) {
        var $chatBox = $("#chat-box_"+chatObj.boxId);
        $chatBox.append("<div>" + data + "</div>").scrollTop($chatBox[0].scrollHeight);
    });
    
    /* append submit handler */
    $('#chat-form_'+chatObj.boxId).submit( function(event) {
        chatObj
        console.log(chatObj);
        event.preventDefault();
        var line = $('#chat-form_'+chatObj.boxId+' [type=text]').val();
        if (line !== '') {
            $('#chat-form_'+chatObj.boxId+' [type=text]').val('');
            chatObj.socket.send(
                JSON.stringify
                ({
                    'type': 'chatter',
                    'chat_id': chatObj.chat_id,
                    'user_id': chatObj.user_id,
                    'target': chatObj.target_id,
                    'chat_key': chatObj.chat_key,
                    'payload': line
                })
            );
        }
        $(this).trigger('ajaxComplete');
    });

    /* Lastly store the chatSocket obj into the global array */
    //NOTE: Return the object and let the caller store into array if they want.
    //chatObjects[boxId] = chatObj;
    return chatObj
}
/*end initChatObject()*/

function checkCredentials(data)
{
    /*NOTE: don't forget to populate user, key, target*/
    var room    = data.chat_id;
    var user    = data.user_id;
    var key     = data.chat_key;
    var target  = data.target_id;
    var boxId   = data.box_id;

    $("#chat-form_"+boxId+" input[name=room]").val(room);
    $("#chat-form_"+boxId+" input[name=user]").val(user);
    $("#chat-form_"+boxId+" input[name=key]").val(key);
    $("#chat-form_"+boxId+" input[name=target]").val(target);
    
    chatObjects[boxId] = initChatObject(boxId);
    console.log(data);
    if(data.result=="success")
    {
        alert("success")
    }
}
