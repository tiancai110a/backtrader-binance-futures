import os

PRODUCTION = "production"
DEVELOPMENT = "development"

COIN_TARGET = "BTC"
COIN_REFER = "USDT"

ENV = os.getenv("ENVIRONMENT", DEVELOPMENT)
DEBUG = True

# futures
BINANCE = {
  "key": "",
  "secret": ""
}

# spot
# BINANCE = {
#   "key": "DA9Rm9HKVsBQ8hXjbj6omu1vY7ZaAPWDZ8sF01lN89ih4AfVh629KqfLQa2UO4w5",
#   "secret": "VHfl78kWdS6VqPhhoh7S8BXyhzcDIwZixNDoFfNdJ9U6PhpKbUeWSpsCIlTbhh9v"
# }

TELEGRAM = {
  "channel": "<CHANEL ID>",
  "bot": "<BOT KEY HERE>"
}

print("ENV = ", ENV)