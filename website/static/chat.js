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
    socket.emit('handle_password', {"nick": nick, "password": password})
}
else{
    socket.emit('handle_password', {"nick": nick, "password": ""})
}


document.getElementById("chatbox").onkeydown = function(event){
    event = event || window.event;
    if (event.keyCode == 13 && !event.shiftKey){
        event.preventDefault();
        var txt = document.getElementById('chatbox').value;
        if (txt != '' && txt != ' ' && socket.connected){
            var ssid = socket.id;
            socket.emit('message', {"mytext": txt, "myid": ssid, "mynick": nick});
            document.getElementById('chatbox').value = '';
        }
    
    }
};
    /* 用按钮发送
   document.getElementById('send').onclick = function(ev){
    var txt = document.getElementById('chatbox').value;
    if (txt != '' && txt != ' '){
        socket.emit('message', txt)
    }
   }
   */

var defaultColorScheme = 'fresh-green'
function setColorScheme(colorScheme){
    document.getElementById('colorscheme-link').href = '../static/color_scheme/' + colorScheme + '.css';
}
document.getElementById('colorscheme-selector').onchange = function(e){
    setColorScheme(e.target.value);
}
   

if (nick !== null && nick.match(/^[a-zA-Z0-9_]{1,12}$/)){
    socket.on('connected', function(data){
        socket.emit('join', {"type": "join", "nick": nick});
        var recvbox = document.createElement('div');
        recvbox.classList.add('info')
        var chatarea = document.getElementById('chatarea')
        recvbox.appendChild(document.createTextNode('◆ 在线的用户：'+data.onlineUsers + ',' + nick));
        chatarea.insertBefore(recvbox, brick)
        socket.on('joinchat', function(dt){
            var recvbox = document.createElement('div');
            recvbox.classList.add('info')
            var chatarea = document.getElementById('chatarea')    
            recvbox.appendChild(document.createTextNode('◆ ' + dt.nick + ' 加入聊天室'));
            chatarea.insertBefore(recvbox, brick)
        })
        socket.on('addtrip', function(args){
            var trip = args.yourtrip
            socket.on('send', function(arg){
                var recvbox = document.createElement('div');
                var text = document.createTextNode(trip + ' ' + arg.mynick + '：' + arg.mytext);
                var chatarea = document.getElementById('chatarea')
                var brick = document.getElementById('brick')
                /*
                recvbox.appendChild(text);
                document.body.appendChild(recvbox);
                */
                recvbox.appendChild(text);
                chatarea.insertBefore(recvbox, brick)
                //document.getElementById('chatbox').value = ''
                window.scrollTo(0, document.body.scrollHeight)
            })
        })
        socket.on('leavechat', function(datas){
            var recvbox = document.createElement('div');
            recvbox.classList.add('info')
            var chatarea = document.getElementById('chatarea')    
            recvbox.appendChild(document.createTextNode('◆ ' + datas.nick + ' 退出聊天室'));
            chatarea.insertBefore(recvbox, brick)
        
        })
        
    });
}
else{
    socket.disconnect();
    alert('昵称只能包含字母、数字以及下划线，且长度不超过12');
}