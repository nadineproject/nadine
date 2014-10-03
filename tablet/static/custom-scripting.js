$(document).bind("mobileinit", function(){
  $.mobile.loader.prototype.options.text = "Please wait...";
  $.mobile.loader.prototype.options.textVisible = true;
  $.mobile.loader.prototype.options.theme = "a";
});

function showGuestForm() {
	document.getElementById('guestform-show').style.display = 'none';
	//document.getElementById('guestform-hide').style.display = 'inline';
	document.getElementById('guestform').style.display = 'block';
	document.getElementById('signin').style.display = 'none';
}

function hideGuestForm() {
	document.getElementById('guestform-show').style.display = 'inline';
	//document.getElementById('guestform-hide').style.display = 'none';
	document.getElementById('guestform').style.display = 'none';
	document.getElementById('signin').style.display = 'block';
}
