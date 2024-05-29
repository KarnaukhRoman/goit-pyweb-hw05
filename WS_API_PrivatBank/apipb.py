import asyncio
from datetime import datetime, timedelta
from aiohttp import ClientSession

class PrivatBankAPIClient:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    async def fetch_exchange_rate(self, session, date):
        url = f"{self.BASE_URL}{date}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
        except Exception as e:
            print(f"HTTP error occurred: {e}")
        return None

    def parse_exchange_rate(self, data, currencies=None):
        date = data['date']
        rates = {rate['currency']: rate for rate in data['exchangeRate']}
        result = {}
        if currencies:
            for currency in currencies:
                if currency in rates:
                    result[currency] = {
                        'sale': rates[currency].get('saleRateNB', rates[currency].get('saleRate')),
                        'purchase': rates[currency].get('purchaseRateNB', rates[currency].get('purchaseRate'))
                    }
        else:
            for currency, rate in rates.items():
                result[currency] = {
                    'sale': rate.get('saleRateNB', rate.get('saleRate')),
                    'purchase': rate.get('purchaseRateNB', rate.get('purchaseRate'))
                }
        return {date: result}

class ExchangeRateService:
    def __init__(self, api_client):
        self.api_client = api_client

    async def get_exchange_rates(self, days, currencies=None):
        async with ClientSession() as session:
            tasks = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
                tasks.append(self.api_client.fetch_exchange_rate(session, date))
            exchange_rates = await asyncio.gather(*tasks)
            parsed_rates = [self.api_client.parse_exchange_rate(data, currencies) for data in exchange_rates if data]
            return parsed_rates
