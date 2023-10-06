from flask import Flask, request
from flask_socketio import SocketIO, join_room
from utils import *

app = Flask(__name__)
socketio = SocketIO(app)

# token을 기준으로 room 생성.
@socketio.on('join')
def onJoin(token):
    join_room(token)

# token room의 subscriber(client)에게 FL_model 전달.
@socketio.on('servSend')
def serverSend(token):
    model_bytes = fedModels(token)
    json = {'token': token, 'model_bytes': model_bytes}
    socketio.emit('cliRecv', json, to = token)
    colReq = connReq()
    colReq.delete_many({'token': token})

# token 생성 및 token의 capa 저장.
@app.route('/token', methods = ['POST'])
def genToken():
    if request.method == 'POST':
        token = generateToken()
        # insert token to MongoDB
        colToken = connToken()
        colToken.insert_one({'token': token, 'capa': request.get_json()['capa']})
        return token
    

# client로부터 모델 수신 및 capa 충족 시 연합 학습과 클라이언트로 모델 전달. 
@app.route('/request', methods = ['POST'])
def cliReq():
    if request.method == 'POST':
        # json = {'token': token, 'model_bytes': model_bytes}
        json = request.get_json()
        
        colReq = connReq()
        colReq.insert_one(json)

        colToken = connToken()
        capacity = colToken.find_one({'token': json['token']})['capa']

        if colReq.count_documents({'token': json['token']}) == capacity:
            serverSend(json['token'])

        return {'status': 'success'}

if __name__ == '__main__':
    socketio.run(app, port=5000)
