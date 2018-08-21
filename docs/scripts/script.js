var body;
var connection;

function openSocket(){

	var host = 'wss://anoikis-eve-online.7e14.starter-us-west-2.openshiftapps.com'
	if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
		host = 'ws://'+ window.location.host
	};

	connection = new WebSocket(host+'/ws/1');
	
	connection.onopen = function (event) {
		body.html('<p>CONNECTION OPEN</p>');
	};

	connection.onclose = function (event) {
		body.html('<p>CONNECTION CLOSE</p>');
		// body.load('templates/offline.html');
		setTimeout(openSocket, 2000);
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
	
	console.log(updateData);

	if ('body' in updateData){
		body.html(updateData.body);
	}
	
}

function getCookie(name) {
    var dc = document.cookie;
    var prefix = name + "=";
    var begin = dc.indexOf("; " + prefix);
    if (begin == -1) {
        begin = dc.indexOf(prefix);
        if (begin != 0) return null;
    }
    else
    {
        begin += 2;
        var end = document.cookie.indexOf(";", begin);
        if (end == -1) {
        end = dc.length;
        }
    }
    // because unescape has been deprecated, replaced with decodeURI
    //return unescape(dc.substring(begin + prefix.length, end));
    return decodeURI(dc.substring(begin + prefix.length, end));
} 

function auth() {

	// var _id = getCookie("_id");

	// if (_id == null) {
	// 	body.load('./templates/login.html');
	// }
	// else {
	//  	openSocket();
	// }

	openSocket();

}

$(document).ready(function(){
	
	body = $('body');
	auth();

});