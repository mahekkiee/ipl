const container = document.getElementById("players")
const filter = document.getElementById("filter")

async function loadPlayers(){

let type = filter.value

let res = await fetch(`/players?type=${type}`)
let data = await res.json()

container.innerHTML = ""

data.forEach(p=>{

let card = document.createElement("div")
card.className = "card"

card.innerHTML = `
<div class="player">${p.name}</div>

<div class="stat">Team : ${p.team}</div>
<div class="stat">Nationality : ${p.nationality}</div>
<div class="stat">Strike Rate : ${p.strike_rate}</div>
<div class="stat">Current Bid : ₹${p.current_bid}</div>

<input id="bid-${p.id}" type="number" placeholder="Enter bid">

<button onclick="placeBid(${p.id})">
Place Bid
</button>
`

container.appendChild(card)

})

}

async function placeBid(id){

let bid = document.getElementById(`bid-${id}`).value

await fetch("/bid",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
player_id:id,
bid:bid
})

})

loadPlayers()

}

filter.addEventListener("change",loadPlayers)

loadPlayers()