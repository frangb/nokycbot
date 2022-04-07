# nokyc bot
A telegram bot to list all current [Bisq](https://bisq.network), [HodlHodl](https://hodlhodl.com) and [Robosats](https://unsafe.robosats.com) offers

# Instructions
- Create a `config.py` file in the same folder, with the following content

```
# -*- coding: utf-8 -*-
# Your telegram bot token
TOKEN = '<YOUR_TELEGRAM_BOT_TOKEN>'
# Port where your Tor proxy is running
TOR_PORT = '<YOUR_TOR_PORT' # it is usually 9050 or 9051
# Payment methods to avoid. In lower case.
avoid_methods = ["monero", "ripple", "litecoin"]

# In case you're using webhooks, fill up the following info
APP_NAME = '<your_app_name>'
```

- For development and testing, set your environment variable `MODE` to `'polling'`. For production, set the variable to `'webhook'`

- Run the bot with `python3 bot.py`
  

