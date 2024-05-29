import asyncio
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from aiofile import AIOFile, Writer
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)

class Server:
    clients = set()

    def __init__(self, exchange_rate_service):
        self.exchange_rate_service = exchange_rate_service

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            await asyncio.gather(*[client.send(message) for client in self.clients])

    async def log_command(self, command):
        async with AIOFile("exchange_log.txt", 'a') as afp:
            writer = Writer(afp)
            await writer(f"{datetime.now()}: {command}\n")

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            params = message.split(' ')
            if params[0] == 'exchange':
                await self.log_command(message)
                days = int(params[1]) if len(params) > 1 else 1
                currencies = params[2:] if len(params) > 2 else None
                exchange_rates = await self.exchange_rate_service.get_exchange_rates(days, currencies)
                response = json.dumps(exchange_rates, ensure_ascii=False)
                await self.send_to_clients(response)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

