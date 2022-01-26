import backtrader as bt
import datetime
import time
trade_time =datetime.datetime.strptime('2022-01-22T18:32:33.639Z', '%Y-%m-%dT%H:%M:%S.%fZ')
print( bt.date2num(trade_time))
x = '1641401711001'
print(datetime.datetime.utcfromtimestamp(int(x[:-3])))
a = [1, 3, 7, 5, 2, 6]
for i,p in enumerate(a):
        print(i,p)