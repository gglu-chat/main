from ratelimiter2 import RateLimiter2 as rl2
from main import ALL_COMMANDS, sendWarn, whisper, listUsers, getUserSid, user_dict, disconnect, emit, getUserDetails, request, join_room, leave_room, getRoomUsers
import random

def handle_command(text, level, room):
    command = text.split(' ')[0]
    if command in ('/h', '/help'):
        sendWarn({"warn": ALL_COMMANDS})
    elif command in ('/w', '/whisper'):
        handle_whisper(text)
    elif command == '/kick' and level >= 3:
        handle_kick(text, level, room)
    elif command == '/ban' and level >= 3:
        handle_ban(text, level, room)
    elif command == '/unban' and level >= 3:
        handle_unban(text, room)
    elif command == '/move' and level >= 3:
        handle_move(text, level, room)
    elif command == '/listusers' and level >= 3:
        sendWarn({"warn": listUsers()})
    else:
        sendWarn({"warn": "请检查您的命令格式。发送`/help`查看所有命令。"})


def handle_whisper(text):
    target_user = text.split(' ')[1]
    wmsg = ' '.join(text.split(' ')[2:])
    try:
        whisper(target_user, wmsg)
    except:
        sendWarn({"warn": "请检查您的命令格式。"})

def handle_kick(text, level, room):
    try:
        target_nick = text.split(' ')[1]
        target_sid = getUserSid(target_nick, room)
        if level > user_dict[target_sid]['level']:
            disconnect(target_sid)
            emit('warn', {"warn": "已将 %s 断开连接。" %(target_nick)}, to=room)
    except:
        sendWarn({"warn": "请检查您的命令格式。"})

def handle_ban(text, level, room):
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
        sendWarn({"warn": "操作失败，可能是权限不足或目标不存在。"})

def handle_unban(text, room):
    try:
        unban_hash = text.split(' ')[1]
        rl2.pardon(unban_hash)
        emit('warn', {"warn": "已解除 %s 的封禁。" %(unban_hash)}, to=room)
    except:
        sendWarn({"warn": "请检查您的命令格式。"})

def handle_move(text, level, room):
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

