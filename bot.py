#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is a telegram bot to get offers from p2p exchanges like
    bisq, hodlhodl and robosats"""

import logging

from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from exchanges.bisq import Bisq
from exchanges.robosats import Robosats
from exchanges.hodlhodl import HodlHodl

import requests
import os
import prettytable as pt
from PIL import Image, ImageDraw, ImageFont
import io

import config as config

# read MODE env variable, fall back to 'polling' when undefined
mode = os.environ.get("MODE", config.DEFAULT_CONNECTION)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Keyboards
keyboard_actions = [
    [
        InlineKeyboardButton("I want to buy BTC", callback_data='sell'),
        InlineKeyboardButton("I want to sell BTC", callback_data='buy')
    ]
]

keyboard_exchanges = [
    [
        InlineKeyboardButton("Bisq", callback_data='bisq'),
        InlineKeyboardButton("HodlHodl", callback_data='hodlhodl'),
        InlineKeyboardButton("Robosats", callback_data='robosats'),
        InlineKeyboardButton("All", callback_data='all')
    ]
]

keyboard_currencies = [
    [
        InlineKeyboardButton("USD", callback_data='usd'),
        InlineKeyboardButton("EUR", callback_data='eur')
    ]
]

keyboard_premium = [
    [
        InlineKeyboardButton("-9%", callback_data='-9'),
        InlineKeyboardButton("-7%", callback_data='-7'),
        InlineKeyboardButton("-5%", callback_data='-5'),
        InlineKeyboardButton("-3%", callback_data='-3'),
        InlineKeyboardButton("-1%", callback_data='-1')
    ],
    [
        InlineKeyboardButton("Show all", callback_data='alloffers'),
    ],
    [
        InlineKeyboardButton("0%", callback_data='0'),
        InlineKeyboardButton("1%", callback_data='1'),
        InlineKeyboardButton("3%", callback_data='3'),
        InlineKeyboardButton("5%", callback_data='5'),
        InlineKeyboardButton("7%", callback_data='7'),
        InlineKeyboardButton("9%", callback_data='9'),
    ]
]
keyboard_developer = [
    [InlineKeyboardButton("Message the developer",
                          url='https://t.me/fgbernal')]
]

keyboard_runquery = [
    [InlineKeyboardButton("Run query", callback_data='query')]
]

keyboard_format = [
    [
        InlineKeyboardButton("Plain text", callback_data='text'),
        InlineKeyboardButton("Image", callback_data='img')
    ]
]

# End User configuration


def table_to_img(table):
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


def get_tor_session():
    logging.info("starting tor session")
    session = requests.session()
    session.proxies = {'http':  'socks5h://127.0.0.1:' + config.TOR_PORT,
                       'https': 'socks5h://127.0.0.1:' + config.TOR_PORT}
    return session


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Welcome to noKYCbot. I will help you find buy and sell orders in Bisq, HodlHodl and Robosats. Please configure the following options:')
    action_url(update, context)
    exchange_url(update, context)
    currency_url(update, context)
    premium_url(update, context)
    format_url(update, context)
    # TODO: Add button to run query from this menu


def help(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup(keyboard_developer)
    update.message.reply_text("""Available Commands:
    /start - configure your options
    /query - execute the query
    /help - show this help message
    /exchange - select the exchange
    /currency - set the currency you want to pay or get paid
    /premium - set the premium over or under market price you're willing to accept
    /action - you want to buy or sell bitcoin?
    /format - output format, image or plain text
    """, reply_markup=reply_markup)


def print_orders(fiat, direction, limit, exchanges):
    session = get_tor_session()
    price_exch = Bisq.getFiatPrice(fiat, session)
    if exchanges == "all":
        logging.info("Obtaining orders from bisq")
        bisqOffers = Bisq.getOffers(fiat, direction, price_exch, session)
        logging.info("Obtaining orders from robosats")
        robosatsOffers = Robosats.getOffers(fiat, direction, session)
        logging.info("Obtaining orders from hodlhodl")
        hodlhodlOffers = HodlHodl.getOffers(
            fiat, direction, price_exch, session)
        allOffers = bisqOffers + robosatsOffers + hodlhodlOffers
    elif exchanges == "bisq":
        logging.info("Obtaining orders from bisq")
        bisqOffers = Bisq.getOffers(fiat, direction, price_exch, session)
        allOffers = bisqOffers
    elif exchanges == "hodlhodl":
        logging.info("Obtaining orders from hodlhodl")
        hodlhodlOffers = HodlHodl.getOffers(
            fiat, direction, price_exch, session)
        allOffers = hodlhodlOffers
    elif exchanges == "robosats":
        logging.info("Obtaining orders from robosats")
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
    return(price_exch, table)


def query_url(update: Update, context: CallbackContext):
    if "exchange" in context.user_data.keys():
        exchange = context.user_data["exchange"]
    else:
        exchange = "all"

    if "action" in context.user_data.keys():
        action = context.user_data["action"]
    else:
        action = "buy"

    if "premium" in context.user_data.keys():
        premium = context.user_data["premium"]
    else:
        premium = "alloffers"

    if "currency" in context.user_data.keys():
        fiat = context.user_data["currency"]
    else:
        fiat = "eur"

    if "format" in context.user_data.keys():
        format = context.user_data["format"]
    else:
        format = 'text'

    price, result = print_orders(fiat, action, premium, exchange)
    msg = f"BTC price: {price} {fiat.upper()}\nBTC {action} offers:\n" + \
        f"{result}"

    if format == 'img':
        img = table_to_img(msg)
        update.message.reply_photo(img)
    else:
        update.message.reply_text(
            f'```{msg}```', parse_mode=ParseMode.MARKDOWN_V2)


def button(update: Update, context: CallbackContext):
    update.callback_query.answer()
    if update.callback_query.data in ['bisq', 'hodlhodl', 'robosats', 'all']:
        context.user_data["exchange"] = update.callback_query.data
        update.callback_query.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text="Ok, I will show you orders from " + context.user_data["exchange"] + " exchange(s)")
    elif update.callback_query.data in ['usd', 'eur']:
        context.user_data["currency"] = update.callback_query.data
        update.callback_query.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text="Currency is set to " + context.user_data["currency"])
    elif update.callback_query.data in ['buy', 'sell']:
        context.user_data["action"] = update.callback_query.data
        update.callback_query.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text="Got it!, I will show you " + context.user_data["action"] + " offers from other users")
    elif update.callback_query.data in ['1', '3', '5', '7', '9', '-1', '-3', '-5', '-7', '-9', 'alloffers']:
        context.user_data["premium"] = update.callback_query.data
        if context.user_data["premium"] == "alloffers":
            msg = "All right, I will show you all orders, regardless of price"
        elif int(context.user_data["premium"]) < 0:
            msg = "ok, I will set the price limit at " + \
                context.user_data["premium"] + "% below the market price."
        elif int(context.user_data["premium"]) > 0:
            msg = "ok, I will set the price limit at " + \
                context.user_data["premium"] + "% above the market price."
        update.callback_query.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text=msg)
    elif update.callback_query.data in ['img', 'text']:
        context.user_data["format"] = update.callback_query.data
        update.callback_query.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text="Ok, I will display the result as " + context.user_data["format"])
    elif update.callback_query.data in ['query']:
        update.callback_query.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text="Executing query. Please wait...")
        query_url(update, context)


def exchange_url(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup(keyboard_exchanges)
    update.message.reply_text(
        'Which exchange(s) do you want to use?', reply_markup=reply_markup)


def currency_url(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup(keyboard_currencies)
    update.message.reply_text(
        'In which currency do you want to pay or get paid?', reply_markup=reply_markup)


def premium_url(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup(keyboard_premium)
    update.message.reply_text(
        'Which premium are you willing to accept over or under market price?', reply_markup=reply_markup)


def action_url(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup(keyboard_actions)
    update.message.reply_text(
        'What do you want to do?', reply_markup=reply_markup)


def format_url(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup(keyboard_format)
    update.message.reply_text(
        'In which format do you want the result to be displayed?', reply_markup=reply_markup)


def unknown_text(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry I can't recognize what you said '%s'" % update.message.text)


def main() -> None:

    updater = Updater(config.TOKEN,
                      use_context=True)
    disp = updater.dispatcher
    disp.add_handler(CommandHandler('start', start))
    disp.add_handler(CommandHandler('help', help))
    disp.add_handler(CommandHandler('exchange', exchange_url))
    disp.add_handler(CommandHandler('currency', currency_url))
    disp.add_handler(CommandHandler('premium', premium_url))
    disp.add_handler(CommandHandler('action', action_url))
    disp.add_handler(CommandHandler('format', format_url))
    disp.add_handler(CommandHandler('query', query_url))

    disp.add_handler(CallbackQueryHandler(button))

    # Filters out unknown messages.
    disp.add_handler(MessageHandler(Filters.text, unknown_text))

    if mode == 'webhook':
        PORT = os.environ.get("PORT", config.DEFAULT_CONNECTION)
        logger.info("starting webhook")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=config.TOKEN,
                              webhook_url=config.APP_NAME + config.TOKEN)
    else:
        updater.start_polling()
        updater.idle()


if __name__ == '__main__':
    main()
