import json

def getRoomUsers(room, user_dict):
    """获取指定房间的用户"""
    room_users = []
    for i in user_dict:
        if user_dict[i]['room'] == room:
            room_users.append(user_dict[i]['nick'])
    return room_users

def getUserSid(nick, room, user_dict):
    """获取指定用户名的sid"""
    for i in user_dict:
        if user_dict[i]['nick'] == nick and user_dict[i]['room'] == room:
            user_sid = i
    return user_sid

def getUserDetails(nick, room, type, user_dict):
    """获取指定用户名的nick,trip,level,hash"""
    for i in user_dict:
        if user_dict[i]['nick'] == nick and user_dict[i]['room'] == room:
            return user_dict[i][type]

def listUsers(user_dict):
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
