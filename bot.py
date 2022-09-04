#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is a telegram bot to get offers from p2p exchanges like
    bisq, hodlhodl and robosats"""

import logging
import i18n

from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

# Utils
from utils.utils import print_orders, table_to_img

import os

import config as config

MYDIR = os.path.dirname(__file__)
i18n.load_path.append(os.path.join(MYDIR, 'i18n'))
i18n.set('locale', 'en')
i18n.set('fallback', 'en')

# Emojis
EMOJI_ROBOT = u'\U0001F916'
EMOJI_PICTURE = '🏞'
EMOJI_TEXT = '🔠'
EMOJI_SELL = '➡️'
EMOJI_BUY = '⬅️'
EMOJI_ES = '🇪🇸'
EMOJI_EN = '🇺🇸'
EMOJI_ZH = '🇨🇳'
EMOJI_IT = '🇮🇹'

# read MODE env variable, fall back to 'polling' when undefined
mode = os.environ.get("MODE", config.DEFAULT_CONNECTION)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    if 'lang' not in context.user_data.keys():
        context.user_data["lang"] = 'en'
    update.message.reply_text(
        EMOJI_ROBOT + ' ' + i18n.t('menu.intro', locale=context.user_data["lang"]))
    action_url(update, context)


def language(update: Update, context: CallbackContext):
    if 'lang' not in context.user_data.keys():
        context.user_data["lang"] = 'en'
    keyboard_lang = [
        [
            InlineKeyboardButton(
                EMOJI_EN + ' ' + "English", callback_data='en'),
            InlineKeyboardButton(
                EMOJI_ES + ' ' + "Español", callback_data='es'),
            InlineKeyboardButton(
                EMOJI_IT + ' ' + "Italiano", callback_data='it'),
            InlineKeyboardButton(EMOJI_ZH + ' ' + "中文", callback_data='zh'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_lang)
    update.message.reply_text(i18n.t(
        'menu.language_select', locale=context.user_data["lang"]), reply_markup=reply_markup)


def help(update: Update, context: CallbackContext):
    if 'lang' not in context.user_data.keys():
        context.user_data["lang"] = 'en'
    keyboard_developer = [
        [InlineKeyboardButton(i18n.t('menu.developer', locale=context.user_data["lang"]),
                              url='https://t.me/fgbernal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_developer)

    text = i18n.t('menu.command_available',
                  locale=context.user_data["lang"]) + '\n'
    text = text + '/start - ' + \
        i18n.t('menu.command_start', locale=context.user_data["lang"]) + '\n'
    text = text + '/query - ' + \
        i18n.t('menu.command_query', locale=context.user_data["lang"]) + '\n'
    text = text + '/help - ' + \
        i18n.t('menu.command_help', locale=context.user_data["lang"]) + '\n'
    text = text + '/lang - ' + \
        i18n.t('menu.command_lang', locale=context.user_data["lang"]) + '\n'
    update.message.reply_text(text, reply_markup=reply_markup)


def run_query(update: Update, context: CallbackContext):
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
        if update.message is None:
            context.bot.send_photo(
                update.callback_query.from_user.id, photo=img)
        else:
            update.message.reply_photo(photo=img)
    else:
        if update.message is None:
            context.bot.send_message(update.callback_query.from_user.id,
                                     text=f'```{msg}```', parse_mode=ParseMode.MARKDOWN_V2)
        else:
            update.message.reply_text(
                text=f'```{msg}```', parse_mode=ParseMode.MARKDOWN_V2)


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if 'lang' not in context.user_data.keys():
        context.user_data["lang"] = 'en'
    if query.data in ['en', 'es', 'it', 'zh']:
        context.user_data["lang"] = query.data
        query.answer()
        query.edit_message_text(text=i18n.t(
            'menu.language_reply', locale=context.user_data["lang"]))
    elif query.data in ['buy', 'sell']:
        context.user_data["action"] = query.data
        query.answer()
        query.edit_message_text(text=i18n.t(
            'menu.action_reply', action=context.user_data["action"], locale=context.user_data["lang"]))
        exchange_url(update, context)
    elif query.data in ['bisq', 'hodlhodl', 'robosats', 'all']:
        context.user_data["exchange"] = query.data
        query.answer()
        query.edit_message_text(i18n.t(
            'menu.exchange_reply', exchange=context.user_data["exchange"], locale=context.user_data["lang"]))
        currency_url(update, context)
    elif query.data in ['usd', 'eur', 'jpy', 'gbp', 'chf', 'cny']:
        context.user_data["currency"] = query.data
        query.answer()
        query.edit_message_text(i18n.t(
            'menu.currency_reply', currency=context.user_data["currency"], locale=context.user_data["lang"]))
        premium_url(update, context)
    elif query.data in ['1', '3', '5', '7', '9', '-1', '-3', '-5', '-7', '-9', 'alloffers']:
        context.user_data["premium"] = query.data
        if context.user_data["premium"] == "alloffers":
            msg = i18n.t('menu.premium_all_reply',
                         locale=context.user_data["lang"])
        elif int(context.user_data["premium"]) < 0:
            msg = i18n.t('menu.premium_low_reply',
                         premium=context.user_data["premium"], locale=context.user_data["lang"])
        elif int(context.user_data["premium"]) > 0:
            msg = i18n.t('menu.premium_high_reply',
                         premium=context.user_data["premium"], locale=context.user_data["lang"])
        query.answer()
        query.edit_message_text(msg)
        format_url(update, context)
    elif query.data in ['img', 'text']:
        context.user_data["format"] = query.data
        query.answer()
        query.edit_message_text(i18n.t(
            'menu.format_reply', format=context.user_data["format"], locale=context.user_data["lang"]))
        query_url(update, context)
    elif query.data in ['query']:
        query.edit_message_text(text=i18n.t(
            'menu.searching', locale=context.user_data["lang"]))
        query.answer()
        run_query(update, context)


def exchange_url(update: Update, context: CallbackContext):
    keyboard_exchanges = [
        [
            InlineKeyboardButton("Bisq", callback_data='bisq'),
            InlineKeyboardButton("HodlHodl", callback_data='hodlhodl'),
            InlineKeyboardButton("Robosats", callback_data='robosats'),
            InlineKeyboardButton("All", callback_data='all')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_exchanges)
    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                             text=i18n.t('menu.exchange_question', locale=context.user_data["lang"]), reply_markup=reply_markup)


def currency_url(update: Update, context: CallbackContext):
    keyboard_currencies = [
        [
            InlineKeyboardButton("($) USD", callback_data='usd'),
            InlineKeyboardButton("(€) EUR", callback_data='eur'),
            InlineKeyboardButton("(¥) JPY", callback_data='jpy')
        ],
        [
            InlineKeyboardButton("(£) GBP", callback_data='gbp'),
            InlineKeyboardButton("(fr) CHF", callback_data='chf'),
            InlineKeyboardButton("(¥) CNY", callback_data='cny')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_currencies)
    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                             text=i18n.t('menu.currency_question', locale=context.user_data["lang"]), reply_markup=reply_markup)


def premium_url(update: Update, context: CallbackContext):
    keyboard_premium = [
        [
            InlineKeyboardButton("-9%", callback_data='-9'),
            InlineKeyboardButton("-7%", callback_data='-7'),
            InlineKeyboardButton("-5%", callback_data='-5'),
            InlineKeyboardButton("-3%", callback_data='-3'),
            InlineKeyboardButton("-1%", callback_data='-1')
        ],
        [
            InlineKeyboardButton(i18n.t(
                'menu.show_all', locale=context.user_data["lang"]), callback_data='alloffers'),
        ],
        [
            InlineKeyboardButton("0%", callback_data='0'),
            InlineKeyboardButton("1%", callback_data='1'),
            InlineKeyboardButton("3%", callback_data='3'),
            InlineKeyboardButton("5%", callback_data='5'),
            InlineKeyboardButton("7%", callback_data='7'),
            InlineKeyboardButton("9%", callback_data='9')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_premium)
    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                             text=i18n.t('menu.premium_question', locale=context.user_data["lang"]), reply_markup=reply_markup)


def action_url(update: Update, context: CallbackContext):
    keyboard_actions = [
        [
            InlineKeyboardButton(EMOJI_SELL + ' ' + i18n.t('menu.buy',
                                 locale=context.user_data["lang"]), callback_data='sell'),
            InlineKeyboardButton(EMOJI_BUY + ' ' + i18n.t('menu.sell',
                                 locale=context.user_data["lang"]), callback_data='buy')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_actions)
    update.message.reply_text(
        i18n.t('menu.action_question', locale=context.user_data["lang"]), reply_markup=reply_markup)


def format_url(update: Update, context: CallbackContext):
    keyboard_format = [
        [
            InlineKeyboardButton(EMOJI_TEXT + ' ' + i18n.t('menu.plain_text',
                                 locale=context.user_data["lang"]), callback_data='text'),
            InlineKeyboardButton(EMOJI_PICTURE + ' ' + i18n.t('menu.image',
                                 locale=context.user_data["lang"]), callback_data='img')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_format)
    if update.message is None:
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                 text=i18n.t('menu.format_question', locale=context.user_data["lang"]), reply_markup=reply_markup)
    else:
        update.message.reply_text(text=i18n.t(
            'menu.format_question', locale=context.user_data["lang"]), reply_markup=reply_markup)


def query_url(update: Update, context: CallbackContext):
    keyboard_runquery = [
        [InlineKeyboardButton(i18n.t(
            'menu.start_search', locale=context.user_data["lang"]), callback_data='query')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_runquery)
    if update.message is None:
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                 text=i18n.t('menu.run_query', locale=context.user_data["lang"]), reply_markup=reply_markup)
    else:
        update.message.reply_text(text=i18n.t(
            'menu.run_query', locale=context.user_data["lang"]), reply_markup=reply_markup)


def unknown_text(update: Update, context: CallbackContext):
    update.message.reply_text(
        i18n.t('menu.not_recognized', message=update.message.text, locale=context.user_data["lang"]))


def main() -> None:

    updater = Updater(config.TOKEN,
                      use_context=True)
    disp = updater.dispatcher
    disp.add_handler(CommandHandler('start', start))
    disp.add_handler(CommandHandler('help', help))
    disp.add_handler(CommandHandler('query', run_query))
    disp.add_handler(CommandHandler('lang', language))

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
