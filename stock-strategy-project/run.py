#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from main import main
    main()
