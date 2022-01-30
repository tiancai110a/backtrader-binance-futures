from turtle import up
import backtrader as bt
from matplotlib.pyplot import step
import numpy as np
import time
import config
import text
from strategies.base import StrategyBase
import math
from enum import Enum
import time
import traceback


class IncreaseMode(Enum):
        Exponent = 1
        Linear = 2
        Const = 3
        
def increase_mode_to_str(mode):
    if mode == IncreaseMode.Exponent:
        return "Exponent"
    elif mode == IncreaseMode.Linear:
        return "Linear"
    elif mode == IncreaseMode.Const:
        return "Const"
    else:
        return "Unknown"


# 以当前价格为中间价格，开出网格, 假如要开6个网格,往上三个,往下三个
# 在6个网格的范围内震荡,每升一个网格 ,就做空,每降一个网格, 就做多,但是做空或者做多 价格以上此交易的价格为准
# 离中心偏离的越多,买入得份额越多(马丁)
# 通过抓取的回测数据不断调整参数 格子大小,以及各自数量
class GridStrategy(StrategyBase):
    params = (
        # 均线参数设置15天，15日均线
        ('step', 30),
        ('grid_num', 10),
        ('increase_mode', IncreaseMode.Exponent),
        ('capital', 0),
        ('leverage', 1),
        ('init_price', 0),
    )

    def __init__(self):
        self.grid_execute = False #False 需要开启网格 True 正在网格中震荡
        self.lastPrice  = 0 # 用于计算当前价格和上一次的价格的差值 大于个格子就交易
        self.up  = 0  # 网格的上限, 如果当前价格超过这个价格,就清仓
        self.down  = 0 # 网格的下限, 如果当前价格低于这个价格,就清仓
        self.start_price  = 0 # 中心价格, 离这个价格越远就交易更多份额
        self.positionMap= [] # 记录持仓
        self.grid_count = 0 # 总共开网格次数
        self.grid_fail_count = 0 # 连续输掉的次数
        max_loss =  self.calc_max_loss()
        max_cap = self.calc_cap()
        self.unit = self.params.capital*self.params.leverage/max_cap/self.params.init_price
        self.init_value = self.broker.get_balance()
        
        
        real_max_capital = max_cap * self.params.init_price*self.unit/self.params.leverage
        real_max_loss = max_loss * self.params.init_price*self.unit/self.params.leverage
        print('中文:',self.unit)
        print('leverage:',self.params.leverage)
        print('init capital:',real_max_capital) # 加仓需要准备的资金
        print('max loss:',real_max_loss)        # 撤出之前最大亏损资金
        print('need prepare capital:',real_max_capital+real_max_loss) # 需要准备这些钱 才能在网格退出之前不爆仓
        print('init value:', self.init_value) # 初始资金
        print("mode",increase_mode_to_str(self.params.increase_mode))
      
    def regrid(self, price):
        self.grid_execute = True
        self.lastPrice = price
        self.up = price + self.params.step*self.params.grid_num/2
        self.down = price - self.params.step*self.params.grid_num/2
        self.start_price  = price
        self.positionMap = []
        self.grid_count = self.grid_count + 1
        self.init_value = self.broker.get_balance()
        print("==========regrid=========")
        print("upper",self.up)
        print("lower",self.down)
        print("start_price",self.start_price)
        



    def next(self):
        # for line in traceback.format_stack():
        #     print(line.strip())
        #print(1)

        #if config.ENV != config.PRODUCTION:  # 回测在数据最后清仓
        i =  list(range(0, len(self.datas)))
        for (d,j) in zip(self.datas,i):
            if len(d) == d.buflen()-2:
                self.close(d,exectype=bt.Order.Market)
            
        price = self.data.open[0]
        # 突破格子的上限和下限,清仓重新开启新一轮网格
        if price > self.up or price < self.down:
            self.clearPosition()
            
        #没有网格就开出网格,各种初始化
        if not self.grid_execute: 
            self.regrid(price)

        up = min(self.lastPrice + self.params.step,self.up)
        down = max(self.lastPrice - self.params.step,self.down)
        if price >=down and price <=up: #如果波动不超过一个格子,就什么都不干
            self.lastPrice =  self.lastPrice
        else:
            self.execute(price)

    def backtest_endup(self):
        i =  list(range(0, len(self.datas)))
        for (d,j) in zip(self.datas,i):
            if len(d) == d.buflen()-2:
                self.close(d,exectype=bt.Order.Market)
                
                
                
    def clearPosition(self):
        print("close" ,self.down,self.up)
        self.close()       
        self.grid_execute =False
        last_value =  self.broker.get_balance()
        if last_value[0] < self.init_value[0]:
            self.grid_fail_count = self.grid_fail_count + 1
            
        if self.grid_fail_count>3: # 连续三次亏损 直接退出
            print("+++++++++++>>>>>>>>>>>>>>>>>> stop loss")
            exit(0)
  
  
  
  
    def execute(self,price):
        direction = "buy"
        if self.lastPrice < price: # 升了一个level 就做空
            direction = "sell"
        else: # 降了一个level 就做多
            direction = "buy"
        
        measure = self.calcMeasure(direction,price)
        if direction =="buy":
            print("execute buy",measure,price)
            self.buy(size=self.unit*measure)
            self.lastPrice = price
        else:
            print("execute sell",measure,price,self.lastPrice)
            self.sell(size=self.unit*measure)
            self.lastPrice = price
            
            
            
            
    def stop(self):
        last_value =  self.broker.get_balance()
        if last_value[0] < self.init_value[0]:
            self.grid_fail_count = self.grid_fail_count + 1
            
        if self.grid_fail_count>3: # 连续三次亏损 直接退出
            exit(0)
            
        msg =  "step:{}, grid:{},value:{}, position.size:{} , position.price:{} unit:{},grid_count:{}".format(self.params.step,self.params.grid_num,self.broker.getvalue(), self.position.size,self.position.price,self.unit,self.grid_count)
        self.log(msg)
        text.writeline("done",msg)
        self.close() 
    def calcMeasure(self,direction,price):
        measure = 0
        for i, t in enumerate(self.positionMap):
            positionDirection = t['direction']
            positionPrice = t['price']
            positionMeasure = t['measure']
            
            if positionDirection == direction: # 相同方向的持仓全都不管
                continue
            up = min(price + 10,self.up)
            down = max(price - 10,self.down)
            levelPrice = t['price']
            if  levelPrice >= down and levelPrice <= up: # 以前的持仓在一个格子范围以内 就不清仓
                continue
            # 如果是买: 所有大于当前价格的做空统统清仓 如果是卖: 所有小于当前价格的做多统统清仓
            if (direction == "buy"  and positionPrice >= price+self.params.step-5) or (direction == "sell"  and positionPrice <= price-self.params.step+5):
                measure+=positionMeasure
                del self.positionMap[i]
                
        # 如果是开仓:
        if measure == 0:
            if self.params.increase_mode == IncreaseMode.Exponent:
                #measure =math.pow(float(2),abs(price - self.start_price)/self.params.step-1)
                measure =math.pow(float(2),abs(price - self.start_price)/self.params.step-1)
            if self.params.increase_mode == IncreaseMode.Linear:
                measure =abs(price - self.start_price)/self.params.step
            elif self.params.increase_mode == IncreaseMode.Const:
                measure = 1
            self.positionMap.append({'direction':direction,'measure':measure,'price':price})
        if measure ==0:
            measure =1
        return  measure
    
    # # 本金计算器
    def calc_cap(self):
        n = self.params.grid_num/2
        if self.params.increase_mode ==IncreaseMode.Exponent:
            return math.pow(2,float(n-1))-1
        elif self.params.increase_mode ==IncreaseMode.Linear:
            return (n-1)*n /2
        elif self.params.increase_mode ==IncreaseMode.Const: # v这是个普通的网格 没有马丁
            return n
        return 0  


    # 每次开单最大亏损
    def calc_max_loss(self):
            n = int(self.params.grid_num/2)
            grid = 0
            if self.params.increase_mode ==IncreaseMode.Exponent:
                for i in range(n):
                    grid +=  math.pow(float(2),float(i))*float(n-i-1) 
            elif self.params.increase_mode ==IncreaseMode.Linear:
                for i in range(n):
                    grid +=  i*(n-i) 
            elif self.params.increase_mode ==IncreaseMode.Const: # 这是个普通的网格 没有马丁
                grid = (1+ n)*n /2
            return grid
            
        