import logging


#穿件日志记录器
logger = logging.getLogger('django')
#输出日志
logger.debug('测试logging模块的debug')
logger.info('测试logging模块的info')
logger.error('测试logging模块的error')