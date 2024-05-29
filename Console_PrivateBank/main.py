import json
import logging
import platform
from datetime import date, timedelta, datetime
import aiohttp
import asyncio
import argparse

BASE_URL ='https://api.privatbank.ua/p24api/exchange_rates?json&date='
# BASE_URL = 'https://660951750f324a9a28831e25.mockapi.io/test/exchange_rates?'
def create_url_list_for_requests(num: int)-> list:
    dates = last_few_days(num)
    return list(map(lambda x: BASE_URL+x,dates))


def last_few_days(number_of_days: int)-> list:
    date_list = []
    today = date.today()
    for day in reversed(range(1, number_of_days+1)):
        date_list.append(datetime.strftime(today - timedelta(days=day),'%d.%m.%Y'))
    return date_list


async def parse_exchange_rate(data, currencies=None):
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


async def get_exchange_rates(url:str,val, session: aiohttp.ClientSession):
    async with session.get(url) as resp:
        print(f'Starting {url}')
        try:
            if resp.status == 200:
                r = await resp.json()
                return await parse_exchange_rate(r, val )
            else:
                print(f"Error status: {resp.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            print(f'Connection error: {url}', str(err))


async def main(num, val):
    async with aiohttp.ClientSession() as session:
        storage_data = []
        urls = create_url_list_for_requests(num)
        futures = [asyncio.create_task(get_exchange_rates(url_,val, session)) for url_ in urls]
        storage_data = await asyncio.gather(*futures)
        print(storage_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Program for selecting exchanges')
    parser.add_argument('num_day', help='кількість днів для вибірки курсу валют')
    parser.add_argument('type_val', nargs='*', default='', help='Тип валют(приклад USD EUR CAD)')
    args = parser.parse_args()

    num = abs(int(args.num_day))
    val = list(map(str.upper, args.type_val))
    if num > 10:
        print('The maximum number of days for a request is 10')
        exit(1)

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main(num, val))

