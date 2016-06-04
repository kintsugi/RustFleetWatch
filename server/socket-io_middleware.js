var socketEvents = require('./socket_events.js')
var Promise = require('promise');

var self = {
  processRequest: function(app, msg) {
    self.authenticate(app, msg).done(function() {
      if(msg.event)
          socketEvents[msg.event](app, msg)
      else 
          throw new Error('Authenticated message with no event:' + msg)
    }, function(err) {
      console.log(err)
    })
  },

  authenticate: function(app, msg) {
    return new Promise(function(fulfill, reject) {
      if(!msg.token.userId || !msg.token.id)
        reject(new Error('Message has no token:' + msg))
      app.models.User.confirm(msg.token.userId, msg.token, null, function(err) {
        if(err)
          reject(err)
        fulfill()
      })
    });

  }
}

module.exports = self
