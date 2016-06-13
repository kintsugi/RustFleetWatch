module.exports = function(app) {
  delete app.models.Player.validations.email;
};
