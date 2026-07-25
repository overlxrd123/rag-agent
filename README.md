# 房屋数据 Agent — 手写 + LangChain 双版本

同一套工具（ETL管道 / 数据库查询 / 报告生成），用原生 Python 和 LangChain 框架分别实现。

## 双版本对比

| | 手写版 `agent.py` | LangChain 版 `langchain_agent.py` |
|------|------|------|
| 决策循环 | 自己写 for step in range(5) | LangGraph 自动维护 |
| 工具定义 | TOOL_LIST 文字描述 | @tool 装饰器 |
| LLM | DeepSeek V4 Pro | 同上 |
| 代码量 | 126 行 | 74 行 |

## 工具库
- `tool_run_etl` — 爬取链家最新房源并更新数据库
- `tool_query_district` — 查某个区的房源统计
- `tool_get_report` — 获取最新分析报告

## 技术栈
`Python` `LangChain` `DeepSeek API` `ETL` `SQLite` `Agent`

## 运行
```bash
chcp 65001
set PYTHONUTF8=1
set DEEPSEEK_KEY=sk-xxx
python langchain_agent.py
```
