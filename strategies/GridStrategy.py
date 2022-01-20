from turtle import up
import backtrader as bt
import numpy as np
import time
from strategies.base import StrategyBase
class GridStrategy(StrategyBase):
    params = (
        # 均线参数设置15天，15日均线
        ('step', 30),
        ('grid_num', 10),
    )

    def __init__(self):
        self.grid_execute = False
        self.up  = 0 
        self.down  = 0 
        self.mid  = 0
        self.lastPrice  = 0
        self.grid= []
      
        



    def next(self):
        i =  list(range(0, len(self.datas)))
        for (d,j) in zip(self.datas,i):
            if len(d) == d.buflen()-2:
                self.close(d,exectype=bt.Order.Market)
        price = self.data.open[0]
        if price > self.up or price < self.down:
            #print("before regrid",price ,self.down,self.up,"position",self.position)
            self.close()
            #print("after regrid",price ,self.down,self.up,"position",self.position)
            self.grid_execute =False
            
        if not self.grid_execute: #没有网格就开出网格
            self.grid_execute = True
            lower = price - self.params.step*self.params.grid_num/2
            upper = price + self.params.step*self.params.grid_num/2
            self.grid = [x for x in np.arange(lower,upper,self.params.step)]
            self.down = self.grid[0]
            self.up = self.grid[-1]
            for p in self.grid:
                if price<=p:
                    self.lastPrice = p
                    break
           
            
        up = min(self.lastPrice + 30,self.up)
        down = max(self.lastPrice - 30,self.down)
        if price >=down and price <=up:
            self.lastPrice = self.lastPrice
        else:
            # 从下往上求 或者从上往下求
            levelPrice = 0
            if price < down:
                reverseGrid = self.grid[::-1]
                for i,p in enumerate(reverseGrid):
                    if price>p:
                        levelPrice = reverseGrid[i-1]
                        break
            if price > up:
                for i,p in enumerate(self.grid):
                    if price<p:
                        levelPrice = self.grid[i-1]
                        break
            self.execute(price,levelPrice)
  
    def execute(self,price,levelprice):
        mid  =  self.grid[int(self.params.grid_num/2)]
        measure = abs(levelprice - mid)/self.params.step
        if self.lastPrice == levelprice:
            return # 啥也不干
        elif self.lastPrice < levelprice: # 升了一个level 就做空
            #print("=====>>>execute time:{} currentprice:{}, levelprice:{}, lastprice:{}, levelArray:{}".format(self.datas[0].datetime.datetime(0),price,levelprice,self.lastPrice,self.grid))
            self.sell(size=0.1*measure)
            self.lastPrice =levelprice
        else: # 降了一个level 就做多
            #print("=====>>>execute time:{} currentprice:{}, levelprice:{}, lastprice:{} levelArray:{}".format(self.datas[0].datetime.datetime(0),price,levelprice,self.lastPrice,self.grid))
            self.buy(size=0.1*measure)
            self.lastPrice =levelprice
    def stop(self):
        self.log("=================>>>>>>>>stop<<<<<<<<<<================= step:{}, grid:{},value:{}, position.size:{} , position.price:{}".format(self.params.step,self.params.grid_num,self.broker.getvalue(), self.position.size,self.position.price))
        self.close() 