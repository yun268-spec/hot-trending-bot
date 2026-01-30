name: 每小时热点推送

on:
  schedule:
    - cron: '0 * * * *'  # 每小时整点运行
  workflow_dispatch:      # 允许手动触发

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: 检出代码
      uses: actions/checkout@v4
    
    - name: 设置Python
      uses: actions/setup-python@v5  # 顺带升级到v5，更稳定
      with:
        python-version: '3.10'
    
    - name: 安装依赖包
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: 执行热点抓取
      env:
        FEISHU_WEBHOOK: ${{ secrets.FEISHU_WEBHOOK }}
        TIANAPI_KEY: ${{ secrets.TIANAPI_KEY }}
      run: python fetch_hot.py
    
    # 可选：如果失败保存日志（使用v4版本）
    - name: 上传日志（失败时）
      if: failure()
      uses: actions/upload-artifact@v4  # ← 关键修改：v3 → v4
      with:
        name: error-log
        path: |
          *.log
          hot_result.txt
