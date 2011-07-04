(function() {
    $(document).ready(function() {
        var room_name = $("#chatform input[name=room]").val();

        var s = new io.Socket(window.location.hostname, {
          port: 3000,
          rememberTransport: false,
          transports: ['websocket', 'xhr-multipart', 'xhr-polling'],
          resource: 'socket.io'
        });
        s.connect();

        s.addEvent('connect', function() {
            s.send(JSON.stringify({'type': 'joined', 'room': room_name, 'payload': $("#chatform input[name=nonce]").val()}));
        });
        
        s.addEvent('reconnect', function() {
            s.send(JSON.stringify({'type': 'joined', 'room': room_name, 'payload': $("#chatform input[name=nonce]").val()}));
        });

        s.addEvent('message', function(data) {
            var $chatbox = $("#chatbox");
            $chatbox.append("<div>" + data + "</div>").scrollTop($chatbox[0].scrollHeight);
        });
        
        //send the message when submit is clicked
        $('#chatform').submit(function (evt) {
            var line = $('#chatform [type=text]').val();
            if (line !== '') {
                $('#chatform [type=text]').val('');
                s.send(JSON.stringify({'type': 'message', 'chat_id': chat_id, 'payload': line}));
            }
            $(this).trigger('ajaxComplete');
            return false;
        });
    });
})();
