import logging
import requests
import io

# Exchange APIs
from exchanges.bisq import Bisq
from exchanges.robosats import Robosats
from exchanges.hodlhodl import HodlHodl

import config as config

import prettytable as pt
from PIL import Image, ImageDraw, ImageFont

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_tor_session():
    logging.info("starting tor session")
    session = requests.session()
    session.proxies = {'http':  'socks5h://127.0.0.1:' + config.TOR_PORT,
                       'https': 'socks5h://127.0.0.1:' + config.TOR_PORT}
    return session


def print_orders(fiat, direction, limit, exchanges):
    """Get orders from bisq, hodlhodl and robosats according to parameters

    Args:
        fiat (string): usd, eur, ...
        direction (string): 'buy' or 'sell'
        limit (int): percentage of premium
        exchanges (list): exchanges to query
    """
    logging.info('Exchanges: ' + exchanges)
    session = get_tor_session()
    price_exch = Bisq.getFiatPrice(fiat, session)
    if exchanges == "all":
        logging.info("Obtaining orders from bisq...")
        bisqOffers = Bisq.getOffers(fiat, direction, price_exch, session)
        logging.info("Obtaining orders from robosats...")
        robosatsOffers = Robosats.getOffers(fiat, direction, session)
        logging.info("Obtaining orders from hodlhodl...")
        hodlhodlOffers = HodlHodl.getOffers(
            fiat, direction, price_exch, session)
        allOffers = bisqOffers + robosatsOffers + hodlhodlOffers
    elif exchanges == "bisq":
        logging.info("Obtaining orders from bisq...")
        bisqOffers = Bisq.getOffers(fiat, direction, price_exch, session)
        allOffers = bisqOffers
    elif exchanges == "hodlhodl":
        logging.info("Obtaining orders from hodlhodl...")
        hodlhodlOffers = HodlHodl.getOffers(
            fiat, direction, price_exch, session)
        allOffers = hodlhodlOffers
    elif exchanges == "robosats":
        logging.info("Obtaining orders from robosats...")
        robosatsOffers = Robosats.getOffers(fiat, direction, session)
        allOffers = robosatsOffers
    if direction == "buy":
        allOffers.sort(key=lambda item: item.get('price'), reverse=True)
    elif direction == "sell":
        allOffers.sort(key=lambda item: item.get('price'))

    table = pt.PrettyTable(
        ['Exchange', 'Price', 'Dif', 'Min', 'Max', 'Method'])

    for offer in allOffers:
        if offer['method'].lower() not in config.avoid_methods:
            row = [f"{offer['exchange']:10}", f"{offer['price']:8n}", f"{offer['dif']:4.1f}%",
                   f"{offer['min_amount']:7n}", f"{offer['max_amount']:7n}", f"{offer['method']}"]
            if limit == "alloffers":
                table.add_row(row)
            else:
                if (direction == "buy") and (offer['dif'] > int(limit)):
                    table.add_row(row)
                if (direction == "sell") and (offer['dif'] < int(limit)):
                    table.add_row(row)
        # TODO: split the message in chunks so it won't exceed the max 4096 characters / msg
        if len(table.get_string()) > 3800:
            logger.info("limite de caracteres alcanzado")
            break
    logging.info("Done!")
    return(price_exch, table)


def table_to_img(table):
    """Convert table to image

    Args:
        table (PrettyTable): Table to convert

    Returns:
        Image: image
    """
    # Calculate dimensions of image from text
    fnt = ImageFont.truetype("fonts/FreeMono.ttf", 15)
    img = Image.new('RGB', (200, 100))
    d = ImageDraw.Draw(img)
    d.text((10, 10), table, font=fnt, fill=(255, 0, 0))
    text_width, text_height = d.textsize(table, font=fnt)
    # draw the actal image
    img = Image.new('RGB', (text_width+20, text_height+20), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text(xy=(10, 10), text=table, font=fnt, fill=(0, 0, 0))
    s = io.BytesIO()
    img.save(s, 'png')
    s.seek(0)
    return s
