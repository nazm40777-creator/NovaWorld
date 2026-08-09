# ============================================================
# NovaWorld - Full Stack Virtual World App
# app.py
# Part 1/4
# FastAPI + WebSocket + Supabase Backend
# ============================================================

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Request,
    HTTPException
)

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None


# ============================================================
# ENVIRONMENT CONFIG
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ============================================================
# SUPABASE CONNECTION
# ============================================================

supabase = None

if SUPABASE_URL and SUPABASE_KEY and create_client:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
    except Exception as e:
        print("Supabase connection error:", e)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="NovaWorld",
    version="1.0.0",
    description="Virtual World Full Stack Game"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GLOBAL MEMORY STATE
# ============================================================

players: Dict[str, dict] = {}

connections: Dict[str, WebSocket] = {}

chat_history: List[dict] = []


# ============================================================
# DATA MODELS
# ============================================================

class PlayerCreate(BaseModel):
    username: str


class ChatMessage(BaseModel):
    username: str
    message: str
    room: str = "global"



# ============================================================
# WEBSOCKET MANAGER
# ============================================================

class ConnectionManager:

    async def connect(
        self,
        player_id: str,
        websocket: WebSocket
    ):
        await websocket.accept()

        connections[player_id] = websocket


    def disconnect(
        self,
        player_id: str
    ):
        if player_id in connections:
            del connections[player_id]


    async def send_personal(
        self,
        player_id: str,
        data: dict
    ):

        websocket = connections.get(player_id)

        if websocket:

            await websocket.send_json(data)



    async def broadcast(
        self,
        data: dict
    ):

        dead = []

        for pid, ws in connections.items():

            try:

                await ws.send_json(data)

            except Exception:

                dead.append(pid)


        for pid in dead:

            self.disconnect(pid)



manager = ConnectionManager()



# ============================================================
# SUPABASE HELPERS
# ============================================================

def save_message(data: dict):

    if not supabase:
        return


    try:

        supabase.table(
            "messages"
        ).insert(data).execute()


    except Exception as e:

        print(
            "Database message error:",
            e
        )



def save_player(data: dict):

    if not supabase:
        return


    try:

        supabase.table(
            "players"
        ).upsert(data).execute()


    except Exception as e:

        print(
            "Database player error:",
            e
        )



def load_messages():

    if not supabase:
        return []


    try:

        result = (
            supabase
            .table("messages")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .limit(50)
            .execute()
        )


        return result.data


    except Exception:

        return []



# ============================================================
# BASIC API
# ============================================================

@app.get(
    "/api/status"
)
async def status():

    return {
        "name": "NovaWorld",
        "status": "online",
        "players": len(players),
        "time": datetime.utcnow().isoformat()
    }



@app.post(
    "/api/player"
)
async def create_player(
    player: PlayerCreate
):

    player_id = str(
        uuid.uuid4()
    )


    data = {

        "id": player_id,

        "username": player.username,

        "x": 500,

        "y": 500,

        "created_at":
            datetime.utcnow().isoformat()

    }


    players[player_id] = data


    save_player(data)


    return data



@app.get(
    "/api/players"
)
async def get_players():

    return list(
        players.values()
    )



# ============================================================
# CHAT API
# ============================================================

@app.post(
    "/api/message"
)
async def send_message(
    msg: ChatMessage
):

    data = {

        "id":
            str(uuid.uuid4()),

        "username":
            msg.username,

        "message":
            msg.message,

        "room":
            msg.room,

        "created_at":
            datetime.utcnow().isoformat()

    }


    chat_history.append(data)


    save_message(data)


    await manager.broadcast(
        {
            "type": "message",
            "data": data
        }
    )


    return data



# ============================================================
# WEBSOCKET REALTIME SERVER
# ============================================================

@app.websocket(
    "/ws/{player_id}"
)
async def websocket_endpoint(
    websocket: WebSocket,
    player_id: str
):

    await manager.connect(
        player_id,
        websocket
    )


    await manager.broadcast(
        {
            "type":
                "player_join",

            "player":
                players.get(player_id)
        }
    )


    try:

        while True:

            data = await websocket.receive_json()


            if data.get("type") == "move":

                if player_id in players:

                    players[player_id]["x"] = data.get("x")

                    players[player_id]["y"] = data.get("y")


                    await manager.broadcast(
                        {
                            "type":
                                "player_move",

                            "player":
                                players[player_id]
                        }
                    )


            elif data.get("type") == "chat":

                message = {

                    "id":
                        str(uuid.uuid4()),

                    "username":
                        data.get("username"),

                    "message":
                        data.get("message"),

                    "room":
                        data.get(
                            "room",
                            "global"
                        ),

                    "created_at":
                        datetime.utcnow().isoformat()

                }


                chat_history.append(
                    message
                )


                save_message(
                    message
                )


                await manager.broadcast(
                    {
                        "type":
                            "message",

                        "data":
                            message
                    }
                )


    except WebSocketDisconnect:

        manager.disconnect(
            player_id
        )


        await manager.broadcast(
            {
                "type":
                    "player_leave",

                "player_id":
                    player_id
            }
        )


# ============================================================
# FRONTEND WILL CONTINUE IN PART 2/4
# ============================================================
# ============================================================
# FRONTEND HTML + CSS
# Part 2/4
# ============================================================


@app.get(
    "/",
    response_class=HTMLResponse
)
async def home():

    return HTMLResponse(
r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>NovaWorld</title>


<style>

/* =====================================================
   iOS DARK GLASS UI
===================================================== */


* {

    box-sizing:border-box;

    font-family:
    -apple-system,
    BlinkMacSystemFont,
    "SF Pro Display",
    Arial,
    sans-serif;

}


body {

    margin:0;

    overflow:hidden;

    background:
    radial-gradient(
        circle at top,
        #25345c,
        #050509
    );

    color:white;

}


/* =====================================================
   GAME WORLD
===================================================== */


#world {

    position:absolute;

    width:100vw;

    height:100vh;

    overflow:hidden;

    background:

    linear-gradient(
        135deg,
        rgba(255,255,255,.05),
        transparent
    ),

    #101522;

}


/* City grid */

.city-grid {

    position:absolute;

    inset:0;

    background-image:

    linear-gradient(
        rgba(255,255,255,.04) 1px,
        transparent 1px
    ),

    linear-gradient(
        90deg,
        rgba(255,255,255,.04) 1px,
        transparent 1px
    );


    background-size:
    80px 80px;

}



/* =====================================================
   BUILDINGS
===================================================== */


.building {

    position:absolute;

    border-radius:25px;

    backdrop-filter:blur(15px);

    background:
    rgba(255,255,255,.08);

    border:
    1px solid rgba(255,255,255,.12);

    box-shadow:
    0 20px 60px rgba(0,0,0,.4);

    display:flex;

    justify-content:center;

    align-items:center;

    font-size:18px;

}



/* Airport */

.airport {

    width:260px;

    height:150px;

    top:80px;

    left:80px;

}



/* Hospital */

.hospital {

    width:230px;

    height:160px;

    top:320px;

    right:100px;

}



/* Train station */

.station {

    width:300px;

    height:120px;

    bottom:160px;

    left:120px;

}



/* Bank */

.bank {

    width:250px;

    height:160px;

    bottom:100px;

    right:150px;

}



/* =====================================================
   PLAYER
===================================================== */


#player {


    position:absolute;


    width:45px;

    height:45px;


    border-radius:50%;


    background:

    linear-gradient(
        135deg,
        #ffffff,
        #6ca8ff
    );


    box-shadow:

    0 0 30px
    #4da3ff;


    transition:

    left .5s ease,

    top .5s ease;


    z-index:20;


}



.player-name {


    position:absolute;

    top:-25px;

    width:120px;

    text-align:center;

    font-size:13px;

}



/* =====================================================
   VEHICLES
===================================================== */


.vehicle {


    position:absolute;


    border-radius:20px;


    opacity:.8;


}



.car {


    width:35px;

    height:18px;

    background:#ffcc00;

    animation:

    roadMove 12s linear infinite;


}



.plane {


    width:70px;

    height:25px;

    background:#e9f5ff;

    animation:

    skyMove 18s linear infinite;


}



.train {


    width:120px;

    height:35px;

    background:#ff5555;

    animation:

    trainMove 15s linear infinite;


}



@keyframes roadMove {


from {

    transform:translateX(-100px);

}


to {

    transform:translateX(110vw);

}

}




@keyframes skyMove {


from {

    left:-100px;

    top:80px;

}


to {

    left:110vw;

    top:180px;

}

}




@keyframes trainMove {


from {

    left:-200px;

}


to {

    left:110vw;

}


}



/* =====================================================
 CHAT UI
===================================================== */


#chat {


position:absolute;


bottom:20px;


right:20px;


width:340px;


height:420px;


background:

rgba(20,20,30,.75);


backdrop-filter:

blur(20px);


border-radius:35px;


border:

1px solid rgba(255,255,255,.15);


display:flex;


flex-direction:column;


overflow:hidden;


}



#messages {


flex:1;


padding:15px;


overflow-y:auto;


}



.msg {


background:

#007aff;


padding:10px 15px;


border-radius:20px;


margin:8px;


max-width:80%;


}



#inputArea {


display:flex;


padding:10px;


}



#chatInput {


flex:1;


border:none;


outline:none;


padding:12px;


border-radius:20px;


background:#222;


color:white;


}



button {


border:none;


background:#007aff;


color:white;


border-radius:20px;


padding:10px 15px;


margin-right:5px;


}



/* =====================================================
 MOBILE
===================================================== */


@media(max-width:700px){


#chat {

width:90vw;

height:350px;

right:5vw;

}



}



</style>

</head>


<body>


<div id="world">


<div class="city-grid"></div>



<div class="building airport">
✈️ المطار الدولي
</div>


<div class="building hospital">
🏥 المستشفى التعليمي
</div>


<div class="building station">
🚆 محطة القطار
</div>


<div class="building bank">
🏦 البنك المركزي
</div>



<div class="vehicle car"
style="top:260px;">
</div>



<div class="vehicle plane">
</div>



<div class="vehicle train"
style="bottom:80px;">
</div>



<div id="player">

<div class="player-name">
Player
</div>

</div>



</div>



<div id="chat">


<div id="messages"></div>


<div id="inputArea">

<input
id="chatInput"
placeholder="اكتب رسالة..."
>


<button onclick="sendChat()">
إرسال
</button>


</div>


</div>



<script>


// JavaScript Engine continues in Part 3/4


</script>



</body>

</html>
"""
    )
// ============================================================
// NovaWorld Frontend Engine
// Part 3/4
// Player Movement + WebSocket + Live Chat
// ============================================================


let playerId = localStorage.getItem("player_id");

let username =
    localStorage.getItem("username")
    ||
    "Player";


if(!playerId){

    playerId =
        crypto.randomUUID();

    localStorage.setItem(
        "player_id",
        playerId
    );

}



let player = document.getElementById(
    "player"
);


let world =
    document.getElementById(
        "world"
    );


let messages =
    document.getElementById(
        "messages"
    );


let chatInput =
    document.getElementById(
        "chatInput"
    );



let position = {

    x:500,

    y:400

};



player.style.left =
position.x+"px";


player.style.top =
position.y+"px";



// ============================================================
// WEBSOCKET CONNECTION
// ============================================================


let protocol =
    location.protocol === "https:"
    ? "wss://"
    : "ws://";


let socket =
new WebSocket(
    protocol +
    location.host +
    "/ws/" +
    playerId
);



socket.onopen = ()=>{


    console.log(
        "Connected"
    );


};



socket.onmessage =
(event)=>{


    let data =
    JSON.parse(
        event.data
    );



    if(data.type==="message"){

        addMessage(
            data.data.username,
            data.data.message
        );

    }



    if(data.type==="player_move"){


        console.log(
            "Player moved:",
            data.player
        );


    }



};



socket.onclose = ()=>{


    console.log(
        "Disconnected"
    );


};




// ============================================================
// PLAYER MOVEMENT
// ============================================================


world.onclick =
(e)=>{


    let rect =
    world.getBoundingClientRect();


    position.x =
        e.clientX - 22;


    position.y =
        e.clientY - 22;



    player.style.left =
        position.x+"px";


    player.style.top =
        position.y+"px";



    if(socket.readyState===1){


        socket.send(

            JSON.stringify({

                type:"move",

                x:position.x,

                y:position.y

            })

        );


    }



};



// ============================================================
// CHAT
// ============================================================


function sendChat(){


    let text =
        chatInput.value.trim();



    if(!text)
        return;



    let data={

        type:"chat",

        username:username,

        message:text,

        room:"global"

    };



    if(socket.readyState===1){


        socket.send(
            JSON.stringify(data)
        );


    }



    chatInput.value="";


}



chatInput.addEventListener(
"keydown",
(e)=>{


    if(e.key==="Enter"){

        sendChat();

    }


});





function addMessage(
    user,
    text
){


    let div =
    document.createElement(
        "div"
    );


    div.className =
        "msg";


    div.innerHTML =
        "<b>"+
        user+
        "</b><br>"+
        text;



    messages.appendChild(
        div
    );


    messages.scrollTop =
        messages.scrollHeight;


}




// ============================================================
// LOAD PLAYER FROM SERVER
// ============================================================


async function createPlayer(){


    try{


        let res =
        await fetch(
            "/api/player",
            {

                method:"POST",

                headers:{

                    "Content-Type":
                    "application/json"

                },


                body:JSON.stringify({

                    username:username

                })

            }

        );


        let data =
        await res.json();



        console.log(
            data
        );


    }

    catch(err){

        console.log(err);

    }


}



createPlayer();




// ============================================================
// WORLD ANIMATION EFFECTS
// ============================================================


let clouds=[];


function createClouds(){


    for(
        let i=0;
        i<8;
        i++
    ){


        let c =
        document.createElement(
            "div"
        );


        c.style.position =
        "absolute";


        c.style.width =
        "120px";


        c.style.height =
        "40px";


        c.style.borderRadius =
        "50px";


        c.style.background =
        "rgba(255,255,255,.12)";


        c.style.top =
        Math.random()*300
        +"px";


        c.style.left =
        Math.random()*window.innerWidth
        +"px";



        world.appendChild(c);


        clouds.push(c);


    }


}



function animateWorld(){


    clouds.forEach(
        c=>{


            let x =
            parseFloat(
                c.style.left
            );


            x+=0.3;


            if(
                x >
                window.innerWidth
            ){

                x=-150;

            }


            c.style.left =
            x+"px";


        }
    );



    requestAnimationFrame(
        animateWorld
    );


}



createClouds();

animateWorld();



// ============================================================
// END PART 3/4
// Production Finishing In Part 4/4
// ============================================================
# ============================================================
# NovaWorld Production Layer
# Part 4/4
# Deployment + Security + Health Checks
# ============================================================


# ============================================================
# ERROR HANDLING
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    return JSONResponse(

        status_code=500,

        content={

            "success": False,

            "error":
                "Internal Server Error"

        }

    )



# ============================================================
# WORLD DATA API
# ============================================================


@app.get(
    "/api/world"
)
async def world_data():

    return {

        "world":
        "NovaWorld",

        "locations":[

            {

                "name":
                "International Airport",

                "type":
                "airport",

                "x":80,

                "y":80

            },


            {

                "name":
                "Educational Hospital",

                "type":
                "hospital",

                "x":900,

                "y":320

            },


            {

                "name":
                "Train Station",

                "type":
                "station",

                "x":120,

                "y":700

            },


            {

                "name":
                "Central Bank",

                "type":
                "bank",

                "x":900,

                "y":700

            }

        ]

    }




# ============================================================
# ONLINE PLAYERS
# ============================================================


@app.get(
    "/api/online"
)
async def online_players():

    return {

        "count":
            len(connections),

        "players":
            list(
                players.values()
            )

    }




# ============================================================
# CHAT HISTORY
# ============================================================


@app.get(
    "/api/chat/history"
)
async def history():

    if chat_history:

        return chat_history[-50:]


    return load_messages()




# ============================================================
# SERVER HEALTH CHECK
# ============================================================


@app.get(
    "/health"
)
async def health():

    return {

        "status":
        "healthy",

        "service":
        "NovaWorld",

        "database":
        "connected"
        if supabase
        else
        "local"

    }



# ============================================================
# STARTUP EVENT
# ============================================================


@app.on_event(
    "startup"
)
async def startup():

    print(
        """
=================================

 NovaWorld Server Started 🚀

 FastAPI:
 ONLINE

 WebSocket:
 ENABLED

 Supabase:
 {}

=================================
        """.format(

            "CONNECTED"
            if supabase
            else
            "DISABLED"

        )
    )




# ============================================================
# SHUTDOWN EVENT
# ============================================================


@app.on_event(
    "shutdown"
)
async def shutdown():

    print(
        "NovaWorld Server Closed"
    )



# ============================================================
# Railway / Render ENTRY POINT
# ============================================================


if __name__ == "__main__":

    import uvicorn


    port = int(
        os.getenv(
            "PORT",
            8000
        )
    )


    uvicorn.run(

        "app:app",

        host=
        "0.0.0.0",

        port=
        port,

        reload=False

    )


# ============================================================
# END OF app.py
# ============================================================

