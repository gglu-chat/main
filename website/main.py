from flask import Flask, render_template, request, flash
from flask_socketio import SocketIO, emit
import os
import json
import random
import hashlib
import base64
import time

app = Flask(__name__)
app.secret_key = 'haeFrbvHjyghragkhAEgRGRryureagAERVRAgef'
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)
salt = os.environ.get('SALT').encode()

user_dict = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@socketio.on('connect', namespace='/chat')
def connect(data):
    emit('connected', {'info': 'connected:D', 'sid': request.sid, 'onlineUsers': list(user_dict.values())})

@socketio.on('disconnect', namespace='/chat')
def disconnect():
    emit('leavechat', {'type': 'leave', 'sid': request.sid, 'nick': user_dict[request.sid]}, broadcast=True)
    #print(user_dict[request.sid], '断开连接')
    user_dict.pop(request.sid)

@socketio.on('join', namespace='/chat')
def join(dt):
    dt = json.loads(str(json.dumps(dt)))
    password = dt['password']
    sha256 = hashlib.sha256()
    sha256.update(password.encode() + salt)
    trip = base64.b64encode(sha256.digest()).decode('utf-8')[0:6]
    emit('joinchat', {"type": "join", "nick": dt['nick'], "trip": trip}, broadcast=True)
    user_dict[request.sid] = dt['nick']


@socketio.on('leave', namespace='/chat')
def leave(datas):
    disconnect()
    emit('leavechat', {'type': 'leave', 'sid': request.sid, 'nick': user_dict[request.sid]}, broadcast=True)


@socketio.on('message', namespace='/chat')
def handle_message(arg):
    arg = json.loads(str(json.dumps(arg)))
    arg['time'] = int(round(time.time() * 1000))
    arg['msg_id'] = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABSCEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(16))
    emit('send', arg, broadcast=True)
    #print(arg)


if __name__ == '__main__':
    #app.run(host="0.0.0.0",port=80)
    port = int(os.environ.get('PORT', 15264))
    #server = pywsgi.WSGIServer(("0.0.0.0", port), app)
    #server.serve_forever()
    socketio.run(app, host='0.0.0.0', port=port)