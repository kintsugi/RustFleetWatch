var shortid = require('shortid');

module.exports = function(Room) {

  Room.observe('before save', function genLink(ctx, next) {
    if(ctx.isNewInstance) {
      ctx.instance.link = shortid.generate();
      ctx.instance.joinLink = shortid.generate();
      ctx.instance.leaderLink = shortid.generate();
    }
    next();
  });

  Room.links = function(id, cb) {
    Room.findById(id, function(err, room) {
      if(err)
        cb(err);
      cb(null, {
        joinLink: room.joinLink,
        leaderLink: room.leaderLink
      });
    });
  }

  Room.remoteMethod(
    'links',
    {
      accepts: [
        {arg: 'id', type: 'number', required: true}
      ],
      returns: {arg: 'links', type: 'object'},
      http: {path: '/:id/links', verb: 'get'}
    }
  );
};
