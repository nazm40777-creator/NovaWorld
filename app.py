import os
import json
import uuid
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="NovaWorld"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



# ==========================
# Static Files
# ==========================

app.mount(
    "/static",
    StaticFiles(directory="."),
    name="static"
)



@app.get("/")
async def home():

    return FileResponse(
        "index.html"
    )



# ==========================
# Players
# ==========================

players = {}

connections = []



async def broadcast(data):

    dead=[]

    for ws in connections:

        try:

            await ws.send_json(data)

        except:

            dead.append(ws)



    for ws in dead:

        connections.remove(ws)




# ==========================
# WebSocket
# ==========================


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()


    connections.append(
        websocket
    )


    player_id=None


    try:


        while True:


            data = await websocket.receive_json()



            if data["type"]=="join":


                player_id=data["id"]


                players[player_id]=data



                await broadcast({

                    "type":"player_join",

                    "player":data

                })





            elif data["type"]=="move":


                if player_id:


                    players[player_id]["x"]=data["x"]

                    players[player_id]["y"]=data["y"]



                    await broadcast({

                        "type":"player_move",

                        "player":
                        players[player_id]

                    })






            elif data["type"]=="chat":



                await broadcast({

                    "type":"chat",

                    "user":
                    data.get("user","Player"),

                    "text":
                    data.get("text",""),

                    "time":
                    datetime.utcnow().isoformat()

                })



    except WebSocketDisconnect:


        if websocket in connections:

            connections.remove(
                websocket
            )



        if player_id in players:

            del players[player_id]





# ==========================
# Run
# ==========================


if __name__=="__main__":


    import uvicorn


    uvicorn.run(

        "app:app",

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                8000
            )
        )

    )
