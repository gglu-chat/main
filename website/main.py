from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import os
import json
import random
import hashlib
import base64
import time
import yaml
from ratelimiter2 import RateLimiter2

app = Flask(__name__)
socketio = SocketIO(app, logger=True)
salt = os.environ.get('SALT').encode()

# 读取配置文件
with open('/app/website/static/config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=yaml.CLoader)
    # 各等级所对应的trip
    levels = config['levels']

# 存放用户信息（nick,room,trip,level,hash）
user_dict = {}

ipsalt = os.urandom(32)

rl2 = RateLimiter2()

all_commands = """**所有命令**：\n
|命令格式|说明|等级|
|:--------:|:----:|:----:|
|/help、/h|查看所有命令|1|
|/whisper <昵称> <文字>、    /w <昵称> <文字>|向目标用户私聊|1|
|/kick <昵称>|断开目标用户的连接|3|
|/ban <昵称>|封禁目标用户|3|
|/unban <哈希>|解除目标哈希的封禁|3|
|/move <昵称> <房间(可选)>|将用户移动到随机/指定的房间。|3|
|/listusers|列出全站所有用户|3|
***
其余帮助：[gglu聊天室帮助文档](https://bujijam.us.kg/docs/help-for-gglu)
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/room')
def chat():
    return render_template('chat.html')


def getRoomUsers(room):
    """获取指定房间的用户"""
    room_users = []
    for i in user_dict:
        if user_dict[i]['room'] == room:
            room_users.append(user_dict[i]['nick'])
    return room_users

def getUserSid(nick, room):
    """获取指定用户名的sid"""
    for i in user_dict:
        if user_dict[i]['nick'] == nick and user_dict[i]['room'] == room:
            user_sid = i
    return user_sid

def getUserDetails(nick, room, type):
    """获取指定用户名的nick,trip,level,hash"""
    for i in user_dict:
        if user_dict[i]['nick'] == nick and user_dict[i]['room'] == room:
            return user_dict[i][type]

def listusers():
    """列出所有房间的用户"""
    # 初始化一个字典，用于存储所有房间的用户信息
    room_users = {}

    # 遍历所有用户，将他们加入到相应的房间中
    for sid, user_info in user_dict.items():
        room = user_info['room']
        nick = user_info['nick']
        trip = user_info['trip']

        # 如果该房间还没有任何用户，将该房间初始化为空列表
        if room not in room_users:
            room_users[room] = []

        # 将该用户的信息添加到该房间的用户列表中
        user_str = '[%s]%s'%(trip, nick)
        room_users[room].append(user_str)

    # 构造一个字符串，用于表示所有房间的用户信息
    result_str = ''
    for room, users in room_users.items():
        user_str = ', '.join(users)
        result_str += '?%s: %s\n'%(room, user_str)

    return result_str

def check_message(msg):
    """检查消息是否安全"""
    try:
        data = json.loads(json.dumps(msg))
    # 解析失败就说明不是json
    except json.JSONDecodeError:
        return False
    if not isinstance(data, dict):
        return False
    # 消息内容必须为字符串
    if 'mytext' not in data or not isinstance(data['mytext'], str):
        return False
    return True


@socketio.on('connect', namespace='/room')
def connect():
    emit('connected', {'info': 'connected:D', 'sid': request.sid})

@socketio.on('disconnect', namespace='/room')
def disconnects():
    # 断开连接时触发leave事件
    leave(user_dict[request.sid]['room'])
    user_dict.pop(request.sid)

@socketio.on('leave', namespace='/room')
def leave(datas):
    room = user_dict[request.sid]['room']
    nick = user_dict[request.sid]['nick']
    _time = int(round(time.time() * 1000))
    emit('leavechat', {'type': 'leave', 'sid': request.sid, 'nick': nick, 'time': _time}, to=room)
    leave_room(room)

@socketio.on('join', namespace='/room')
def join(dt):
    dt = json.loads(str(json.dumps(dt)))
    nick = dt['nick']
    room = dt['room']
    password = dt['password']
    _time = int(round(time.time() * 1000))

    # 密码不为空时加密，为空时trip直接赋值'null'
    if password != '':
        sha256 = hashlib.sha256()
        sha256.update(password.encode() + salt)
        trip = base64.b64encode(sha256.digest()).decode('utf-8')[0:6]
    else:
        trip = 'null'

    # 通过xff头来获取ip并加密
    ip = (request.headers.getlist("X-Forwarded-For")[0]).split(',')[0]
    sha256 = hashlib.sha256()
    sha256.update(ip.encode() + ipsalt)
    iphash = base64.b64encode(sha256.digest()).decode('utf-8')[0:15]

    # 检测该用户trip所属的标签并添加，再添加相应的等级
    # Todo: trip为null的等级为0
    level = ''
    for k, v in levels.items():
        if trip in v:
            level = k
    if not level:
        level = 1
    
    # 检测昵称是否重复
    if (dt['nick'] not in getRoomUsers(room)) and (not rl2.frisk(iphash, '0')):
        join_room(room)
        emit('joinchat', {"type": "join", "nick": nick, "trip": trip, "level": level, "room": room, "onlineUsers": getRoomUsers(room), "hash": iphash, "time": _time}, to=room)
    else:
        if dt['nick'] in getRoomUsers(room):
            sendWarn({"warn": "昵称已被占用。"})
        elif rl2.frisk(iphash, '0'):
            sendWarn({"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)。"})
        disconnect()
    user_dict[request.sid] = {}
    user_dict[request.sid]['nick'] = nick
    user_dict[request.sid]['room'] = room
    user_dict[request.sid]['trip'] = trip
    user_dict[request.sid]['level'] = level
    user_dict[request.sid]['hash'] = iphash


@socketio.on('message', namespace='/room')
def handle_message(arg):
    if not check_message(arg):
        disconnect(request.sid)
        return

    arg = json.loads(str(json.dumps(arg)))
    arg['time'] = int(round(time.time() * 1000))
    arg['msg_id'] = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABSCEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(16))
    arg['room'] = user_dict[request.sid]['room']
    arg['level'] = user_dict[request.sid]['level']
    arg['mynick'] = user_dict[request.sid]['nick']
    arg['trip'] = user_dict[request.sid]['trip']
    text = arg['mytext']
    room = arg['room']
    level = arg['level']

    # 判断消息是否满足频率限制
    iphash = user_dict[request.sid]['hash']
    try:
        if rl2.search(iphash)['arrested']:
            sendWarn({"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)。"})
            disconnect(request.sid)
    except:
        pass
    if rl2.frisk(iphash, text) or len(text) > 16384:
        sendWarn({"warn": "您发送了太多消息，请稍后再试。"})

    elif(text.count(' ') + text.count('　') + text.count('\n') == len(text)):
        return

    # 聊天命令
    elif text[0] == '/':
        command = text.split(' ')[0]
        if command == '/h' or command == '/help':
            sendWarn({"warn": all_commands})
        elif command == '/w' or command == '/whisper':
            target_user = text.split(' ')[1]
            wmsg = ' '.join(text.split(' ')[2:])
            try:
                whisper(target_user, wmsg)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})

        elif command == '/kick' and level >= 3:
            try:
                target_nick = text.split(' ')[1]
                target_sid = getUserSid(target_nick, room)
                if level > user_dict[target_sid]['level']:
                    disconnect(target_sid)
                    emit('warn', {"warn": "已将 %s 断开连接。" %(target_nick)}, to=room)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})

        elif command == '/ban' and level >= 3:
            try:
                target_user = text.split(' ')[1]
                target_userid = getUserSid(target_user, room)
                target_hash = getUserDetails(target_user, room, 'hash')
                if level > user_dict[target_userid]['level']:
                    rl2.arrest(target_hash, target_hash)
                    emit('warn', {"warn": "%s 封禁了 %s ，用户哈希：%s" %(user_dict[request.sid]['nick'], target_user, target_hash)}, to=room)
                    emit('warn', {"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)"}, to=target_userid)
                    disconnect(target_userid)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})

        elif command == '/unban' and level >= 3:
            try:
                unban_hash = text.split(' ')[1]
                rl2.pardon(unban_hash)
                emit('warn', {"warn": "已解除 %s 的封禁。" %(unban_hash)}, to=room)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})

        elif command == '/move' and level >= 3:
            try:
                tg_nick = text.split(' ')[1]
                tg_sid = getUserSid(tg_nick, room)
                tg_level = user_dict[tg_sid]['level']
                if text.split(' ')[2:]:
                    tg_room = ' '.join(text.split(' ')[2:])
                else:
                    tg_room = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABSCEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(8))
                if level > tg_level:
                    leave_room(room, sid=tg_sid)
                    emit('leavechat', {'type': 'leave', 'sid': tg_nick, 'nick': tg_nick}, to=room)
                    emit('warn', {"warn": "已将 %s 移动到了 ?%s 聊天室。" %(tg_nick, tg_room)}, to=room)
                    join_room(tg_room, sid=tg_sid)
                    user_dict[tg_sid]['room'] = tg_room
                    emit('joinchat', {"type": "join", "nick": tg_nick, "trip": user_dict[tg_sid]['trip'], "level": tg_level, "room": tg_room, "onlineUsers": getRoomUsers(tg_room), "hash": user_dict[tg_sid]['hash'], "iskicked": "True"}, to=tg_room)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})

        elif command == '/listusers' and level >= 3:
            try:
                sendWarn({"warn": listusers()})
            except:
                sendWarn({"warn": "请检查您的命令格式。"})
        else:
            sendWarn({"warn": "请检查您的命令格式。发送`/help`查看所有命令。"})

    # 行数超过25行时折叠消息，否则正常发送
    elif rl2.lineCount(text) >= 25:
        emit('foldmsg', arg, to=room)
    else:
        emit('send', arg, to=room)

@socketio.on('warn', namespace='/room')
def sendWarn(data):
    emit('warn', data, to=request.sid)

@socketio.on('whisper', namespace='/room')
def whisper(nick, text):
    arg = {"type": "whisper", "text": text, "from": user_dict[request.sid]['nick'], "to": nick}
    arg['time'] = int(round(time.time() * 1000))
    room = user_dict[request.sid]['room']
    emit('whisper', arg, to=getUserSid(nick, room))
    emit('sendwmsg', arg, to=request.sid)

@socketio.on('invite', namespace='/room')
def handle_invite(data):
    iphash = user_dict[request.sid]['hash']
    try:
        if rl2.search(iphash)['arrested']:
            sendWarn({"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)。"})
            disconnect(request.sid)
    except:
        pass
    if rl2.frisk(iphash, '123456789012 邀请你去一个随机房间 ?abcdefgh'):
        sendWarn({"warn": "您发送了太多邀请，请稍后再试。"})
        return
    
    data['time'] = int(round(time.time() * 1000))
    data['inviteRoom'] = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABSCEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(8))
    data['from'] = user_dict[request.sid]['nick']
    to_nick = data['to']
    room = user_dict[request.sid]['room']

    try:
        emit('invite', data, to=getUserSid(to_nick, room))
        emit('sendinvite', data, to=request.sid)
        # 如果邀请的用户在该聊天室不存在，getUserSid会报错`user_id`在赋值前被引用
    except UnboundLocalError:
        sendWarn({"warn": "请检查您的命令格式。"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 15264))
    socketio.run(app, host='0.0.0.0', port=port)
