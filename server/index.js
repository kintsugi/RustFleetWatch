var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);

var users = {};

app.get('/', function(req, res){
    res.sendFile(__dirname + '/index.html');
});

app.get('/css/ss.css', function(req, res){
  res.sendFile(__dirname + '/css/ss.css');
});

http.listen(3000, function(){
    console.log('listening on *:3000');
});

io.on('connection', function(socket){
    socket.on('playerupdate', function(data, fn) {
        users[socket.id] = data;
    });
    
    socket.on('disconnect', function(data, fn) {
        delete users[socket.id];
    })
});

setInterval(function(){
    io.emit('userlist', users);
}, 100);