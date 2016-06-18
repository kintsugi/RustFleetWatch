
function getClients(app, room) {
  return new Promise(function(fulfill, reject) {
    app.models.Room.findById(room.id, function(err, room) {
      if(err)
        reject(err);
      if(room) {
        room.clients({}, function(err, clients) {
          if(err)
            reject(err);
          fulfill(clients);
        })
      }
      else
        reject(new Error('no room for playerUpdate: ' + msg))
    })

  })
}

function getRoom(app, socketId) {
  return new Promise(function(fulfill, reject) {
    app.models.Client.findOne({
      where: {
        socketId: socketId
      }
    }, function(err, client) {
      if(err)
        reject(err);
      if(client) {
        client.room({}, function(err, room) {
          if(err)
            reject(err);
          fulfill(room);
        })
      }
      else
        reject(new Error('No client for: ' + client))
    })
  });
}

function deleteClient(app, socketId) {
  app.models.Client.findOne({
    where: {socketId: socketId}
  }, function(err, client) {
    if(err) {
      console.log(err);
  } else if(client)
    client.destroy(function(err) {
      if(err)
        console.log(err)
    });
  })
}


function emitTo(app, clients, eventName, payload) {
  for(client in clients) {
    var socketId = clients[client].socketId;
    var socket = app.io.sockets.connected[socketId]
    if(!socket)
      deleteClient(app, socketId);
    else {
      socket.emit(eventName, payload);
    }
  }
}

function emitDisconnect(app, socket) {
  getRoom(app, socket.id)
  .then(function(room) {
    getClients(app, room)
  .then(function(clients) {
    emitTo(app, clients, 'playerDisconnect', {id: socket.id.substr(2)})
  })
  }, function(err) {console.log(err)});

}

function emitUpdate(app, msg, socket, clients) {
  var payload = {
    id: socket.id.substr(2),
    isLeader: msg.isLeader,
    isMember: msg.isMember,
    isViewer: msg.isViewer,
    userName: msg.userName,
    stats: msg.stats,
  }
  emitTo(app, clients,'playerUpdate', payload);
}

module.exports = {

  disconnect: function(app, socket) {
    emitDisconnect(app, socket)
    deleteClient(app, socket.id)
  },

  //User defined events below

  subscribe: function(app, msg, socket) {
    app.models.Client.create({
      socketId: socket.id,
      roomId: msg.room.id
    }, function(err, client) {
      if(err)
        console.log(err);
      else {
        socket.emit('subscribed');
      }
    });
  },

  playerUpdate: function(app, msg, socket) {
    getClients(app, msg.room).then(function(clients) {
      emitUpdate(app, msg, socket, clients);
    }, function(err) {
      console.log(err);
    });
  },
}
