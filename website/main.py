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
with open('static\\config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=yaml.CLoader)
    labels = config['labels']

# 存放sid，和sid对应的用户昵称和加入的房间
user_dict = {}

ipsalt = os.urandom(32)

rl = RateLimiter()

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
        if user_dict[i][1] == room:
            room_users.append(user_dict[i][0])
    return room_users

@socketio.on('connect', namespace='/room')
def connect():
    emit('connected', {'info': 'connected:D', 'sid': request.sid})

@socketio.on('disconnect', namespace='/room')
def disconnects():
    # 断开连接时触发leave事件
    leave(user_dict[request.sid][1])
    user_dict.pop(request.sid)

@socketio.on('leave', namespace='/room')
def leave(datas):
    room = user_dict[request.sid][1]
    emit('leavechat', {'type': 'leave', 'sid': request.sid, 'nick': user_dict[request.sid][0]}, to=room)
    leave_room(room)

@socketio.on('nick_taken', namespace='/room')
def nickTaken():
    emit('nickTaken', {"info": "昵称已被占用"})

@socketio.on('join', namespace='/room')
def join(dt):
    dt = json.loads(str(json.dumps(dt)))
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
    g.iphash = iphash

    # 检测该用户trip所属的标签并添加
    for k, v in labels.items():
        if trip in v:
            label = k
        else:
            label = 'user'

    # 检测昵称是否重复
    if dt['nick'] not in getRoomUsers(room):
        join_room(room)
        emit('joinchat', {"type": "join", "nick": dt['nick'], "trip": trip, "label": label, "room": room, "onlineUsers": getRoomUsers(room), "hash": iphash}, to=room)
    else:
        nickTaken()
        disconnect()
    nick_and_room = []
    nick_and_room.append(dt['nick'])
    nick_and_room.append(room)
    user_dict[request.sid] = nick_and_room
    # {'nBfbNBltuGT0DRmfAAAB': ['name', 'chat_room']}

@socketio.on('message', namespace='/room')
def handle_message(arg):
    arg = json.loads(str(json.dumps(arg)))
    arg['time'] = int(round(time.time() * 1000))
    arg['msg_id'] = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABSCEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(16))
    room = arg['room']
    # 判断消息是否满足频率限制
    score = len(arg['mytext'])
    if rl.frisk(request.sid, score) or len(arg['mytext']) > 16384:
        ratelimit()
    # 字数超过750或者行数超过25行时折叠消息
    elif len(arg['mytext']) >= 750 or arg['mytext'].count('\n') >= 25:
        emit('foldmsg', arg, to=room)
    else:
        emit('send', arg, to=room)

@socketio.on('ratelimit', namespace='/room')
def ratelimit():
    emit('ratelimit', {"info": "您发送了太多消息，请稍后再试"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 15264))
    socketio.run(app, host='0.0.0.0', port=port)