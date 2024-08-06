from xtquant import xtdatacenter as xtdc
xtdc.set_token('')

print('xtdc.init')
xtdc.init() # 初始化行情模块，加载合约数据，会需要大约十几秒的时间
print('done')
# 为其他进程的xtdata提供服务时启动server，单进程使用不需要
print('xtdc.listen')
listen_addr = xtdc.listen(port = 58610)
print(f'done, listen_addr:{listen_addr}')
from xtquant import xtdata
print('running')
xtdata.run() #循环，维持程序运行