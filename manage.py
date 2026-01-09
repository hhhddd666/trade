#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import hashlib

# 保存原始的 md5 函数
original_md5 = hashlib.md5

# 定义补丁函数：过滤掉 usedforsecurity 参数
def patched_md5(*args, **kwargs):
    # 移除非法的 usedforsecurity 参数（如果存在）
    kwargs.pop('usedforsecurity', None)
    # 调用原始 md5 函数，只传递合法参数
    return original_md5(*args, **kwargs)

# 替换全局的 md5 函数
hashlib.md5 = patched_md5

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
