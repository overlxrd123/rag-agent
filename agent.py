"""
Multi-Tool Agent：把 ETL 管道 + 数据查询 升级为语音驱动的智能助手
"""

import requests, json, os, subprocess, sqlite3

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "你的Key放这里")

# ===== 工具库 =====
def tool_run_etl():
    """工具1：执行 ETL 管道，爬取最新数据并更新数据库"""
    result = subprocess.run(["python", r"D:\Projects\etl_pipeline\etl.py"],
                            capture_output=True, text=True, timeout=60)
    db = sqlite3.connect(r"D:\Projects\etl_pipeline\rental.db")
    total = db.execute("SELECT COUNT(*) FROM rental_history").fetchone()[0]
    db.close()
    return {"status": "完成", "total_rows": total, "output": result.stdout[-500:]}

def tool_query_district(district: str):
    """工具2：查某个区的房源统计"""
    db = sqlite3.connect(r"D:\Projects\etl_pipeline\rental.db")
    cur = db.execute("""
        SELECT district, COUNT(*) as cnt, ROUND(AVG(price_yuan),0) as avg_price
        FROM rental_history WHERE district LIKE ? GROUP BY district
    """, [f"%{district}%"])
    rows = [{"district": r[0], "count": r[1], "avg_price": r[2]} for r in cur.fetchall()]
    db.close()
    return rows

def tool_get_report():
    """工具3：生成并返回最新 HTML 报告路径"""
    latest = r"D:\Projects\etl_pipeline\latest_report.html"
    if os.path.exists(latest):
        import time
        mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(latest)))
        return {"path": latest, "updated": mtime}
    return {"error": "暂无报告，请先执行 ETL"}

TOOL_LIST = """
可用工具：
1. tool_run_etl — 抓取链家最新租房数据并更新数据库（无需参数）
2. tool_query_district — 查某个区的房源统计（参数：区名，如"海淀"）
3. tool_get_report — 获取最新 HTML 报告路径（无需参数）
"""

# ===== LLM 调用 =====
def call_llm(system_prompt, user_message):
    r = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-v4-pro", "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ], "temperature": 0},
        timeout=30
    )
    resp = r.json()
    if "choices" not in resp:
        print(f"API错误: {resp}")
        return json.dumps({"action": "final", "summary": f"API调用失败: {resp}"})
    return resp["choices"][0]["message"]["content"]

# ===== Agent 多步执行 =====
def agent_run(user_input: str):
    print(f"👤 用户: {user_input}")
    history = []

    for step in range(5):
        history_text = ""
        for h in history:
            history_text += f"第{h['step']}步: 调用 {h['action']} 参数={h['arg']} → {str(h['result'])[:300]}\n"

        decision_prompt = f"""你是智能房屋数据分析助手。{TOOL_LIST}
=== 已执行历史 ===
{history_text}
=== 用户需求 ===
{user_input}
请决定下一步：如果数据够回答用户了，回复 {{"action":"final","summary":"用中文总结分析结果"}}；否则回复 {{"action":"工具名","arg":"参数或null"}}
只输出JSON。"""

        decision = call_llm(decision_prompt, user_input)
        print(f"🧠 第{step+1}步: {decision[:150]}")

        try:
            d = json.loads(decision)
        except:
            continue

        if d.get("action") == "final" or "summary" in d:
            return d.get("summary", "分析完成")

        action = d.get("action")
        arg = d.get("arg")
        if arg == "null":
            arg = None

        result = {}
        if action == "tool_run_etl":
            result = tool_run_etl()
        elif action == "tool_query_district" and arg:
            result = tool_query_district(arg)
        elif action == "tool_get_report":
            result = tool_get_report()
        else:
            continue

        print(f"📊 结果: {str(result)[:200]}")
        history.append({"step": step+1, "action": action, "arg": arg, "result": result})

    return "Agent 尝试多次未能完成分析，请稍后重试。"

# ===== 交互模式 =====
if __name__ == "__main__":
    if DEEPSEEK_KEY == "你的Key放这里":
        print("请设置 DEEPSEEK_KEY 环境变量")
        exit()

    print("=" * 50)
    print("🏠 房屋数据 Agent 已启动")
    print("试试: 更新数据 / 查海淀房源 / 最新报告")
    print("quit 退出")
    print("=" * 50)

    while True:
        ui = input("\n👤 你: ").strip()
        if ui.lower() in ['quit', 'exit', '退出', 'q']:
            break
        if not ui:
            continue
        print(f"🤖 Agent: {agent_run(ui)}")
