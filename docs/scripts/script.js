var connection;

function openSocket(){

	var host = 'wss://anoikis-eve-online.7e14.starter-us-west-2.openshiftapps.com'
	if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
		host = 'ws://'+ window.location.host
	};

	connection = new WebSocket(host+'/ws/1');
	
	connection.onopen = function (event) {
		$('body').html('<p>CONNECTION OPEN</p>');
	};

	connection.onclose = function (event) {

		$('body').html('<p>CONNECTION CLOSE</p>');
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
	
	// console.log(updateData);
	
	if ('setCookie' in updateData){
		console.log('SETTING COOKIE FROM SOCKET')
		setCookie(updateData.setCookie.name,updateData.setCookie.value,7);
		window.location = window.location.origin;
	}

	if ('eraseCookie' in updateData){
		console.log('DELETE COOKIE FROM SOCKET')
		eraseCookie(updateData.eraseCookie.name);
		window.location = window.location.origin;
	}

	if ('login' in updateData){
		console.log('DISPLAY LOGIN SCREEN FROM SOCKET')
		$('body').html(updateData.login);
	}

	if ('welcome' in updateData){
		console.log('DISPLAY WELCOME SCREEN FROM SOCKET')
		eraseCookie('_code')
		eraseCookie('_id')
		$('body').html('Welcome ' + updateData.welcome.name);
	}
	
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

function auth() {

	_url = new URL(window.location.href);
	_code = _url.searchParams.get("code");

	if (_code != null){
		console.log('SETTING CODE COOKIE FROM URL')
		setCookie('_code',_code,7)	
	}

	console.log('OPENING SOCKET')
	openSocket();

}

$(document).ready(function(){

	auth();

});