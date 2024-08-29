import random
import time
import json
from flask_socketio import emit, disconnect
from utils import check_message, getUserSid

def handleMsg(request, arg, user_dict, rl2):
    """"处理用户消息"""
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
            emit("warn", {"warn": "您已经被封禁。有任何疑问请联系管理员或站长。"})
            disconnect(request.sid)
    except:
        pass

    if rl2.frisk(iphash, text) or len(text) > 16384:
        emit("warn", {"warn": "您发送了太多消息，请稍后再试。"})

    elif (text.count(' ') + text.count('　') + text.count('\n') == len(text)):
        return

    # 聊天命令
    elif text[0] == '/':
        from commands import handle_command
        handle_command(text, level, room, user_dict, request, rl2)
    # 行数超过25行时折叠消息，否则正常发送
    elif rl2.lineCount(text) >= 25:
        emit('foldmsg', arg, to=room)
    else:
        emit('send', arg, to=room)

def handleWarning(request, data):
    """处理警告"""
    emit('warn', data, to=request.sid)

def handleWhisper(request, nick, text, user_dict):
    """处理私信"""
    arg = {"type": "whisper", "text": text, "from": user_dict[request.sid]['nick'], "to": nick}
    arg['time'] = int(round(time.time() * 1000))
    room = user_dict[request.sid]['room']
    emit('whisper', arg, to=getUserSid(nick, room, user_dict))
    emit('sendwmsg', arg, to=request.sid)

def handleInvite(request, data, user_dict, rl2):
    iphash = user_dict[request.sid]['hash']
    if rl2.search(iphash)['arrested']:
        emit("warn", {"warn": "您已经被封禁。有任何疑问请联系管理员或站长。"})
        disconnect(request.sid)
        return
    
    if rl2.frisk(iphash, '123456789012 邀请你去一个随机房间 ?abcdefgh'):
        emit("warn", {"warn": "您发送了太多邀请，请稍后再试。"})
        return
    
    data['time'] = int(round(time.time() * 1000))
    data['inviteRoom'] = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABSCEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(8))
    data['from'] = user_dict[request.sid]['nick']
    to_nick = data['to']
    room = user_dict[request.sid]['room']

    try:
        emit('invite', data, to=getUserSid(to_nick, room, user_dict))
        emit('sendinvite', data, to=request.sid)
        # 如果邀请的用户在该聊天室不存在，getUserSid会报错`user_id`在赋值前被引用
    except UnboundLocalError:
        emit("warn", {"warn": "请检查您的命令格式。"})
