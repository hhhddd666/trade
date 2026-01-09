# utils/json_serializer.py
import json
from datetime import datetime, date

# 自定义JSON编码器，专门处理日期时间类型
class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # 如果是datetime/date类型，转成字符串
        if isinstance(obj, (datetime, date)):
            return obj.strftime("%Y-%m-%d %H:%M:%S")  # 转成"2024-05-20 14:30:00"格式
        # 其他类型按默认规则处理
        return super().default(obj)

# 封装序列化函数（傻瓜式调用）
def serialize_data(data):
    """把含datetime的数据转成JSON能识别的格式"""
    # 先转成JSON字符串，再转回字典（确保所有datetime都被处理）
    json_str = json.dumps(data, cls=DateTimeJSONEncoder)
    return json.loads(json_str)
