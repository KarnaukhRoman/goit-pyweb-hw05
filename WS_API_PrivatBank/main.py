import asyncio
from server import Server
from apipb import PrivatBankAPIClient, ExchangeRateService
import websockets

async def main():
    api_client = PrivatBankAPIClient()
    exchange_rate_service = ExchangeRateService(api_client)
    server = Server(exchange_rate_service)
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
