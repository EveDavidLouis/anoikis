var connection;
var i;

function openSocket(session = 0){

	var host = 'wss://esi-online.herokuapp.com'
	if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
		host = 'ws://'+ window.location.host
	};
	$('.loader').show();
	
	connection = new WebSocket(host+'/esi/'+ getCookie('_id'));
	i=i+1
	console.log('Connecting....'+ i);

	connection.onerror = function (event) {
		
		console.log('Error....'+ i);
		$('.loader').show();
		$('#brand').html('ESI-ERROR');
		
		connection.close();
	};

	connection.onclose = function (event) {
		
		console.log('Close....'+ i);
		
		$('.loader').show();
		$('#brand').html('ESI-OFFLINE');

		setTimeout(openSocket, 500);

	};

	connection.onopen = function (event) {

		$('.loader').hide();
		$('#brand').html('ESI-ONLINE');

		_url = new URL(window.location.href);
		_code = _url.searchParams.get("code");
		_state = _url.searchParams.get("state");
		if (_code != null && _state != null){
			connection.send(JSON.stringify({'code': _code,'state': _state}));
		}
		
	};

	connection.onmessage = function (event) {
		
		data = JSON.parse(event.data);

		if ('endPoint' in data){
			update(data);
		} else {
			console.log('NO ENDPOINT');
			console.log(data);	
		}
	};

}

function update(msg){
	

	switch(msg.endPoint) {
		case 'esi-login':
			setCookie(msg.data.name,msg.data.value,7);
			window.location = window.location.origin;
			break;
		case 'welcome':
			$('#main-container').html(msg.data);
			$('#navbar').hide();
			break;
		case 'home':	
			$('#navbar').show();
			$('#brand').html('<img src="https://image.eveonline.com/Character/'+ msg.data.CharacterID+'_64.jpg">'+msg.data.CharacterName);
			$('#main-container').html(msg.data);
			break;
		case 'myCharacters':
			console.log('MYCHARACTERS');
			console.log(msg.data);
			data = '<p>'+JSON.stringify(msg.data.characters)+'</p>'
			data += msg.data.addCharacter;
			$('#main-container').html(data);
			break;
		default:
			console.log('UNKNOW ENDPOINT');
			console.log(msg);
	}

	// if (msg.endPoint == 'login'){
	// 	$('#main-container').html(msg.login);
	// 	$('#navbar').hide();
	// }

	// if ('brand' in msg){
	// 	$('#brand').html('<img src="https://image.eveonline.com/Character/'++'_64.jpg">'+);
	// 	$('#navbar').show();
	// }

	// if ('main' in msg){
	// 	$('#main-container').html(msg.main);
	// }
	
	// if ('setCookie' in msg){
	// 	setCookie(msg.setCookie.name,msg.setCookie.value,7);
	// 	window.location = window.location.origin;
	// }

	// if ('addCharacter' in msg){
	// 	window.location = window.location.origin;
	// }
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
	return '';
}

function eraseCookie(name) {   
	document.cookie = name+'=; Max-Age=-99999999;';  
}

function logout () {
	eraseCookie('_id');
	location.reload();
}

function ownedCharacters () {
	connection.send(JSON.stringify({'ownedCharacters': 'GET'}));
}


$(document).ready(function(){
	i = 0;
	openSocket();
});