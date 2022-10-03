/*
    不用看啦我写得很烂q-q
*/
var ws_url = 'https://' + document.domain + ':' + location.port + '/chat';
var socket = io.connect(ws_url);

var nick = prompt('昵称：')
if (nick.includes('#')){
    var well_index = nick.indexOf('#')
    var password = nick.slice(well_index + 1)
    nick = nick.slice(0,well_index)
}
else{
    var password = ''
}

/*
var defaultColorScheme = 'fresh-green'
function setColorScheme(colorScheme){
    document.getElementById('colorscheme-link').href = '../static/color_scheme/' + colorScheme + '.css';
}
document.getElementById('colorscheme-selector').onchange = function(e){
    setColorScheme(e.target.value);
}
*/

var trip = 'NOTRIP'
var msg_id = 'MSG_ID'
if (nick !== null && nick.match(/^[a-zA-Z0-9_]{1,12}$/)){
    socket.on('connected', function(data){
        if (data.onlineUsers.indexOf(nick)===-1){
            socket.emit('join', {"type": "join", "nick": nick, "password": password});
            var recvbox = document.createElement('div');
            recvbox.classList.add('info')
            var chatarea = document.getElementById('chatarea')
            if (data.onlineUsers.length == 0){
                recvbox.appendChild(document.createTextNode('◆ 在线的用户：' + nick));
            }
            else{
                recvbox.appendChild(document.createTextNode('◆ 在线的用户：'+data.onlineUsers + ',' + nick));
            }    
            chatarea.insertBefore(recvbox, brick)
            socket.on('joinchat', function(dt){
                if (dt.nick == nick){
                    trip = dt.trip
                }
                var recvbox = document.createElement('div');
                recvbox.classList.add('info')
                var chatarea = document.getElementById('chatarea')    
                recvbox.appendChild(document.createTextNode('◆ ' + dt.nick + ' 加入聊天室'));
                chatarea.insertBefore(recvbox, brick)

                document.getElementById("chatbox").onkeydown = function(event){
                    event = event || window.event;
                    if (event.keyCode == 13 && !event.shiftKey){
                        event.preventDefault();
                        var txt = document.getElementById('chatbox').value;
                        if (txt != '' && txt != ' ' && socket.connected){
                            var ssid = socket.id;
                            socket.emit('message', {"mytext": txt, "myid": ssid, "mynick": nick, "trip": trip});
                            document.getElementById('chatbox').value = '';
                        }
                    
                    }
                };

                socket.on('send', function(arg){
                    var recvbox = document.createElement('div');
                    recvbox.classList.add('message');
                    // 昵称部分
                    var nick_box = document.createElement('a');
                    nick_box.classList.add('nick')
                    nick_box.classList.add('hint--bottom-right')
                    nick_box.setAttribute('aria-label', 'trip:' + arg.trip + '\n' + arg.time)
                    var your_nick = document.createTextNode(arg.mynick);
                    nick_box.append(your_nick)
                    //消息部分
                    var text = document.createTextNode(': ' + arg.mytext);

                    var chatarea = document.getElementById('chatarea');
                    var brick = document.getElementById('brick');
                    if (arg.msg_id != msg_id){
                        recvbox.appendChild(nick_box);
                        recvbox.appendChild(text);
                        chatarea.insertBefore(recvbox, brick)
                    }
                    msg_id = arg.msg_id

                })
            })
            socket.on('leavechat', function(datas){
                var recvbox = document.createElement('div');
                recvbox.classList.add('info');
                var chatarea = document.getElementById('chatarea');   
                recvbox.appendChild(document.createTextNode('◆ ' + datas.nick + ' 退出聊天室'));
                chatarea.insertBefore(recvbox, brick);
            
            })
        }
        else{
            socket.disconnect();
            alert('昵称已被占用')
        }
    });
}
else{
    socket.disconnect();
    alert('昵称只能包含字母、数字以及下划线，且长度不超过12');
}
