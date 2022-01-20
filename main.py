#!/usr/bin/env python3

import time
import backtrader as bt
import datetime as dt
import yaml
import os
import gc

import numpy as np
from ccxtbt import CCXTStore
from config import BINANCE, ENV, PRODUCTION, COIN_TARGET, COIN_REFER, DEBUG

from dataset.dataset import CustomDataset
from sizer.percent import FullMoney
from strategies.GridStrategy import GridStrategy
from utils import print_trade_analysis, print_sqn, send_telegram_message
import backtrader.feeds as btfeeds
import sys
import codecs

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

import toolkit as tk

def main():
    cerebro = bt.Cerebro(stdstats=True)
    if ENV == PRODUCTION:  # Live trading with Binance
        broker_config = {
            'apiKey': BINANCE.get("key"),
            'secret': BINANCE.get("secret"),
            'timeout': 5000,
            'verbose': False,
            'nonce': lambda: str(int(time.time() * 1000)),
            'enableRateLimit': True,
        }

        store = CCXTStore(exchange='binanceusdm', currency=COIN_REFER, config=broker_config, retries=5, debug=False,
                          sandbox=True)

        broker_mapping = {
            'order_types': {
                bt.Order.Market: 'market',
                bt.Order.Limit: 'limit',
                bt.Order.Stop: 'stop-loss',
                bt.Order.StopLimit: 'stop limit'
            },
            'mappings': {
                'closed_order': {
                    'key': 'status',
                    'value': 'closed'
                },
                'canceled_order': {
                    'key': 'status',
                    'value': 'canceled'
                }
            }
        }
        broker = store.getbroker(broker_mapping=broker_mapping)
        cerebro.setbroker(broker)

        hist_start_date = dt.datetime.utcnow() - dt.timedelta(minutes=3000)
        data = store.getdata(
                    dataname=f'{"BTCUSDT"}',
                    name=f'{"BTCUSDT"}',
                    timeframe=bt.TimeFrame.Minutes,
                    fromdate=hist_start_date,
                    compression=1,
                    ohlcv_limit=10000
                )

        cerebro.adddata(data)
        # data = cerebro.resampledata(data,
        #                         timeframe=bt.TimeFrame.Ticks,
        #                         compression=1)



        cerebro.broker.setcommission(commission=0.0004)
        cerebro.addsizer(FullMoney)
    else:  # Backtesting with CSV file
         # Include Strategy
        #cerebro.addstrategy(GridStrategy,step= 90,grid_num=10)
        cerebro.addstrategy(GridStrategy)
        # strats = cerebro.optstrategy(
        # GridStrategy,
        # step=range(30, 100,10),
        # grid_num=range(6, 12, 2),
        # )
        data = btfeeds.GenericCSVData(
        dataname="data_btc_01-10-13",
        #dataname="1.txt",
        datetime=1,
        open=13,
        high=14,
        low=15,
        close=7, # 确认
        volume=16,
        timeframe=bt.TimeFrame.Ticks, 
        compression=1,
    )
        cerebro.adddata(data)
        # 创建交易数据集
    
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.00037)
        cerebro.addsizer(FullMoney)


   
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.00037)
    cerebro.addsizer(FullMoney)
    
    # 引擎运行前打印期出资金
    print('组合期初资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run(maxcpus=1)
    # 引擎运行后打期末资金
    print('组合期末资金: %.2f' % cerebro.broker.getvalue())
    #cerebro.plot()




if __name__ == "__main__":
    perc_levels = [x for x in np.arange(
                1 + 0.005 * 5,
                # 1/2  arange 
                1 - 0.005 * 5 - 0.005/2,
                -0.005)]
    print(perc_levels)
    try:
        main()
        gc.collect

    except KeyboardInterrupt:
        print("finished.")
        time = dt.datetime.now().strftime("%d-%m-%y %H:%M")
        send_telegram_message("Bot finished by user at %s" % time)
    except Exception as err:
        send_telegram_message("Bot finished with error: %s" % err)
        print("Finished with error: ", err)
        raise
