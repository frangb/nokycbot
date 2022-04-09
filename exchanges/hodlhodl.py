#!/usr/bin/env python3

import json
import requests
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


class HodlHodl:

    def getOffers(curr, direction, refprice, session):
        curr = curr.upper()
        api = f"https://hodlhodl.com/api/v1/offers?filters[side]={direction}&filters[include_global]=true&filters[currency_code]={curr}&filters[only_working_now]=true&sort[by]=price"
        try:
            f = session.get(api)
        except requests.exceptions.Timeout as e:
        # Maybe set up for a retry, or continue in a retry loop
            logger.error("Error obtaining orders from Robosats (timeout): %s - %s" % (e.errno, e.strerror))
            return []
        except requests.exceptions.TooManyRedirects as e:
            logger.error("Error obtaining orders from Robosats (too many redirects): %s - %s" % (e.errno, e.strerror))
            return []
        except requests.exceptions.RequestException as e:
            logger.error("Error obtaining orders from Robosats: %s - %s" % (e.errno, e.strerror))
            return []

        try:
            jsonweb = f.json()
            f.close()
            alloffers = jsonweb['offers']
        except json.decoder.JSONDecodeError as e:
            logger.error("Error decoding orders from HodlHodl: %s - %s" % (e.errno, e.strerror))
            return []

        lista = []

        for offer in alloffers:
            offers = {}
            offers['exchange'] = "HodlHodl"
            offers['price'] = int(float(offer['price']))
            offers['dif'] = (offers['price']/refprice - 1)*100
            offers['currency'] = offer['currency_code']
            offers['min_amount'] = int(float(offer['min_amount']))
            offers['max_amount'] = int(float(offer['max_amount']))
            offers['min_btc'] = offers['min_amount']/offers['price']
            offers['max_btc'] = offers['max_amount']/offers['price']
            status = offer['trader']['online_status']
            if (direction == "buy"):
                offers['method'] = offer['payment_methods'][0]['name']
            else:
                offers['method'] = offer['payment_method_instructions'][0]['payment_method_name']
            if "SEPA" in offers['method']:
                offers['method'] = "SEPA"
            elif "Any national bank" in offers['method']:
                offers['method'] = "NATIONAL_BANK"
            if (status == 'online'):
                lista.append(offers)

        lista.sort(key=lambda item: item.get("price"))
        return lista
