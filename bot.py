import configparser
import ccxt
from os import path
import logging as log
from supertrend import Worker
import time
import logging
import os

class Bot():

    def __init__(self):
        config_parser = configparser.ConfigParser()
        settings_path = path.abspath("settings.conf")
        config_parser.read(settings_path)

        workers = []

        for config_section in config_parser.sections():

            if not (config_section in ccxt.exchanges):
                continue
            
            #1st worker param
            config = config_parser[config_section]

            exchange_cls = getattr(ccxt, config_section)
            #2nd worker param
            exchange = exchange_cls({
                'apiKey': config['apikey'],
                'secret': config['apisecret']
            })
          
            #3rd worker param (each item)
            markets = []
            for market in exchange.loadMarkets():
                watchlist = config['wachtlist'].split(',')
                currency = market.split('/')[0]
                if(market.endswith('/'+ config['basecurrency']) and currency in watchlist):
                    markets.append(market)

            #4th worker param (each item)
            tickers = []
            if (exchange.has['fetchTickers']):
                tickers = exchange.fetch_tickers(markets)
            else:
                for market in markets:
                    ticker = exchange.fetch_ticker(market)
                    tickers.append(ticker)

            #5th worker param (each item)
            balance = exchange.fetch_balance()
            free_balance = balance[config['basecurrency']]['free']
            size = (free_balance *  min(1, float(config['percentageatrisk']))) / len(markets)

            polling_interval = config['pollingintervalinseconds']
            base_currency = config['basecurrency']
            bars_timeframe = config['barstimeframe']
            console_output = config.getboolean('consoleoutput')
            dataframe_logging = config.getboolean('dataframelogging')
            file_output = config.getboolean('fileoutput')

            for market in markets:
                ticker = tickers[market]['info']['lastPrice']
                bot_id = config_section.lower() + "_" + market.replace("/", "_").lower()
                logger = self.mylogger('supertrend', bot_id)
                workers.append(Worker(console_output, dataframe_logging, file_output, polling_interval, base_currency, bars_timeframe, logger, bot_id, config_section, exchange, market, size))

        
        self.workers = workers
     
    def mylogger(self, strategy, bot_id):
        logger = logging.getLogger(strategy)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(threadName)s:%(name)s] %(asctime)s %(levelname)s:\t%(message)s')
        file_handler = logging.FileHandler(os.path.join(bot_id + ".log"), 'a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def run(self):
        for worker in self.workers:
            worker.start()
            time.sleep(5)

Bot().run()