var path = require("path");

module.exports = function(app) {
  app.get('/', function(req, res) {
    if(req.query.id)
      res.sendFile(clientPath('room.html'));
    else
      res.sendFile(clientPath('index.html'))
  });
};

function clientPath(relative) {
  return path.resolve(__dirname, '../../client/', relative);
}
