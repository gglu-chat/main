from flask import Flask, render_template, request
import os
from flask_socketio import SocketIO
from config import load_config
from user_management import handleUserConnect, handleUserDisconnect, handleUserJoin, handleUserLeave
from message_handling import *
from ratelimiter2 import RateLimiter2

app = Flask(__name__)
socketio = SocketIO(app, logger=True)

# 读取配置文件
config = load_config()
# 各等级所对应的trip
LEVELS = config['levels']

# 存放用户信息（nick,room,trip,level,hash）
user_dict = {}

rl2 = RateLimiter2()


@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/room')
def chat():
    return render_template('chat.html')


@socketio.on('connect', namespace='/room')
def connect():
    handleUserConnect(request)

@socketio.on('disconnect', namespace='/room')
def disconnects():
    handleUserDisconnect(request, user_dict)

@socketio.on('leave', namespace='/room')
def leave(datas):
    handleUserLeave(request, user_dict)

@socketio.on('join', namespace='/room')
def join(dt):
    handleUserJoin(request, dt, user_dict, rl2, config)

@socketio.on('message', namespace='/room')
def message(arg):
    handleMsg(request, arg, user_dict, rl2)

@socketio.on('warn', namespace='/room')
def warn(data):
    handleWarning(request, data)

@socketio.on('whisper', namespace='/room')
def whisper(nick, text):
    handleWhisper(request, nick, text, user_dict)

@socketio.on('invite', namespace='/room')
def invite(data):
    handleInvite(request, data, user_dict, rl2)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 15264))
    socketio.run(app, host='0.0.0.0', port=port)
