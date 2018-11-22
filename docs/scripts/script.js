var connection

function openSocket(){

	var host = 'wss://esi-online.herokuapp.com'
	if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
		host = 'ws://'+ window.location.host
	};

	$('.loader').show()
	
	connection = new WebSocket(host+'/esi/'+ getCookie('_id'))

	connection.onerror = function (event) {
		
		$('.loader').show()
		$('#brand').html('ESI-ERROR')	
		connection.close()
	};

	connection.onclose = function (event) {
				
		$('.loader').show()
		$('#brand').html('ESI-OFFLINE')

		setTimeout(openSocket, 500)

	};

	connection.onopen = function (event) {

		$('.loader').hide();
		$('#brand').html('ESI-ONLINE');

		_url = new URL(window.location.href)
		_code = _url.searchParams.get('code')
		_state = _url.searchParams.get('state')
		if (_code != null && _state != null){
			connection.send(JSON.stringify({'code': _code,'state': _state}))
		}
		
	};

	connection.onmessage = function (event) {
		
		msg = JSON.parse(event.data)
		if ('endPoint' in msg){
			
			app['endpoint'] = msg.endPoint
			app[msg.endPoint] = msg.data
			update(msg)

		} else if ('error' in msg) {
			console.warn(msg)
		} else {
			console.warn('NO ENDPOINT')
			console.warn(msg)
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
			$('#navbar').hide();
			break;
		case 'home':	
			$('#navbar').show();
			$('#brand').html('<img src="https://image.eveonline.com/Character/'+ msg.data.CharacterID+'_64.jpg">'+msg.data.CharacterName);
			getCharacters('owner');
			break;
		case 'esi-api':
			window.location = window.location.origin;
			break;
		case 'characters':
			break;
		case 'character':
			break;
		default:
			window.alert(JSON.stringify(msg));
			console.warn(msg);
	}
}


function setCookie(name,value,days) {
	var expires = '';
	if (days) {
		var date = new Date();
		date.setTime(date.getTime() + (days*24*60*60*1000));
		expires = '; expires=' + date.toUTCString();
	}
	document.cookie = name + '=' + (value || '')  + expires + '; path=/';
}
function getCookie(name) {
	var nameEQ = name + '=';
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

function logout() {
	eraseCookie('_id');
	location.reload();
}

function getCharacters(type='owner') {
	connection.send(JSON.stringify({'getCharacters': type}));
}

function getCharacter(characterID) {
	connection.send(JSON.stringify({'getCharacter': characterID}));
}

$(document).ready(function(){
	openSocket();
});