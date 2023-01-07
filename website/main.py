from flask import Flask, render_template, request, g
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import os
import json
import random
import hashlib
import base64
import time
import yaml
from ratelimiter import RateLimiter

app = Flask(__name__)
app.secret_key = 'haeFrbvHjyghragkhAEgRGRryureagAERVRAgef'
app.config['SECRET_KEY'] = 'secret!'
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

rl = RateLimiter()

all_commands = """**所有命令**：\n
|命令格式|说明|等级|
|:--------:|:----:|:----:|
|/help、/h|查看所有命令|1|
|/whisper <昵称> <文字>、    /w <昵称> <文字>|向目标用户私聊|1|
|/kick <昵称>|断开目标用户的连接|3|
|/ban <昵称>|封禁目标用户|3|
|/unban <哈希>|解除目标哈希的封禁|3|
|/move <昵称> <房间(可选)>|将用户移动到随机/指定的房间。|3|
"""

@app.route('/')
def index():
    return render_template('index.html')

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
    emit('leavechat', {'type': 'leave', 'sid': request.sid, 'nick': nick}, to=room)
    leave_room(room)

@socketio.on('join', namespace='/room')
def join(dt):
    dt = json.loads(str(json.dumps(dt)))
    nick = dt['nick']
    room = dt['room']
    password = dt['password']
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
    level = ''
    for k, v in levels.items():
        if trip in v:
            level = k
    if not level:
        level = 1
    
    # 检测昵称是否重复
    if (dt['nick'] not in getRoomUsers(room)) and (not rl.frisk(iphash, 0)):
        join_room(room)
        emit('joinchat', {"type": "join", "nick": nick, "trip": trip, "level": level, "room": room, "onlineUsers": getRoomUsers(room), "hash": iphash}, to=room)
    else:
        if dt['nick'] in getRoomUsers(room):
            sendWarn({"warn": "昵称已被占用"})
        elif rl.frisk(iphash, 0):
            sendWarn({"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)"})
        disconnect()
    user_dict[request.sid] = {}
    user_dict[request.sid]['nick'] = nick
    user_dict[request.sid]['room'] = room
    user_dict[request.sid]['trip'] = trip
    user_dict[request.sid]['level'] = level
    user_dict[request.sid]['hash'] = iphash

@socketio.on('message', namespace='/room')
def handle_message(arg):
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
    score = len(text)
    if rl.frisk(iphash, score) or len(text) > 16384:
        sendWarn({"warn": "您发送了太多消息，请稍后再试"})
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
                sendWarn({"warn": "请检查您的命令格式"})
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
                    rl.arrest(target_hash, target_hash)
                    emit('warn', {"warn": "%s封禁了%s，用户哈希：%s" %(user_dict[request.sid]['nick'], target_user, target_hash)}, to=room)
                    emit('warn', {"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)"}, to=target_userid)
                    disconnect(target_userid)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})
        elif command == '/unban' and level >= 3:
            try:
                unban_hash = text.split(' ')[1]
                rl.pardon(unban_hash)
                emit('warn', {"warn": "已解除 %s 的封禁" %(unban_hash)}, to=room)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})
        elif command == '/move' and level >= 3:
            try:
                tg_nick = text.split(' ')[1]
                tg_sid = getUserSid(tg_nick, room)
                if text.split(' ')[2:]:
                    tg_room = ' '.join(text.split(' ')[2:])
                else:
                    tg_room = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABSCEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(8))
                if level > user_dict[tg_sid]['level']:
                    leave_room(room, sid=tg_sid)
                    emit('warn', {"warn": "已将 %s 移动到了 %s 聊天室" %(tg_nick, tg_room)}, to=room)
                    join_room(tg_room, sid=tg_sid)
            except:
                sendWarn({"warn": "请检查您的命令格式。"})
    # 字数超过750或者行数超过25行时折叠消息，否则正常发送
    elif len(text) >= 750 or text.count('\n') >= 25:
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 15264))
    socketio.run(app, host='0.0.0.0', port=port)