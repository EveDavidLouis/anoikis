var connection;

function openSocket(session = 0){

	// var host = 'wss://esi-eve-online.193b.starter-ca-central-1.openshiftapps.com'
	var host = 'wss://esi-eve-online.7e14.starter-us-west-2.openshiftapps.com'
	if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
		host = 'ws://'+ window.location.host
	};

	connection = new WebSocket(host+'/ws/'+ getCookie('_id'));
	
	connection.onopen = function (event) {

		_url = new URL(window.location.href);
		_code = _url.searchParams.get("code");
		if (_code != null){
			connection.send(JSON.stringify({'code': _code}));
		}
	};

	connection.onclose = function (event) {

		// $('body').html('<p>CONNECTION CLOSE</p>');
		$('body').load('offline.html').fadeIn('Slow');
		setTimeout(openSocket, 2000);
	};

	connection.onerror = function (event) {
		$('body').html('<p>ERROR</p>');
	};

	connection.onmessage = function (event) {

		data = JSON.parse(event.data);
		update(data);

	};
}

function update(updateData){
	
	console.log(updateData);
	
	if ('setCookie' in updateData){
		setCookie(updateData.setCookie.name,updateData.setCookie.value,7);
		window.location = window.location.origin;
	}

	if ('eraseCookie' in updateData){
		eraseCookie(updateData.eraseCookie.name);
		window.location = window.location.origin;
	}

	if ('login' in updateData){
		$('body').fadeIn('slow').html(updateData.login);
	}

	if ('welcome' in updateData){
		$('body').html(updateData.welcome).fadeIn('slow');
	}
	
}

function logout () {
	eraseCookie('_id');
	location.reload();
}

function setCookie(name,value,days) {
	var expires = "";
	if (days) {
		var date = new Date();
		date.setTime(date.getTime() + (days*24*60*60*1000));
		expires = "; expires=" + date.toUTCString();
	}
	document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}
function getCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}
function eraseCookie(name) {   
	document.cookie = name+'=; Max-Age=-99999999;';  
}

$(document).ready(function(){

	openSocket();

});