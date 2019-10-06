var host = 'wss://zkillboard.com:2096'

Vue.component('status', {
	props: ['data'],
	template: `
		<h2>{{data}}</h2>
	`
});

Vue.component('stream', {
	props: ['data','names'],
	template: `
		<ul>
			<li v-for="log in data">
				<div v-if="log.kill">
					{{ log.event }}: {{ character_name(log.kill.victim.character_id) }}
				</div>
				<div v-else>
					{{ log.event }}: {{ log.data }}
				</div>
			</li>
		</ul>
	`,
	methods: {
		character_name: function (character_id) {
			this.$parent.addName(character_id);
			return this.$parent['names'][character_id];
		}
	}
});

const app = new Vue({
	el: "#app",
	data: {
		message: "",
		logs: [],
		names:{},
		status: "disconnected"
	},
	methods: {
		connect() {
			this.socket = new WebSocket(host);
			this.socket.onopen = () => {
				this.status = "connected";
				this.logs.unshift({ event: "Connected to", data: host})
				
				this.socket.onmessage =  ({data})  => {	
					this.logs.unshift({ event: "Recieved message", kill:JSON.parse(data) });

				};

				this.message = {"action":"sub","channel":"killstream"}
				this.sendMessage();
			};
		},
		disconnect() {
			this.socket.close();
			this.status = "disconnected";
			this.logs = [];
		},
		sendMessage(e) {
			this.socket.send(JSON.stringify(this.message) );
			this.logs.unshift({ event: "Sent message", data:this.message });
			this.message = "";
		},
		addName(id){
			this.names[id] = null;
			this.saveNames();
		},
		saveNames(){
			const parsed = JSON.stringify(this.names);
			localStorage.setItem('names', parsed);
		}

	},
	mounted() {
				
		if (!(localStorage.getItem('names'))) {
			localStorage.setItem('names', JSON.stringify({}));
		}

		try {
			this.names = JSON.parse(localStorage.getItem('names'));
		} catch(e) {
			localStorage.removeItem('names');
		}
	
	},
	watch: {
		names(newName) {
			localStorage.names = JSON.stringify(newName);
		}
	}
});

app.connect();