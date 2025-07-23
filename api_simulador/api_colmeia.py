from fastapi import FastAPI
import uvicorn
import json
import asyncio

app = FastAPI()

# Carrega dados históricos
with open("dados_historicos.json", "r") as f:
    dados = json.load(f)[0]  # acessa a lista interna

index = 0  # para controlar o dado atual

@app.get("/dados")
async def get_dado():
    global index
    if index >= len(dados):
        index = 0  # reinicia do início

    dado = dados[index]
    index += 1

    await asyncio.sleep(2)  # simula envio em tempo real
    return dado

if __name__ == "__main__":
    uvicorn.run("api_colmeia:app", host="0.0.0.0", port=8000, reload=True)
