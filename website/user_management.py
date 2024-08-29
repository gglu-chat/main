import time
import hashlib
import base64
from flask_socketio import emit, join_room, leave_room, disconnect
from utils import getRoomUsers, getUserSid
import json, os

SALT = os.environ.get('SALT').encode()
IPSALT = os.urandom(32)

def handleUserConnect(request):
    """处理用户连接"""
    emit('connected', {'info': 'connected:D', 'sid': request.sid})

def handleUserDisconnect(request, user_dict):
    """处理用户断开连接"""
    if request.sid in user_dict:
        # 断开连接时触发leave事件
        handleUserLeave(request, user_dict)
        user_dict.pop(request.sid)

def handleUserLeave(request, user_dict):
    room = user_dict[request.sid]['room']
    nick = user_dict[request.sid]['nick']
    _time = int(round(time.time() * 1000))
    emit('leavechat', {'type': 'leave', 'sid': request.sid, 'nick': nick, 'time': _time}, to=room)
    leave_room(room)

def handleUserJoin(request, dt, user_dict, rl2, config):
    dt = json.loads(str(json.dumps(dt)))
    nick = dt['nick']
    room = dt['room']
    password = dt['password']
    _time = int(round(time.time() * 1000))

    trip = createTrip(password)

    # 通过xff头来获取ip并加密
    ip = (request.headers.getlist("X-Forwarded-For")[0]).split(',')[0]
    iphash = hashIP(ip)

    # 检测该用户trip所属的标签并添加，再添加相应的等级
    # Todo: trip为null的等级为0
    level = getUserLevel(trip, config)
    
    # 检测昵称是否重复
    if (nick not in getRoomUsers(room, user_dict)) and (not rl2.frisk(iphash, '0')):
        join_room(room)
        emit('joinchat', {"type": "join", "nick": nick, "trip": trip, "level": level, "room": room, "onlineUsers": getRoomUsers(room, user_dict), "hash": iphash, "time": _time}, to=room)
    else:
        handleJoinError(nick, room, user_dict, rl2, iphash)
    user_dict[request.sid] = {"nick": nick, "room": room, "trip": trip, "level": level, "hash": iphash}


def createTrip(password):
    """密码不为空时加密，否则返回null"""
    if password:
        sha256 = hashlib.sha256()
        sha256.update(password.encode() + SALT)
        return base64.b64encode(sha256.digest()).decode('utf-8')[0:6]
    return 'null'

def hashIP(ip):
    sha256 = hashlib.sha256()
    sha256.update(ip.encode() + IPSALT)
    return base64.b64encode(sha256.digest()).decode('utf-8')[0:15]

def getUserLevel(trip, config):
    """获取用户等级"""
    for level, trips in config['levels'].items():
        if trip in trips:
            return level
    return 1    

def handleJoinError(nick, room, user_dict, rl2, iphash):
    """处理加入房间时的错误情况"""
    if nick in getRoomUsers(room, user_dict):
        emit('warn', {"warn": "昵称已被占用。"})
    elif rl2.frisk(iphash, '0'):
        emit('warn', {"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)。"})
    disconnect()