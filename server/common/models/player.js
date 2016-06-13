var shortid = require('shortid');
var Promise = require('promise');

function create(Player) {
    return new Promise(function(fulfill, reject) {
      Player.create({
        password: shortid.generate()
      }, function(err, player) {
        if(err)
          reject(err)
        fulfill(player);
      });
    });
}

function getAccessToken(player) {

}


module.exports = function(Player) {

  Player.join = function(cb) {
    create(Player).done(function(player) {

    }, cb);
    
  }
  
  Player.remoteMethod (
        'join',
        {
          http: {path: '/join', verb: 'POST'},
          returns: {arg: 'user', type: 'object'}
        }
    );
};
