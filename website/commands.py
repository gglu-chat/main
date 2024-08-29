import random
from flask_socketio import emit, disconnect, join_room, leave_room
from utils import getUserSid, getUserDetails, getRoomUsers

ALL_COMMANDS = """**所有命令**：\n
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

def handle_command(text, level, room, user_dict, request, rl2):
    # 聊天命令
    if text[0] == '/':
        command = text.split(' ')[0]
        if command == '/h' or command == '/help':
            emit("warn", {"warn": ALL_COMMANDS})
        elif command == '/w' or command == '/whisper':
            target_user = text.split(' ')[1]
            wmsg = ' '.join(text.split(' ')[2:])
            from message_handling import handleWhisper
            try:
                handleWhisper(request, target_user, wmsg, user_dict)
            except:
                emit("warn", {"warn": "请检查您的命令格式。"})

        elif command == '/kick' and level >= 3:
            try:
                target_nick = text.split(' ')[1]
                target_sid = getUserSid(target_nick, room, user_dict)
                if level > user_dict[target_sid]['level']:
                    disconnect(target_sid)
                    emit('warn', {"warn": "已将 %s 断开连接。" %(target_nick)}, to=room)
            except:
                emit("warn", {"warn": "请检查您的命令格式。"})

        elif command == '/ban' and level >= 3:
            try:
                target_user = text.split(' ')[1]
                target_userid = getUserSid(target_user, room, user_dict)
                target_hash = getUserDetails(target_user, room, 'hash', user_dict)
                if level > user_dict[target_userid]['level']:
                    rl2.arrest(target_hash, target_hash)
                    emit('warn', {"warn": "%s 封禁了 %s ，用户哈希：%s" %(user_dict[request.sid]['nick'], target_user, target_hash)}, to=room)
                    emit('warn', {"warn": "您已经被封禁。有任何疑问请联系管理员或[站长](mailto://bujijam@qq.com/)"}, to=target_userid)
                    disconnect(target_userid)
            except:
                emit("warn", {"warn": "请检查您的命令格式。"})

        elif command == '/unban' and level >= 3:
            try:
                unban_hash = text.split(' ')[1]
                rl2.pardon(unban_hash)
                emit('warn', {"warn": "已解除 %s 的封禁。" %(unban_hash)}, to=room)
            except:
                emit("warn", {"warn": "请检查您的命令格式。"})

        elif command == '/move' and level >= 3:
            try:
                tg_nick = text.split(' ')[1]
                tg_sid = getUserSid(tg_nick, room, user_dict)
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
                    emit('joinchat', {"type": "join", "nick": tg_nick, "trip": user_dict[tg_sid]['trip'], "level": tg_level, "room": tg_room, "onlineUsers": getRoomUsers(tg_room, user_dict), "hash": user_dict[tg_sid]['hash'], "iskicked": "True"}, to=tg_room)
            except:
                emit("warn", {"warn": "请检查您的命令格式。"})