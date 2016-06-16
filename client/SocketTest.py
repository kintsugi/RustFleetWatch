from socketIO_client import SocketIO, LoggingNamespace

host = 'localhost'
port = 3000 
socketIO = SocketIO(host, port, LoggingNamespace)
tokenOptions = {
    'token': {
        "id": "tsHx9J3ZuLJXLaz7H0uq2sILl3pGfkWCFrxoWc7wkqsDFXfPoJnYHmLMQpNCRfIn",
        "ttl": 1209600,
        "created": "2016-06-04T06:36:48.403Z",
        "userId": 1
    },
    'event': 'test'
}

link = 'Bkevudm1S'

subscribeObj = {
    'link': link,
    'event': 'subscribe',
}

playerUpdateObj = {
    'link': link,
    'event': 'playerUpdate',
    'userName': 'terminull',
    'stats': {
        'hp': 69,
        'hunger': 42,
        'thirst': 96,
    },
}


def subscribe():
    print 'subbbing'
    socketIO.emit('msg', subscribeObj)

def playerUpdate():
    print 'subbed'
    socketIO.emit('msg', playerUpdateObj)

socketIO.on('connect', subscribe);
socketIO.on('subscribed', playerUpdate)
x = 5
while x > 0:
    x = x - 1
    socketIO.emit('msg', playerUpdateObj)
    playerUpdateObj['stats']['hp'] = playerUpdateObj['stats']['hp'] - 2;
    socketIO.wait(1);
