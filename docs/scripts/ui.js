var app = new Vue({
			el: '#app',
			data: {
				endpoint: null,
				welcome: null,
				character: null,
				characters: null
			}
		})

//++++++++++++++++++++
// MINI PORTAIT
//++++++++++++++++++++
Vue.component('miniportrait', {
	props: {'data'},
	template: `
		<div class="col-lg-2 p-2">
			<a :href="portraitHref">
				<img :src="portraitUrl" class="img-fluid rounded mx-auto d-block" :title="data.CharacterName">
			</a>
		</div>
	`,
	computed: {
		portraitUrl: function () {
			return 'https://image.eveonline.com/Character/' + this.data.CharacterID + '_128.jpg'
		},
		portraitHref: function () {
			return 'javascript:getCharacter('+this.data.CharacterID+')'
		}
	}
})

//++++++++++++++++++++
// STATS
//++++++++++++++++++++
Vue.component('stats', {
	props: ['data'],
	template: `

		<div class="row">
			<div class="col-lg-12">
				<div v-for="(stat,statName) in statsMap" class="card">
					<div class="card-header collapes" :data-target="'#'+statName" data-toggle="collapse" aria-expanded="false">
						<h5 class="mb-0">{{statName}}</h5>
					</div>
					<div :id="statName" class="collapse">
						<div v-for="(v,k) in stat" class="card-body p-0">
							<table class="table mb-0 table-striped">
								<tbody>
									<tr>
										<td><strong>{{k}}:</strong>{{v}}</td>		
									</tr>
								</tbody>
							</table>
						</div>
					</div>
				</div>	
			</div>
		</div>
	`,
	computed: {
		number: function (input) {
			return (input).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
		},
		statsMap: function () {


			return this.data['stats'].reduce(function(map, obj) {
				
				for (group in obj){
					
					if (group == 'year'){continue;}

					if (!(group in map)){map[group]={}}

					for (stat in obj[group]){
						if (stat in map[group]){
							map[group][stat] += obj[group][stat]
						}else{
							map[group][stat] = obj[group][stat]
						}
						
					}
				}

				return map

			}, {} )
		
		}
		
	}
})

//++++++++++++++++++++
// GENERAL
//++++++++++++++++++++
Vue.component('general', {
	props: ['data'],
	template: `
	<div class="row">
		<div class="col-lg-3">
			<img :src="portraitUrl" class="img-fluid rounded mx-auto d-block" :title="data.esi_api.CharacterName">
		</div>
		<div class="col-lg-9">
			<div class="row">
				<div class="col-lg-6">
					<ul class="list-group">
						<li class="list-group-item d-flex justify-content-between align-items-center"><strong>Name:</strong>{{ data.esi_api.CharacterName }}</li>
						<li class="list-group-item d-flex justify-content-between align-items-center"><strong>Owner:</strong><miniportrait :data="{CharacterID:data.owner,CharacterName:''}"></miniportrait></li>
					
					</ul>
				</div>
				<div class="col-lg-6">
					<ul class="list-group">
						<li class="list-group-item d-flex justify-content-between align-items-center" v-if="data.location.solar_system_id"><strong>Current Location:</strong>{{ data.location.solar_system_id }}</li>
						<li class="list-group-item d-flex justify-content-between align-items-center" v-if="data.location.structure_id"><strong>Structure:</strong>{{ data.location.structure_id }}</li>
					
					</ul>
				</div>
			</div>
		</div>
	</div>
	`,
	computed: {
		portraitUrl: function () {
			return 'https://image.eveonline.com/Character/' + this.data.esi_api.CharacterID + '_512.jpg'
		}
	}
})

//++++++++++++++++++++
// BOOKMARKS
//++++++++++++++++++++
Vue.component('bookmarks', {
	props: ['data'],
	template: `
	<div class="row">
		<div class="col-lg-12">
			<div v-for="(folder,folder_id) in bookmarkMap" class="card">
				<div class="card-header collapes" :data-target="'#'+folder_id" data-toggle="collapse" aria-expanded="false">
					<h5 class="mb-0">{{folder.name}}</h5> <span class="badge badge-primary badge-pill"></span>
				</div>
				<div :id="folder_id" class="collapse">
					<div v-for="bm in folder.bookmarks" class="card-body p-0">
						<table class="table mb-0 table-striped">
							<tbody>
								<tr>
									<td style="width: 25%">{{bm.label}}</td>	
									<td style="width: 25%">{{bm.location_id}}</td>		
									<td style="width: 25%">{{bm.creator_id}}</td>	
									<td style="width: 25%">{{bm.notes}}</td>			
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>	
		</div>
	</div>
	`,
	computed:{
		bookmarkMap: function(){

			var bookmarks_map = this.data['bookmarks-folders'].reduce(function(map, obj) {
				
				map[obj.folder_id] = {'name':obj.name,'bookmarks':[]}
				return map

			}, {})
			
			bookmarks_map[0] = {'name':'No Folder','bookmarks':[]}

			var bookmarks_map = this.data['bookmarks'].reduce(function(map,obj){
				
				if ('folder_id' in obj) {map[obj.folder_id].bookmarks.push(obj)} 
				else { map[0].bookmarks.push(obj)}
				return map

			},bookmarks_map)
			
			return bookmarks_map
		}
	}
})

//++++++++++++++++++++
// WALLET
//++++++++++++++++++++
Vue.component('walletdetails', {
	props: ['data'],
	template: `
		<tr>
			<td v-bind:class="indicator">{{date}}</th>
			<td v-bind:class="indicator">{{balance}}</th>
			<td v-bind:class="indicator">{{amount}}</th>
			<td v-bind:class="indicator">{{data.ref_type}}</th>	
			<td v-bind:class="indicator">{{data.description}}</th>
			<td v-bind:class="indicator">{{data.reason}}</th>
		</tr>
	`,
	computed: {
		balance: function () {
			return (this.data.balance).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
		},
		amount: function () {
			return (this.data.amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
		},
		indicator: function () {
			
			switch (true){
				case (Math.abs(this.data.amount) < 100000000):
					return ""
					break
				case (Math.abs(this.data.amount) < 1000000000):
					return "table-warning"
					break
				default:
					return "table-danger"
					break
			}
		},
		date: function () {
			return new Date(this.data.date).toISOString().slice(0,10)
		}
	}
})

Vue.component('wallet', {
	props: ['data'],
	template: `
	<div class="row">
		<div class="col-lg-12">
		<table class="table table-striped table-hover table-bordered table-sm" id="wallet">
			<thead class="table-dark">
				<tr>
					<th>date</th>
					<th>balance</th>
					<th>amount</th>
					<th>ref_type</th>	
					<th>description</th>
					<th>reason</th>
				</tr>
			</thead>
			<tbody>
				<walletdetails v-for="item in data['wallet-journal']" :key="item.id" v-bind:data="item">
				</walletdetails>
			</tbody>
		</table>
		</div>
	</div>
	`
})

//++++++++++++++++++++
// TRANSACTIONS
//++++++++++++++++++++
Vue.component('transactionsdetails', {
	props: ['data'],
	template: `
		<tr>
			<td v-bind:class="indicator">{{date}}</th>
			<td v-bind:class="indicator">{{data.location_id}}</th>
			<td v-bind:class="indicator">{{data.client_id}}</th>
			<td v-bind:class="indicator">{{data.type_id}}</th>
			<td v-bind:class="indicator">{{qty}}</th>
			<td v-bind:class="indicator">{{up}}</th>
			<td v-bind:class="indicator">{{amount}}</th>
		</tr>
	`,
	computed: {
		up: function () {
			return (this.data.unit_price).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
		},
		qty: function () {
			return (this.data.quantity).toFixed(0).replace(/\d(?=(\d{3})+\.)/g, '$&,')
		},
		amount: function () {
			return (this.data.unit_price * this.data.quantity).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
		},
		indicator: function () {
			
			switch (true){
				case (Math.abs(this.data.unit_price * this.data.quantity) < 100000000):
					return ""
					break
				case (Math.abs(this.data.unit_price * this.data.quantity) < 1000000000):
					return "table-warning"
					break
				default:
					return "table-danger"
					break
			}
		},
		date: function () {
			return new Date(this.data.date).toISOString().slice(0,10)
		}
	}
})

Vue.component('transactions', {
	props: ['data'],
	template: `
	<div class="row">
		<div class="col-lg-12">
		<table class="table table-striped table-hover table-bordered table-sm" id="transactions">
			<thead class="table-dark">
				<tr>
					<th>Date</th>
					<th>Location</th>
					<th>Client</th>
					<th>Item</th>
					<th>Quantity</th>
					<th>Unit price</th>
					<th>Total Value</th>
				</tr>
			</thead>
			<tbody>
				<transactionsdetails v-for="item in data['wallet-transactions']" :key="item.id" v-bind:data="item">
				</transactionsdetails>
			</tbody>
		</table>
		</div>
	</div>
	`
})