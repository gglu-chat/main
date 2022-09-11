from flask import Flask, render_template, request, flash
from flask_socketio import SocketIO, emit
import os
import json
import random
import hashlib
import base64

app = Flask(__name__)
app.secret_key = 'haeFrbvHjyghragkhAEgRGRryureagAERVRAgef'
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)
salt = b"\x02\x88\xd6\x85\x02z\xbcS\xc2\xb10\x03\xa4n\xecl\x9e\x1f\xd5\xf4\xd4c\xd9\xc7\xc0\x92\xd5\x8a\xfe\x9b\xabT\xbe\xe53\xbdj\x95\xe6\x8a'=\x9c\x028\xee\x1eG\xaf\xd6\xdf\x9bp\xd9\x94\xd2X\x18\x0f\x92WQ\x1b\xdd\xec\x7fa\x8a\xb1b\x84\xea\xbe\xf7.\xb2>,\x14\xbb-\xe3M\x85\x0c\xa0HBY\xfa\xf0ll\x92\xbb]\xd4\xee\xa7\x11\xb1\xce\xa0\xab\xc9|D\xabf\xa8jP\xfb\xe7d\xa76\x9a7jBZ*\x1a\xe5\xda\xe4\xb6Ssl?\xb7\xe3\xb8P\nP\x1fq\xe4\xae\xcb]\xd4\x1f6\xe5\xdc\xd2\x03B\x1d\x97*l\n^A\xc3V\x82\r`{\xf1\xc8>\xb4g6\xbe|B&)>\xc6\x7f\xbb0\xf5\xf1\xd5\x83\x7f\x9a\x85jv\xb2J\xdf+\x94\x9f\x944m0\xba3\xf5\xbc>:\x89\xf193\xda\x0f\x10h(0F\xabxw7\x89\x8a\xbd\xff\xc6E\xf1\x9f\x1a4>\x1a\xaeJ\x80\x9b\x14<\x1a\xda\x11\xc5\x1d-\xcar:\x1e)\xa7\xcf\xb1M'8"

user_dict = {}

@app.route('/')
def index():
    return "hello world"

@app.route('/random', methods=['POST', 'GET'])
def randomkit():
    r = None
    if request.method == 'POST':
        try:
            aa = int(request.form['a'])
            bb = int(request.form['b'])
            r = random.randint(aa, bb)
        except ValueError:
            flash('请输入正确格式的数字！')
    return render_template('random.html', r = r)

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
    emit('joinchat', dt, broadcast=True)
    user_dict[request.sid] = dt['nick']


@socketio.on('leave', namespace='/chat')
def leave(datas):
    disconnect()
    emit('leavechat', {'type': 'leave', 'sid': request.sid, 'nick': user_dict[request.sid]}, broadcast=True)


@socketio.on('message', namespace='/chat')
def handle_message(arg):
    arg = json.loads(str(json.dumps(arg)))
    emit('send', arg, broadcast=True)
    #print(arg)

@socketio.on('handle_password', namespace='/chat')
def handle_password(args):
    args = json.loads(str(json.dumps(args)))
    password = args['password']
    sha256 = hashlib.sha256()
    sha256.update(password.encode() + salt)
    trip = base64.b64encode(sha256.digest()).decode('utf-8')[0:6]
    emit('addtrip', {'yourtrip': trip}, broadcast=True)


if __name__ == '__main__':
    #app.run(host="0.0.0.0",port=80)
    port = int(os.environ.get('PORT', 15264))
    #server = pywsgi.WSGIServer(("0.0.0.0", port), app)
    #server.serve_forever()
    socketio.run(app, host='0.0.0.0', port=port)