var connection;

function openSocket(){

	var host = 'wss://space-anoikis.1d35.starter-us-east-1.openshiftapps.com'
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
	
	console.log(updateData);
	
	if ('setCookie' in updateData){
		setCookie(updateData.setCookie.name,updateData.setCookie.value,7);
		window.location = window.location.origin;
	}

	if ('eraseCookie' in updateData){
		eraseCookie(updateData.eraseCookie.name);
		window.location = window.location.origin;
	}

	if ('body' in updateData){
		$('body').html(updateData.body);
	}

	if ('login' in updateData){
		$('body').html('Welcome ' + updateData.login.name);
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
		setCookie('_code',_code,7)
	}

	openSocket();

}

$(document).ready(function(){

	auth();

});