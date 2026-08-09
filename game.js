// =====================================
// NovaWorld Game Engine
// game.js
// Part 1/3
// =====================================



let player = document.getElementById("player");

let world = document.getElementById("world-map");



let playerX = window.innerWidth / 2;

let playerY = window.innerHeight / 2;



// =====================================
// PLAYER MOVEMENT
// =====================================


function movePlayer(x,y){


    playerX = x;

    playerY = y;



    player.style.left =
    playerX + "px";


    player.style.top =
    playerY + "px";



    sendPlayerPosition();


}




if(world){


world.addEventListener(
"click",
function(event){



    let rect =
    world.getBoundingClientRect();



    let x =
    event.clientX -
    rect.left -
    25;



    let y =
    event.clientY -
    rect.top -
    25;



    movePlayer(
        x,
        y
    );



});



}





// =====================================
// PAGE NAVIGATION
// =====================================


const navButtons =
document.querySelectorAll(
".bottom-nav button"
);



const pages =
document.querySelectorAll(
".page"
);



navButtons.forEach(
button=>{


button.addEventListener(
"click",
()=>{


let target =
button.dataset.page;



pages.forEach(
page=>{


page.classList.remove(
"active"
);


});



let selected =
document.getElementById(
target
);



if(selected){

selected.classList.add(
"active"
);

}



});


});





// =====================================
// PLAYER DATA
// =====================================


let playerId =
localStorage.getItem(
"player_id"
);



if(!playerId){


playerId =
crypto.randomUUID();



localStorage.setItem(
"player_id",
playerId
);


}




let username =
localStorage.getItem(
"username"
)
||
"Player";



let coins =
localStorage.getItem(
"coins"
)
||
0;



document.getElementById(
"username"
).innerText =
username;



document.getElementById(
"coins"
).innerText =
coins;
// =====================================
// WEBSOCKET SYSTEM
// Part 2/3
// =====================================



let socket = null;



function connectServer(){



let protocol =
window.location.protocol === "https:"
?
"wss://"
:
"ws://";



socket = new WebSocket(

protocol +
window.location.host +
"/ws"

);





socket.onopen = function(){


console.log(
"Connected to NovaWorld"
);



socket.send(
JSON.stringify({

type:"join",

id:playerId,

username:username,

x:playerX,

y:playerY

})
);


};





socket.onmessage = function(event){



let data =
JSON.parse(
event.data
);





// CHAT MESSAGE


if(data.type === "chat"){


addChatMessage(

data.user,

data.text

);


}





// PLAYER MOVE


if(data.type === "player_move"){


updateOtherPlayer(
data.player
);


}




};





socket.onclose = function(){


console.log(
"Reconnecting..."
);



setTimeout(

connectServer,

3000

);



};



}




connectServer();





// =====================================
// SEND POSITION
// =====================================


function sendPlayerPosition(){



if(
socket &&
socket.readyState === WebSocket.OPEN

){


socket.send(

JSON.stringify({

type:"move",

id:playerId,

x:playerX,

y:playerY


})

);



}



}







// =====================================
// OTHER PLAYERS
// =====================================


let otherPlayers = {};



function updateOtherPlayer(data){



if(
data.id === playerId
)
return;





let other =
document.getElementById(
"player-" + data.id
);




if(!other){


other =
document.createElement(
"div"
);



other.id =
"player-" + data.id;



other.innerHTML =
"🧍";



other.style.position =
"absolute";



other.style.fontSize =
"40px";



other.style.zIndex =
"15";



world.appendChild(
other
);



}





other.style.left =
data.x + "px";



other.style.top =
data.y + "px";



otherPlayers[data.id] =
other;



}






// =====================================
// CHAT
// =====================================



let sendButton =
document.getElementById(
"send"
);



let messageInput =
document.getElementById(
"message"
);





if(sendButton){


sendButton.onclick =
function(){



let text =
messageInput.value.trim();



if(!text)
return;



socket.send(

JSON.stringify({

type:"chat",

user:username,

text:text

})

);



messageInput.value="";



};



}





function addChatMessage(
user,
text
){



let box =
document.getElementById(
"chat-list"
);



if(!box)
return;



let message =
document.createElement(
"div"
);



message.className =
"chat-user";



message.innerHTML =

"👤 <b>"
+
user
+
"</b><br>"
+
text;



box.appendChild(
message
);



box.scrollTop =
box.scrollHeight;



}
// =====================================
// NovaWorld Game Engine
// Part 3/3
// Final Features
// =====================================



// =====================================
// SAVE PLAYER DATA
// =====================================


function savePlayerData(){


localStorage.setItem(
"username",
username
);



localStorage.setItem(
"coins",
coins
);



}





savePlayerData();







// =====================================
// PLAYER LEVEL SYSTEM
// =====================================


let level =

Number(
localStorage.getItem("level")
)
||
1;



function addExperience(){



level++;



localStorage.setItem(
"level",
level
);



let levelElement =
document.getElementById(
"level"
);



if(levelElement){

levelElement.innerText =
level;

}


}







// =====================================
// RANDOM WORLD EVENTS
// =====================================



function worldEvent(){



let events=[

"🌟 حدث جديد في المدينة",

"🚗 سباق سيارات بدأ",

"✈️ طائرة وصلت للمطار",

"🎁 هدية مجانية ظهرت"

];



let random =

events[
Math.floor(
Math.random()*events.length
)
];



console.log(random);



}





setInterval(

worldEvent,

30000

);







// =====================================
// TELEGRAM MINI APP SUPPORT
// =====================================


if(
window.Telegram &&
window.Telegram.WebApp

){


const tg =
window.Telegram.WebApp;



tg.ready();



tg.expand();



console.log(
"Telegram Mini App Connected"
);



}







// =====================================
// DEVICE TOUCH SUPPORT
// =====================================


let touchStartX = 0;

let touchStartY = 0;



document.addEventListener(
"touchstart",
function(e){


touchStartX =
e.touches[0].clientX;


touchStartY =
e.touches[0].clientY;


});





document.addEventListener(
"touchend",
function(e){


let x =
e.changedTouches[0].clientX;



let y =
e.changedTouches[0].clientY;



// حركة بسيطة باللمس

if(world){

movePlayer(
x-25,
y-25
);

}


});






// =====================================
// LOADING
// =====================================


window.onload =
function(){


console.log(
"NovaWorld Loaded"
);



movePlayer(
playerX,
playerY
);



};
