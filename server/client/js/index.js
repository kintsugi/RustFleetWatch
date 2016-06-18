function join() {
  return new Promise(function(fulfill, reject) {
    var user = JSON.parse(window.localStorage.getItem('user'));
    console.log(user);
    if(user)
      fulfill(user);
    else {
      var jqxhr = $.post('/api/Players/join', function(data) {
        window.localStorage.setItem('user', JSON.stringify(data))
        console.log(data);
        fulfill(data);
      })
        .fail(reject);
    }
  });
}

function createRoom(user) {
  return new Promise(function(fulfill, reject) {
    var jqxhr = $.ajax({
      type: 'POST',
      url: '/api/Rooms',
      contentType: 'application/json',
      data: JSON.stringify({
        playerId: user.token.userId
      }),
      success: function(data) {
        fulfill({user: user, room: data});
      },
    })
      .fail(reject)
  });
}

$(document).ready(function(){
  $('#create-room-button').on('click', function() {
    join().then(createRoom).then(function(userRoom) {
      window.location = '?id=' + userRoom.room.link;
    });
  });
});
