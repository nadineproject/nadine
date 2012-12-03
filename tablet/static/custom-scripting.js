$(document).bind("mobileinit", function(){
  $.mobile.loader.prototype.options.text = "Please wait...";
  $.mobile.loader.prototype.options.textVisible = true;
  $.mobile.loader.prototype.options.theme = "a";
});