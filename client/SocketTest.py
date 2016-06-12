from socketIO_client import SocketIO, LoggingNamespace

host = 'localhost'
port = 3000 
socketIO = SocketIO(host, port, LoggingNamespace)
options = {
    'token': {
        "id": "tsHx9J3ZuLJXLaz7H0uq2sILl3pGfkWCFrxoWc7wkqsDFXfPoJnYHmLMQpNCRfIn",
        "ttl": 1209600,
        "created": "2016-06-04T06:36:48.403Z",
        "userId": 1
    },
    'event': 'test'
}
socketIO.emit('msg', options)
