#!/usr/bin/env python3

import time
import backtrader as bt
import datetime as dt
import yaml
import numpy as np
from ccxtbt import CCXTStore
from config import BINANCE, ENV, PRODUCTION, COIN_TARGET, COIN_REFER, DEBUG

from dataset.dataset import CustomDataset
from sizer.percent import FullMoney
from strategies.BasicRSI import BasicRSI
from utils import print_trade_analysis, print_sqn, send_telegram_message
import backtrader.feeds as btfeeds
import sys
import codecs

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

import toolkit as tk
class TestStrategy1(bt.Strategy):
    params = (
        # 均线参数设置15天，15日均线
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.date(0)
        #print("=====>>>",self.datas[0].datetime.date(0))
        print('%s, %s' % (dt, txt))

    def __init__(self):
        # 保存收盘价的引用
        self.dataclose = self.datas[0].close
        # 跟踪挂单
        self.order = None
        # 买入价格和手续费
        self.buyprice = None
        self.buycomm = None
        # 加入均线指标
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)

        # 绘制图形时候用到的指标
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25,subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)


    # 订单状态通知，买入卖出都是下单
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            return

        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '已买入, 价格: %.2f, 费用: %.2f, 佣金 %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('已卖出, 价格: %.2f, 费用: %.2f, 佣金 %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        # 其他状态记录为：无挂起订单
        self.order = None

    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('交易利润, 毛利润 %.2f, 净利润 %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # 记录收盘价
       # self.log('Close, %.2f' % self.dataclose[0])

        # 如果有订单正在挂起，不操作
        if self.order:
            return
        # 如果没有持仓则买入
        if not self.position:
            # 今天的收盘价在均线价格之上 
            if self.dataclose[0] > self.sma[0]: 
                # 买入
                self.log('买入单, %.2f' % self.dataclose[0])
                    # 跟踪订单避免重复
                self.order = self.buy(size=1)
        else:
            # 如果已经持仓，收盘价在均线价格之下
            if self.dataclose[0] < self.sma[0]:
                # 全部卖出
                self.log('卖出单, %.2f' % self.dataclose[0])
                # 跟踪订单避免重复
                self.order = self.buy(size=1)

# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt, txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.datadatetime = self.datas[0].datetime
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume
         # 加入均线指标
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0])

        # 绘制图形时候用到的指标
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25,subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)
       

    def next(self):
        #self.order = self.long()
        # Simply log the closing price of the series from the reference
        self.log('=====>>>>time {},Close {} Open {} high {},low {} volumn {}'.format(self.datadatetime[0], self.dataclose[0],self.dataopen[0],self.datahigh[0],self.datalow[0],self.datavolume[0]))



def main():
    cerebro = bt.Cerebro(stdstats=True)
    print("====>>>>",BINANCE.get("key"),BINANCE.get("secret"))
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
                          sandbox=False)

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
        data = btfeeds.GenericCSVData(
        dataname="1.txt",
        datetime=1,
        open=13,
        high=14,
        low=15,
        close=7, # 确认
        volume=16,
        openinterest=-1,
        timeframe=bt.TimeFrame.Ticks, 
        compression=1,
    )
        cerebro.adddata(data)
        # data = cerebro.resampledata(data,
        #                         timeframe=bt.TimeFrame.Ticks,
        #                         compression=1)

        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.0004)
        cerebro.addsizer(FullMoney)

    #bt.observers.BuySell = MyBuySell
#    Analyzers to evaluate trades and strategies
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    # Include Strategy
    cerebro.addstrategy(TestStrategy1)
    
    # 引擎运行前打印期出资金
    print('组合期初资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    # 引擎运行后打期末资金
    print('组合期末资金: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()



if __name__ == "__main__":
    perc_levels = [x for x in np.arange(
                1 + 0.005 * 5,
                # 1/2  arange 
                1 - 0.005 * 5 - 0.005/2,
                -0.005)]
    print(perc_levels)
    try:
        main()
    except KeyboardInterrupt:
        print("finished.")
        time = dt.datetime.now().strftime("%d-%m-%y %H:%M")
        send_telegram_message("Bot finished by user at %s" % time)
    except Exception as err:
        send_telegram_message("Bot finished with error: %s" % err)
        print("Finished with error: ", err)
        raise
