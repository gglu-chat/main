/*
    不用看啦我写得很烂q-q
*/
var ws_url = 'https://' + document.domain + ':' + location.port + '/room';
var socket = io.connect(ws_url);

let nick, onlineUsers, password, trip, md, myNick, myRoom;

// 初始化markdown引擎
md = new remarkable.Remarkable('full', {
    html: false,
	xhtmlOut: false,
	breaks: true,
	langPrefix: '',
	linkTarget: '_blank" rel="noreferrer',
	typographer:  true,
	quotes: `""''`
}).use(remarkable.linkify);

myNick = window.localStorage['nick_and_password']
// 当`?`后面有内容时(输入了房间名)弹出对话框
if (window.location.search != ''){
    nick = prompt('昵称：', myNick)
    if (nick.includes('#')){
        var well_index = nick.indexOf('#')
        password = nick.slice(well_index + 1)
        nick = nick.slice(0,well_index)
    }
    else{
        password = ''
    }
}

// 不带"?"的房间名
try{
    myRoom = (window.location.search.match(/^\?(.*)$/))[1]
}
catch(e){
    // `?`后面无内容时进入随机的8字母房间
    myRoom = getRandomString(8)
    window.location.assign('http://' + document.domain + ':' + location.port + '/room?' + myRoom)
}
document.title = `?${myRoom} - gglu聊天室`;

function getRandomString(length){
    var characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    var len = length;
    var str = '';
    for(var i = 0; i < len; i++){
        str += characters.charAt(Math.floor(Math.random() * characters.length))
    }
    return str
}

function insertAtCursor(text) {
	var input = document.getElementById('chatbox');
	var start = input.selectionStart || 0;
	var before = input.value.substr(0, start);
	var after = input.value.substr(start);

	before += text;
	input.value = before + after;
	input.selectionStart = input.selectionEnd = before.length;
}

trip = 'NOTRIP'
var msg_id = 'MSG_ID'
if (nick !== null && nick.match(/^[a-zA-Z0-9_]{1,12}$/)){
    socket.on('connected', function(){
            window.localStorage['nick_and_password'] = nick + '#' + password
            var users = document.getElementById('users')
            users.innerHTML = '';    
            // 向服务端发送join事件
            socket.emit('join', {"type": "join", "nick": nick, "password": password, "room": myRoom});
    });

    socket.on('joinchat', function(dt){
        if (dt.nick == nick){
            trip = dt.trip
            var recvbox = document.createElement('div');
            recvbox.classList.add('info')
            var chatarea = document.getElementById('chatarea')
            if (dt.onlineUsers.length == 0){
                recvbox.appendChild(document.createTextNode(`◆ 在线的用户：${nick}`));
            }
            else{
                recvbox.appendChild(document.createTextNode(`◆ 在线的用户：${dt.onlineUsers},${nick}`));
            }    
            chatarea.insertBefore(recvbox, brick)
            // 向在线列表中添加用户
            dt.onlineUsers.forEach(item => {
                var user = document.createElement('a');
                user.textContent = item;
    
                var userLi = document.createElement('li');
                userLi.appendChild(user);
                users.appendChild(userLi);
            });    
        }
        var recvbox = document.createElement('div');
        recvbox.classList.add('info')
        var chatarea = document.getElementById('chatarea')    
        recvbox.appendChild(document.createTextNode(`◆ ${dt.nick} 加入聊天室`));
        chatarea.insertBefore(recvbox, brick)
        var user = document.createElement('a');
        user.textContent = dt.nick;
        var userLi = document.createElement('li');
        userLi.appendChild(user);
        users.appendChild(userLi);


        document.getElementById("chatbox").onkeydown = function(event){
            event = event || window.event;
            // enter发送，shift+enter换行
            if (event.keyCode == 13 && !event.shiftKey){
                event.preventDefault();
                var txt = document.getElementById('chatbox').value;
                if (txt && typeof txt === 'string' && socket.connected){
                    // 向服务端发送message事件
                    socket.emit('message', {"type": "chat", "mytext": txt});
                    document.getElementById('chatbox').value = '';
                }
            
            }
        };

        // 给send事件注册处理程序
        socket.on('send', function(arg){
            var recvbox = document.createElement('div');
            recvbox.classList.add('message');
            // 昵称部分
            var nick_box = document.createElement('a');
            nick_box.classList.add('nick')
            nick_box.classList.add('hint--bottom-right')
            var date = new Date(arg.time)
            nick_box.setAttribute('aria-label', `trip:${arg.trip}\n${date.toLocaleString()}`)
            var your_nick = document.createTextNode(arg.mynick);
            nick_box.append(your_nick)
            //消息部分
            var text = document.createElement('div');
            text.innerHTML = md.render(arg.mytext)

            var chatarea = document.getElementById('chatarea');
            var brick = document.getElementById('brick');
            if (arg.msg_id != msg_id){
                recvbox.appendChild(nick_box);
                recvbox.appendChild(text);
                chatarea.insertBefore(recvbox, brick)
                // 每发一条消息，滚动条就滚动到底部
                chatarea.scrollTop = chatarea.scrollHeight
            }
            msg_id = arg.msg_id

            // `@someone`播放提示音
            if (arg.mytext.includes('@' + nick)){
                document.getElementById('notify').play();
            }

            // 点击昵称在输入框内插入`@someone`
            nick_box.onclick = function (e) {
                insertAtCursor(`@${e.target.innerHTML} `);
                document.getElementById('chatbox').focus();
            }

        })
    })

    // 给leavechat事件注册处理程序
    socket.on('leavechat', function(datas){
        var recvbox = document.createElement('div');
        recvbox.classList.add('info');
        var chatarea = document.getElementById('chatarea');   
        recvbox.appendChild(document.createTextNode(`◆ ${datas.nick} 退出聊天室`));
        chatarea.insertBefore(recvbox, brick);

        var users = document.getElementById('users')
        var children = users.children
        // 移除在线列表中离开的用户
        for (var i = 0; i < children.length; i++) {
            var user = children[i];
            if (user.textContent == datas.nick) {
                users.removeChild(user);
            }
        }
    })

    socket.on('foldmsg', function(arg){
        var nick_box = document.createElement('a');
        nick_box.classList.add('nick')
        nick_box.classList.add('hint--bottom-right')
        var date = new Date(arg.time)
        nick_box.setAttribute('aria-label', `trip:${arg.trip}\n${date.toLocaleString()}`)
        var your_nick = document.createTextNode(arg.mynick);
        nick_box.append(your_nick)

        var recvbox = document.createElement('div');
        recvbox.classList.add('message');
        var details = document.createElement('details');
        var summary = document.createElement('summary');
        summary.classList.add('foldmsg')
        summary.innerHTML = '点此展开长消息...'
        var text = document.createElement('div');
        text.innerHTML = md.render(arg.mytext);
        var chatarea = document.getElementById('chatarea');
        recvbox.appendChild(nick_box);
        details.appendChild(summary);
        details.appendChild(text);
        recvbox.appendChild(details);
        chatarea.insertBefore(recvbox, brick);
    })

    socket.on('warn', function(data){
        var recvbox = document.createElement('div');
        recvbox.classList.add('warn');
        var chatarea = document.getElementById('chatarea');   
        recvbox.appendChild(document.createTextNode(`◆ ${data.warn}`));
        chatarea.insertBefore(recvbox, brick);
    })
}
else{
    // 昵称为空或不满足昵称要求的断开连接
    socket.disconnect();
    var recvbox = document.createElement('div');
    recvbox.classList.add('warn');
    var chatarea = document.getElementById('chatarea');   
    recvbox.appendChild(document.createTextNode('◆ 昵称只能包含字母、数字以及下划线，且长度不超过12'));
    chatarea.insertBefore(recvbox, brick);
}
