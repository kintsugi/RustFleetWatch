var socketEvents = require('./socket_events.js')
var Promise = require('promise');

//'token' or 'link'
var mode = 'link'

function tokenAuthenticate(app, msg) {
  return new Promise(function(fulfill, reject) {
    if(!msg.token.userId || !msg.token.id)
      reject(new Error('Message has no token:' + msg))

    app.models.AccessToken.findOne({
      where: {
        id: msg.token.id,
        userId: msg.token.userId,
      } 
    }, function(err, token) {
      if(err)
        reject(err);
      fulfill(token);
    });
  });
}

function linkAuthenticate(app, msg) {
  return new Promise(function(fulfill, reject) {
    if(!msg.link)
      reject(new Error('Message has no link:' + msg))
    
    app.models.Room.findOne({where: {or:[{link: msg.link}, {leaderLink: msg.link}, {joinLink: msg.link}]}}, function(err, room) {
      if(err)
        reject(err);
      if(!room)
        reject(new Error('No room with join/leader link:' + msg));

      msg.isViewer = room.link == msg.link;
      msg.isMember = room.joinLink == msg.link;
      msg.isLeader = room.leaderLink == msg.link;
      msg.room = room;
      fulfill(msg);
    })
  })
}


var self = {
  processRequest: function(app, msg, socket) {

    function callEvent() {
      if(msg.event && socketEvents[msg.event])
          socketEvents[msg.event](app, msg, socket)
      else 
          throw new Error('Authenticated message with no event or event doesnt exist:' + msg)
    }

    if(mode == 'token') {
      tokenAuthenticate(app, msg).done(callEvent, function(err) {
        console.log(err)
      })
    } else if(mode == 'link') {
      linkAuthenticate(app, msg).done(callEvent, function(err) {
        console.log(err)
      });
    }
  }
}

module.exports = self
