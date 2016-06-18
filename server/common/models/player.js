var shortid = require('shortid');
var Promise = require('promise');

//1 year
var ttl = 60 * 60 * 24 * 365;
var PlayerModel;

function create() {
  return new Promise(function(fulfill, reject) {
    PlayerModel.create({
      password: shortid.generate()
    }, function(err, player) {
      if(err)
        reject(err)
      fulfill(player);
    });
  });
}

function getAccessToken(player) {
  return new Promise(function(fulfill, reject) {
    player.createAccessToken(ttl, function(err, token) {
      if(err)
        reject(err)
      fulfill(token);
    })
  });
}

module.exports = function(Player) {
  PlayerModel = Player;

  Player.join = function(cb) {
    create()
    .then(getAccessToken, cb)
    .then(function(token) {
      cb(null, token)
    }, cb)
  }
  
  Player.remoteMethod (
    'join',
    {
      http: {path: '/join', verb: 'POST'},
      returns: {arg: 'token', type: 'object'}
    }
  );
};
