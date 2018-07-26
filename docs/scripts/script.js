var data = [];
var connection = '';

function openSocket(){

	var host = 'wss://space-anoikis.1d35.starter-us-east-1.openshiftapps.com/ws/1'
	//var host = 'wss://0.0.0.0/ws'

	connection = new WebSocket(host);
	
	var body = $('body');

	connection.onopen = function (event) {
		body.html('<p>CONNECTION OPEN</p>');
	};

	connection.onclose = function (event) {
		body.load('templates/offline.html');
		setTimeout(openSocket, 10000);
	};

	connection.onerror = function (event) {
		body.html('<p>ERROR</p>');
	};

	connection.onmessage = function (event) {
		
		data = JSON.parse(event.data);
		update(data);
	};
}

function update(updateData){

	console.log('update')

}

$(document).ready(function(){
	openSocket();
});