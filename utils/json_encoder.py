# utils/json_encoder.py
import json
from datetime import datetime, date

class DateTimeJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime/date类型"""
    def default(self, obj):
        # 如果是datetime或date类型，转成字符串
        if isinstance(obj, (datetime, date)):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        # 其他类型按默认规则处理
        return super().default(obj)

def serialize_with_datetime(data):
    """
    封装序列化函数：把含datetime的数据转成JSON可序列化的格式
    :param data: 包含datetime的字典/列表等数据
    :return: 序列化后的普通字典（无datetime类型）
    """
    # 先转成JSON字符串（处理datetime），再转回字典
    json_str = json.dumps(data, cls=DateTimeJSONEncoder)
    return json.loads(json_str)
