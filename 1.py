import datetime
x = '1641401711001'
print(datetime.datetime.utcfromtimestamp(int(x[:-3])))
a = [1, 3, 7, 5, 2, 6]
for i,p in enumerate(a):
        print(i,p)