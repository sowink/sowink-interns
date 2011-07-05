/* TODO: Figure out how to handle too many chat notifications. Guess this is
        dependent on ui implementation, but it might be a good idea to have a
        ctl_chat_busy that the js can send if there are too many notifications.
*/

    //preload the chat template
    var chatBoxTemplate = $('#chatBoxTemplate'),
    chatSessions = 0,
    chatBoxes = $('#chatBoxes');    

(function() {
    WEB_SOCKET_SWF_LOCATION = "http://localhost/media/swf/WebSocketMain.swf";
    var my_ctl_priv = $("#targetForm input[name=my_ctl_priv]").val();
    var user_id = $("#targetForm input[name=user]").val();
    var target_id = $("#targetForm input[name=target]");
    var chat_key = $("#targetForm input[name=key]").val();

    var ctl = new io.Socket(window.location.hostname, {
      port: 3000,
      rememberTransport: false,
      resource: 'socket.io'
    });
    ctl.connect();

    ctl.addEvent('connect', function() {
        ctl.send(JSON.stringify({'type': 'ctl_init', 'chat_id': my_ctl_priv, 'user_id': user_id, 'target': target_id.val(), 'chat_key': chat_key }));
    });
    
    ctl.addEvent('reconnect', function() {
        ctl.send(JSON.stringify({'type': 'ctl_init', 'chat_id': my_ctl_priv, 'user_id': user_id, 'target': target_id.val(), 'chat_key': chat_key }));
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
            console.log("someone wants to chat with you ;)");
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
    $('#targetForm').submit(function (event)
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
    //create new id for this chatBox
    var boxId = (chatSessions + 1);
    //clone it from template
    var chatBox = chatBoxTemplate.clone();
    //rename this chatBox instance by appending its boxId
    chatBox.attr('id', 'chatBox_'+boxId);
    //rename its child chatDialog
    chatBox.find('#chatDialog').attr('id', 'chatDialog_'+boxId);
    //rename it's child chatForm
    chatBox.find('#chatForm').attr('id', 'chatForm_'+boxId);
    //set value of the hidden target field
    target_id = $("#targetForm input[name=key]").val()
    chatBox.find('#chatForm').find('input[name=target]').val(target_id);
    //append this chatBox to the chatBoxes holder div
    chatBox.appendTo(chatBoxes);
    //make div visible
    chatBox.css("display","block")
    //get credentials from server
    requestCredentials(boxId);

    /* now comes the connection stuff. We'll need to populate these fields with
        the data received from our xhr posts */
//     var my_ctl_priv = $("#chatForm_"+boxId+" input[name=my_ctl_priv]").val();
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

function requestCredentials(boxId)
{
    // request chat credentials based on target
    var target_id = $("#chatform"+boxId+" input[name=target]").val();
    var chatboxURL = 'livechat/chatbox'

    $.ajax({
        type: 'POST',
        url: 'livechat/chatbox',
        data: target_id,
        success: checkCredentials,
        dataType: 'json'
    });
}        

function checkCredentials(data)
{
    console.log(data)
}
