function setInputSize() {
  var text = $(this).val();
  $(this).val(text)
  $(this).attr('size', text.length)
}

$(document).ready(function(){
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
});
