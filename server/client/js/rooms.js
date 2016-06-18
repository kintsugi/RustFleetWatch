var pageInfo = {};
var socket;
var leaderTemplate;
var memberTemplate;

function setInputSize() {
  var text = $(this).val();
  $(this).val(text)
  $(this).attr('size', text.length)
}

//http://stackoverflow.com/questions/19491336/get-url-parameter-jquery-or-how-to-get-query-string-values-in-js
function getUrlParameter(sParam) {
  var sPageURL = decodeURIComponent(window.location.search.substring(1)),
    sURLVariables = sPageURL.split('&'),
    sParameterName,
    i;

  for (i = 0; i < sURLVariables.length; i++) {
    sParameterName = sURLVariables[i].split('=');

    if (sParameterName[0] === sParam) {
      return sParameterName[1] === undefined ? true : sParameterName[1];
    }
  }
};

function getRoom() {
  var queryUrl = '/api/Rooms?filter[where][link]=' + getUrlParameter('id');
  return new Promise(function(fulfill, reject) {
    var jqxhr = $.ajax({
      type: 'GET',
      url: queryUrl,
      success: function(data) {
        pageInfo.room = data[0];
        fulfill(data[0])
      }
    })
      .fail(reject);
  });
}
function getLinks(room) {
  return new Promise(function (fulfill, reject) {
    var jqxhr = $.ajax({
      type: 'GET',
      url: '/api/Rooms/' + room.id + '/links',
      headers: {
        Authorization: pageInfo.user.token.id
      },
      success: function(data) {
        pageInfo.owner = true;
        fulfill(data.links);
      }
    })
      .fail(reject);
  })
}

function setLinks(links) {
  $('#leader-link').text(links.leaderLink);
  $('#join-link').text(links.joinLink);
  $('#link-row').show();
}

function setPayload(player, payload) {
  $(player).find('.username').text(payload.userName)
  var userStats = $(player).children('.user-stats')
  var hp = $(userStats).find('.hp');
  var thirst = $(userStats).find('.thirst');
  var hunger = $(userStats).find('.hunger');
  $(hp).css({
    width: payload.stats.hp + '%'
  });
  $(hp).parent().children('.bar-text').text(payload.stats.hp)
  $(thirst).css({
    width: payload.stats.thirst + '%'
  });
  $(thirst).parent().children('.bar-text').text(payload.stats.thirst)
  $(hunger).css({
    width: payload.stats.hunger + '%'
  });
  $(hunger).parent().children('.bar-text').text(payload.stats.hunger)


} 

function addPlayer(payload) {
  console.log(payload)
  if(payload.isLeader) {
    newLeader = $(leaderTemplate).clone();
    $(newLeader).attr('id', payload.id);
    setPayload(newLeader, payload);
    $('#leader').append(newLeader);
  } else if(payload.isMember) {
    newMember = $(memberTemplate).clone();
    $(newMember).attr('id', payload.id);
    setPayload(newMember, payload);
    $('#leader').append(newMember);
  }
}

function playerUpdate(payload) {
  if($('#' + payload.id).length < 1) {
    addPlayer(payload);
  } else {
    setPayload($('#' + payload.id), payload);
  }

}

function playerDisconnect(payload) {
  $('#' + payload.id).remove();
}

function init() {
  pageInfo.user = JSON.parse(window.localStorage.getItem('user'));
  getRoom().then(getLinks).then(setLinks);
  socket = io.connect();

  socket.on('connect', function() {
    console.log('connect')
    socket.emit('msg', {
      event: 'subscribe',
      link: getUrlParameter('id'), 
    })
  })

  socket.on('playerUpdate', function(payload) {
    console.log('update')
    playerUpdate(payload);
  })

  socket.on('playerDisconnect', function(payload) {
    playerDisconnect(payload);
  })

}

$(document).ready(function(){
  leaderTemplate = $('#leader-template').clone();
  memberTemplate = $('#member-template').clone();

  $('#link-row').hide();
  $('#leader-template').hide();
  $('#member-template').hide();
  $('#add-squad').hide();

  $('.subtle-input').each(setInputSize);
  $('.subtle-input').on('change', setInputSize);

  $('.collapse-btn').on('click', function() {
    collapsed = $(this).attr('aria-expanded')
    console.log(collapsed)
    var glyph = $(this).find('.glyphicon');
    if(collapsed == 'true') {
      $(glyph).removeClass('glyphicon-menu-down')
      $(glyph).addClass('glyphicon-menu-right')
    } else {
      $(glyph).removeClass('glyphicon-menu-right')
      $(glyph).addClass('glyphicon-menu-down')
    }
  })

  init();



});
