import streamlit as st
import sqlite3
import pandas as pd

# 设置页面标题
st.set_page_config(page_title="舞蹈学术信息看板", layout="wide")

st.title("舞蹈学术信息看板")
st.markdown("聚合演出资讯、学术讲座与艺术活动，按地点整理近期信息。")

DISPLAY_SECTIONS = ["演出资讯", "学术讲座/研讨会", "艺术活动"]

PERFORMANCE_KEYWORDS = [
    "舞剧", "演出", "剧目", "购票", "开票", "剧场", "剧院", "专场",
    "上演", "巡演", "芭蕾", "音乐剧", "舞蹈诗剧", "校内演出"
]

ACADEMIC_KEYWORDS = [
    "讲座", "研讨", "论坛", "会议", "学术", "报告", " symposium", "seminar"
]

ACTIVITY_KEYWORDS = [
    "艺术节", "活动", "工作坊", "大师课", "公开课", "导赏", "沙龙",
    "展览", "招募", "体验", "美育", "营", "开放日"
]

def clean_value(value, fallback="待公布"):
    if pd.isna(value) or str(value).strip() == "":
        return fallback
    return str(value)

def classify_section(row):
    category = clean_value(row.get("category"), "")
    text = " ".join([
        clean_value(row.get("title"), ""),
        clean_value(row.get("summary"), ""),
        category
    ]).lower()

    if category == "舞剧信息" or any(keyword.lower() in text for keyword in PERFORMANCE_KEYWORDS):
        return "演出资讯"

    if category == "学术讲座" or any(keyword.lower() in text for keyword in ACADEMIC_KEYWORDS):
        return "学术讲座/研讨会"

    if category == "展演资讯" or any(keyword.lower() in text for keyword in ACTIVITY_KEYWORDS):
        return "艺术活动"

    return "艺术活动"

def prepare_display_data(data):
    display_df = data.copy()
    display_df["首页板块"] = display_df.apply(classify_section, axis=1)
    display_df["名称"] = display_df["title"].apply(lambda value: clean_value(value, "未命名信息"))
    display_df["时间"] = display_df["date"].apply(clean_value)
    display_df["地点"] = display_df["location"].apply(clean_value)
    return display_df.sort_values(["地点", "时间", "名称"], na_position="last")

# 连接数据库
def load_data():
    conn = sqlite3.connect('academic_events.db')
    # 查询所有数据并按时间倒序排列
    df = pd.read_sql_query("SELECT * FROM academic_events ORDER BY date DESC", conn)
    conn.close()
    return df

# 读取数据
try:
    df = load_data()

    if df.empty:
        st.info("暂无数据。请先运行采集脚本，或检查 GitHub Actions 是否成功写入 academic_events.db。")
        st.stop()

    search_term = st.text_input("搜索关键词")
    if search_term:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

    display_df = prepare_display_data(df)

    if display_df.empty:
        st.write("当前筛选条件下暂无数据。")
        st.stop()

    metric_cols = st.columns(3)
    for col, section in zip(metric_cols, DISPLAY_SECTIONS):
        col.metric(section, int((display_df["首页板块"] == section).sum()))

    st.divider()

    for section in DISPLAY_SECTIONS:
        section_df = display_df[display_df["首页板块"] == section][["名称", "时间", "地点"]]
        st.subheader(section)

        if section_df.empty:
            st.caption("暂无相关信息")
            continue

        st.dataframe(
            section_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "名称": st.column_config.TextColumn("名称", width="large"),
                "时间": st.column_config.TextColumn("时间", width="medium"),
                "地点": st.column_config.TextColumn("地点", width="medium"),
            }
        )

except Exception as e:
    st.error(f"数据库读取失败，请检查文件是否存在: {e}")
