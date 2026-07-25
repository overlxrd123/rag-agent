"""
LangChain 版 Agent — 同一套工具，用框架重写
"""
import os, sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
import subprocess, sqlite3
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "你的Key放这里")

# ===== LLM =====
llm = ChatOpenAI(
    model="deepseek-v4-pro",
    api_key=DEEPSEEK_KEY,
    base_url="https://api.deepseek.com/v1",
    temperature=0,
)

# ===== 工具定义 — 跟手写版完全一样 =====
@tool
def tool_run_etl(query: str = "") -> str:
    """抓取链家最新租房数据并更新数据库。调用此工具不需要参数。"""
    result = subprocess.run(
        ["python", r"D:\Projects\etl_pipeline\etl.py"],
        capture_output=True, text=True, timeout=60, encoding="gbk"
    )
    db = sqlite3.connect(r"D:\Projects\etl_pipeline\rental.db")
    total = db.execute("SELECT COUNT(*) FROM rental_history").fetchone()[0]
    db.close()
    return f"ETL完成。数据库累计{total}条房源"

@tool
def tool_query_district(district: str) -> str:
    """查询某个区的房源统计。参数 district 是区名，如'海淀'或'朝阳'。"""
    db = sqlite3.connect(r"D:\Projects\etl_pipeline\rental.db")
    cur = db.execute(
        "SELECT district, COUNT(*) as cnt, ROUND(AVG(price_yuan),0) as avg_price FROM rental_history WHERE district LIKE ? GROUP BY district",
        [f"%{district}%"]
    )
    rows = [f"{r[0]}: {r[1]}套, 均价{r[2]}元/月" for r in cur.fetchall()]
    db.close()
    return "\n".join(rows) if rows else f"未找到{district}的房源"

@tool
def tool_get_report(query: str = "") -> str:
    """获取最新 HTML 报告的生成时间和路径。调用此工具不需要参数。"""
    path = r"D:\Projects\etl_pipeline\latest_report.html"
    if os.path.exists(path):
        import time
        mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(path)))
        return f"最新报告: {path}，生成时间: {mtime}"
    return "暂无报告，请先执行 tool_run_etl"

# ===== 创建 Agent =====
tools = [tool_run_etl, tool_query_district, tool_get_report]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是智能房屋数据分析助手。用中文回复。先思考需要什么工具，调完工具根据结果回答。",
)

# ===== 交互模式 =====
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 LangChain Agent 已启动")
    print("试试: 更新数据 / 查海淀房源 / 最新报告")
    print("quit 退出")
    print("=" * 50)

    while True:
        ui = input("\n👤 你: ").strip()
        if ui.lower() in ['quit', 'exit', '退出', 'q']:
            break
        if not ui:
            continue
        try:
            result = agent.invoke({"messages": [{"role": "user", "content": ui}]})["messages"][-1].content
            print(f"🤖 Agent: {result}")
        except Exception as e:
            print(f"❌ 错误: {e}")
