(function() {
    WEB_SOCKET_SWF_LOCATION = "http://localhost/media/swf/WebSocketMain.swf"
    var chat_id = $("#chatform input[name=room]").val();
    var user_id = $("#chatform input[name=user]").val();
    var target_id = $("#chatform input[name=target]").val();
    var chat_key = $("#chatform input[name=key]").val();

    var s = new io.Socket(window.location.hostname, {
      port: 3000,
      rememberTransport: false,
      resource: 'socket.io'
    });
    s.connect();

    s.addEvent('connect', function() {
        s.send(JSON.stringify({'type': 'joined', 'chat_id': chat_id, 'user_id': user_id, 'target': target_id, 'chat_key': chat_key }));
    });
    
    s.addEvent('reconnect', function() {
        s.send(JSON.stringify({'type': 'reconnect', 'chat_id': chat_id, 'user_id': user_id, 'target': target_id, 'chat_key': chat_key }));
    });

//     s.addEvent('disconnect', function() {
//         s.send(JSON.stringify({'type': 'disconnect', 'chat_id': chat_id, 'user_id': user_id, 'target': target_id, 'chat_key': chat_key }));
//     });

    s.addEvent('message', function(data) {
        var $chatbox = $("#chatbox");
        $chatbox.append("<div>" + data + "</div>").scrollTop($chatbox[0].scrollHeight);
    });
    
    //send the message when submit is clicked
    $('#chatform').submit(function (evt) {
        var line = $('#chatform [type=text]').val();
        if (line !== '') {
            $('#chatform [type=text]').val('');
            s.send(JSON.stringify({'type': 'chatter', 'chat_id': chat_id, 'user_id': user_id, 'target': target_id, 'chat_key': chat_key, 'payload': line}));
        }
        $(this).trigger('ajaxComplete');
        return false;
    });
})();
