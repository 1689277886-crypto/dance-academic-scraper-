import json
import os
import re
import sqlite3
from html import escape
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


st.set_page_config(page_title="舞蹈学术信息看板", layout="wide")

st.markdown("""
<style>
    :root {
        --ink: #17231f;
        --muted: #63736b;
        --line: #d9e2dc;
        --paper: #f7faf6;
        --panel: #ffffff;
        --green: #245c45;
        --green-2: #3f7b60;
        --green-soft: #e7f0ea;
    }

    .stApp {
        background: var(--paper);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(247, 250, 246, 0.88);
        backdrop-filter: blur(8px);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.4rem;
        padding-bottom: 4rem;
    }

    .site-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.8rem 0 1.1rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 1.4rem;
    }

    .brand {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--green);
    }

    .nav-links {
        display: flex;
        gap: 1rem;
        color: var(--muted);
        font-size: 0.92rem;
    }

    .hero {
        background: linear-gradient(180deg, #edf5ef 0%, #f7faf6 100%);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 2.1rem 2rem 1.8rem;
        margin-bottom: 1rem;
    }

    .hero-kicker {
        color: var(--green-2);
        font-size: 0.86rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }

    .hero-title {
        color: var(--ink);
        font-size: clamp(2rem, 5vw, 4.4rem);
        line-height: 1.05;
        font-weight: 750;
        margin: 0;
    }

    .hero-subtitle {
        max-width: 720px;
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.7;
        margin-top: 1rem;
    }

    .stat-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 1rem 0 1.5rem;
    }

    .stat-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem;
    }

    .stat-label {
        color: var(--muted);
        font-size: 0.82rem;
    }

    .stat-value {
        color: var(--green);
        font-size: 1.9rem;
        font-weight: 750;
        margin-top: 0.3rem;
    }

    .section-heading {
        display: flex;
        align-items: end;
        justify-content: space-between;
        border-bottom: 1px solid var(--line);
        padding-bottom: 0.55rem;
        margin: 1.8rem 0 0.9rem;
    }

    .section-heading h2 {
        font-size: 1.35rem;
        color: var(--ink);
        margin: 0;
    }

    .section-heading span {
        color: var(--muted);
        font-size: 0.86rem;
    }

    .poster-wall {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 0.8rem;
        margin-bottom: 1.4rem;
    }

    .poster-tile {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        min-height: 220px;
    }

    .poster-tile img {
        width: 100%;
        aspect-ratio: 3 / 4;
        object-fit: cover;
        display: block;
        background: var(--green-soft);
    }

    .poster-title {
        padding: 0.58rem 0.65rem 0.72rem;
        font-size: 0.82rem;
        line-height: 1.35;
        color: var(--ink);
    }

    .city-chip {
        display: inline-block;
        background: var(--green-soft);
        color: var(--green);
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 0.28rem 0.7rem;
        font-size: 0.84rem;
        font-weight: 650;
        margin: 0.6rem 0 0.55rem;
    }

    .performance-card {
        display: grid;
        grid-template-columns: 112px minmax(0, 1fr);
        gap: 1rem;
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .performance-card img {
        width: 112px;
        aspect-ratio: 3 / 4;
        object-fit: cover;
        border-radius: 6px;
        background: var(--green-soft);
    }

    .performance-title {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }

    .performance-meta {
        color: var(--muted);
        font-size: 0.86rem;
        line-height: 1.5;
        margin-bottom: 0.45rem;
    }

    .performance-intro {
        color: #35443e;
        font-size: 0.92rem;
        line-height: 1.58;
        margin-bottom: 0.65rem;
    }

    .ticket-link {
        display: inline-block;
        color: #ffffff !important;
        background: var(--green);
        border-radius: 6px;
        padding: 0.42rem 0.72rem;
        text-decoration: none !important;
        font-size: 0.86rem;
        font-weight: 650;
    }

    .source-text {
        color: var(--muted);
        font-size: 0.82rem;
        margin-left: 0.7rem;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 8px;
        border: 1px solid var(--line);
        background: #ffffff;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--line);
    }

    .stTabs [data-baseweb="tab"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px 8px 0 0;
        color: var(--green);
    }

    @media (max-width: 720px) {
        .nav-links {
            display: none;
        }
        .hero {
            padding: 1.4rem;
        }
        .stat-row {
            grid-template-columns: 1fr;
        }
        .performance-card {
            grid-template-columns: 82px minmax(0, 1fr);
        }
        .performance-card img {
            width: 82px;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="site-nav">
  <div class="brand">舞蹈学术信息看板</div>
  <div class="nav-links">
    <span>舞剧资讯</span>
    <span>讲座信息</span>
    <span>城市索引</span>
  </div>
</div>

<section class="hero">
  <div class="hero-kicker">Dance Information Board</div>
  <h1 class="hero-title">近期舞蹈资讯<br/>与学术讲座</h1>
  <div class="hero-subtitle">
    聚合公开来源中的舞剧演出、购票入口与讲座信息，按城市与类别整理，仅保留今天及未来可关注的信息。
  </div>
</section>
""", unsafe_allow_html=True)

LOCAL_TZ = ZoneInfo("Asia/Shanghai")
DISPLAY_SECTIONS = ["舞剧资讯", "讲座信息"]
EXCLUDED_SHOW_TITLES = ["无名之辈", "叹春风"]

PERFORMANCE_KEYWORDS = [
    "舞剧", "演出", "剧目", "购票", "开票", "剧场", "剧院", "专场",
    "上演", "巡演", "芭蕾", "音乐剧", "舞蹈诗剧", "校内演出"
]

ACADEMIC_KEYWORDS = [
    "讲座", "研讨", "论坛", "会议", "学术", "报告", "seminar", "symposium"
]

CITY_ORDER = [
    "上海",
    "南京", "苏州", "无锡", "常州", "南通", "扬州", "镇江", "泰州",
    "盐城", "淮安", "徐州", "连云港", "宿迁",
    "杭州", "宁波", "温州", "绍兴", "嘉兴", "湖州", "金华", "台州",
    "舟山", "丽水", "衢州",
    "北京",
]

CITY_TO_REGION = {
    "上海": "上海",
    "南京": "江苏", "苏州": "江苏", "无锡": "江苏", "常州": "江苏",
    "南通": "江苏", "扬州": "江苏", "镇江": "江苏", "泰州": "江苏",
    "盐城": "江苏", "淮安": "江苏", "徐州": "江苏", "连云港": "江苏",
    "宿迁": "江苏",
    "杭州": "浙江", "宁波": "浙江", "温州": "浙江", "绍兴": "浙江",
    "嘉兴": "浙江", "湖州": "浙江", "金华": "浙江", "台州": "浙江",
    "舟山": "浙江", "丽水": "浙江", "衢州": "浙江",
    "北京": "北京",
}

LOCATION_HINTS = {
    "上海": "上海",
    "上戏": "上海",
    "上海戏剧学院": "上海",
    "上海国际舞蹈中心": "上海",
    "南京": "南京",
    "南艺": "南京",
    "南京艺术学院": "南京",
    "江苏大剧院": "南京",
    "南京保利": "南京",
    "苏州": "苏州",
    "无锡": "无锡",
    "常州": "常州",
    "南通": "南通",
    "扬州": "扬州",
    "镇江": "镇江",
    "泰州": "泰州",
    "盐城": "盐城",
    "淮安": "淮安",
    "徐州": "徐州",
    "连云港": "连云港",
    "宿迁": "宿迁",
    "杭州": "杭州",
    "浙江音乐学院": "杭州",
    "浙音": "杭州",
    "宁波": "宁波",
    "温州": "温州",
    "绍兴": "绍兴",
    "嘉兴": "嘉兴",
    "湖州": "湖州",
    "金华": "金华",
    "台州": "台州",
    "舟山": "舟山",
    "丽水": "丽水",
    "衢州": "衢州",
    "北京": "北京",
    "北舞": "北京",
    "北京舞蹈学院": "北京",
    "中国艺术研究院": "北京",
}


def clean_value(value, fallback="待公布"):
    if pd.isna(value) or str(value).strip() == "":
        return fallback
    return str(value).strip()


def normalize_title(title):
    text = str(title or "")
    text = re.sub(r"[《》【】\[\]（）()“”\"'·\s]", "", text)
    text = re.sub(r"(舞剧|音乐剧|芭蕾舞剧|芭蕾|演出|中文版|巡演|专场|经典版)", "", text)
    return text.lower()


def is_excluded_show(title):
    normalized = normalize_title(title)
    return any(normalize_title(excluded) in normalized for excluded in EXCLUDED_SHOW_TITLES)


def today_in_china():
    return datetime.now(LOCAL_TZ).date()


def parse_event_dates(date_text, reference_year=None):
    if not date_text:
        return []

    text = str(date_text)
    if any(marker in text for marker in ["待公布", "另行通知", "暂无", "不详"]):
        return []

    year = reference_year or today_in_china().year
    dates = []

    full_date_pattern = re.compile(
        r"(?P<year>20\d{2})\s*[年./-]\s*(?P<month>\d{1,2})\s*[月./-]\s*(?P<day>\d{1,2})"
    )
    for match in full_date_pattern.finditer(text):
        try:
            dates.append(date(int(match.group("year")), int(match.group("month")), int(match.group("day"))))
        except ValueError:
            continue

    month_day_pattern = re.compile(r"(?<!\d)(?P<month>\d{1,2})\s*[月./]\s*(?P<day>\d{1,2})\s*[日号]?")
    for match in month_day_pattern.finditer(text):
        try:
            dates.append(date(year, int(match.group("month")), int(match.group("day"))))
        except ValueError:
            continue

    same_month_range_pattern = re.compile(
        r"(?:(?P<year>20\d{2})\s*[年./-]\s*)?"
        r"(?P<month>\d{1,2})\s*[月./]\s*(?P<start>\d{1,2})\s*[日号]?"
        r"\s*[-—–~至到]+\s*(?P<end>\d{1,2})\s*[日号]?(?!\s*[月./])"
    )
    for match in same_month_range_pattern.finditer(text):
        try:
            range_year = int(match.group("year")) if match.group("year") else year
            dates.append(date(range_year, int(match.group("month")), int(match.group("end"))))
        except ValueError:
            continue

    return sorted(set(dates))


def is_current_or_future(date_text):
    event_dates = parse_event_dates(date_text)
    return bool(event_dates) and max(event_dates) >= today_in_china()


def classify_section(row):
    category = clean_value(row.get("category"), "")
    text = " ".join([
        clean_value(row.get("title"), ""),
        clean_value(row.get("summary"), ""),
        category,
    ]).lower()

    if category == "舞剧信息" or any(keyword.lower() in text for keyword in PERFORMANCE_KEYWORDS):
        return "舞剧资讯"

    if category == "学术讲座" or any(keyword.lower() in text for keyword in ACADEMIC_KEYWORDS):
        return "讲座信息"

    return ""


def fallback_city(row):
    text = " ".join([
        clean_value(row.get("location"), ""),
        clean_value(row.get("title"), ""),
        clean_value(row.get("summary"), ""),
    ])
    for hint, city in LOCATION_HINTS.items():
        if hint in text:
            return city
    return "其他"


def get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")


@st.cache_data(show_spinner=False, ttl=24 * 60 * 60)
def ai_city_from_location(title, location, summary, api_key):
    fallback_row = {"title": title, "location": location, "summary": summary}
    fallback = fallback_city(fallback_row)

    if not api_key or genai is None or types is None:
        return fallback

    prompt = (
        "请根据活动名称、地点和摘要判断该活动所在城市。"
        "只允许返回以下城市之一："
        f"{'、'.join(CITY_ORDER)}、其他。"
        "请只返回 JSON，格式为 {\"city\":\"城市名\"}。"
        f"\n活动名称：{title}\n地点：{location}\n摘要：{summary}"
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0
            )
        )
        data = json.loads(response.text)
        city = str(data.get("city", "")).strip()
        return city if city in CITY_TO_REGION else fallback
    except Exception:
        return fallback


def city_sort_key(city):
    try:
        return CITY_ORDER.index(city)
    except ValueError:
        return len(CITY_ORDER)


def prepare_display_data(data):
    display_df = data.copy()
    for column in ["poster_url", "intro", "ticket_url", "source"]:
        if column not in display_df.columns:
            display_df[column] = ""

    display_df = display_df[display_df["date"].apply(is_current_or_future)]
    display_df["首页板块"] = display_df.apply(classify_section, axis=1)
    display_df = display_df[display_df["首页板块"].isin(DISPLAY_SECTIONS)]
    display_df = display_df[~display_df["title"].apply(is_excluded_show)]

    api_key = get_api_key()
    with st.spinner("正在判断城市并整理信息..."):
        display_df["城市"] = display_df.apply(
            lambda row: ai_city_from_location(
                clean_value(row.get("title"), ""),
                clean_value(row.get("location"), ""),
                clean_value(row.get("summary"), ""),
                api_key
            ),
            axis=1
        )

    display_df["地区"] = display_df["城市"].map(CITY_TO_REGION).fillna("其他")
    display_df = display_df[
        (
            (display_df["首页板块"] == "舞剧资讯")
            & display_df["地区"].isin(["浙江", "江苏", "上海"])
        )
        | (
            (display_df["首页板块"] == "讲座信息")
            & display_df["地区"].isin(["浙江", "江苏", "上海", "北京"])
        )
    ]

    display_df["名称"] = display_df["title"].apply(lambda value: clean_value(value, "未命名信息"))
    display_df["时间"] = display_df["date"].apply(clean_value)
    display_df["地点"] = display_df["location"].apply(clean_value)
    display_df["简介"] = display_df.apply(
        lambda row: clean_value(row.get("intro"), clean_value(row.get("summary"), "")),
        axis=1
    )
    display_df["海报"] = display_df["poster_url"].apply(lambda value: clean_value(value, ""))
    display_df["购票入口"] = display_df.apply(
        lambda row: clean_value(row.get("ticket_url"), clean_value(row.get("url"), "")),
        axis=1
    )
    display_df["来源"] = display_df["source"].apply(lambda value: clean_value(value, ""))
    display_df["城市排序"] = display_df["城市"].apply(city_sort_key)
    return display_df.sort_values(["首页板块", "城市排序", "地点", "时间", "名称"], na_position="last")


def render_performance_card(row):
    poster_url = clean_value(row.get("海报"), "")
    title = escape(clean_value(row.get("名称"), "未命名信息"))
    time_text = escape(clean_value(row.get("时间")))
    location = escape(clean_value(row.get("地点")))
    intro = escape(clean_value(row.get("简介"), "")[:100])
    source = escape(clean_value(row.get("来源"), ""))
    ticket_url = clean_value(row.get("购票入口"), "")

    image_html = (
        f'<img src="{escape(poster_url)}" alt="{title} 海报" />'
        if poster_url
        else '<div style="width:112px;aspect-ratio:3/4;border-radius:6px;background:#e7f0ea;"></div>'
    )
    source_html = f'<span class="source-text">来源：{source}</span>' if source else ""
    ticket_html = (
        f'<a class="ticket-link" href="{escape(ticket_url)}" target="_blank">购票入口</a>'
        if ticket_url
        else ""
    )

    st.markdown(f"""
    <article class="performance-card">
        <div>{image_html}</div>
        <div>
            <div class="performance-title">{title}</div>
            <div class="performance-meta">时间：{time_text}<br/>地点：{location}</div>
            <div class="performance-intro">{intro}</div>
            <div>{ticket_html}{source_html}</div>
        </div>
    </article>
    """, unsafe_allow_html=True)


def render_section_heading(title, subtitle=""):
    st.markdown(f"""
    <div class="section-heading">
      <h2>{escape(title)}</h2>
      <span>{escape(subtitle)}</span>
    </div>
    """, unsafe_allow_html=True)


def render_stat_row(display_df):
    performance_count = int((display_df["首页板块"] == "舞剧资讯").sum())
    lecture_count = int((display_df["首页板块"] == "讲座信息").sum())
    city_count = int(display_df["城市"].nunique())
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-card"><div class="stat-label">舞剧资讯</div><div class="stat-value">{performance_count}</div></div>
      <div class="stat-card"><div class="stat-label">讲座信息</div><div class="stat-value">{lecture_count}</div></div>
      <div class="stat-card"><div class="stat-label">覆盖城市</div><div class="stat-value">{city_count}</div></div>
    </div>
    """, unsafe_allow_html=True)


def render_poster_wall(display_df):
    poster_df = display_df[
        (display_df["首页板块"] == "舞剧资讯")
        & (display_df["海报"].astype(str).str.strip() != "")
    ].head(12)

    if poster_df.empty:
        return

    tiles = []
    for _, row in poster_df.iterrows():
        title = escape(clean_value(row.get("名称"), "未命名信息"))
        poster = escape(clean_value(row.get("海报"), ""))
        tiles.append(f"""
        <div class="poster-tile">
          <img src="{poster}" alt="{title} 海报" />
          <div class="poster-title">{title}</div>
        </div>
        """)

    render_section_heading("海报墙", "来自信息库中的舞剧海报")
    st.markdown(f'<div class="poster-wall">{"".join(tiles)}</div>', unsafe_allow_html=True)


def load_data():
    conn = sqlite3.connect("academic_events.db")
    df = pd.read_sql_query("SELECT * FROM academic_events ORDER BY date DESC", conn)
    conn.close()
    return df


try:
    df = load_data()

    if df.empty:
        st.info("暂无数据。请先运行采集脚本，或检查 GitHub Actions 是否成功写入 academic_events.db。")
        st.stop()

    search_term = st.text_input("搜索", placeholder="输入剧目、讲座、城市或场馆关键词")
    if search_term:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

    display_df = prepare_display_data(df)

    if display_df.empty:
        st.write("当前没有符合地区与时间条件的信息。")
        st.stop()

    render_stat_row(display_df)
    render_poster_wall(display_df)

    render_section_heading("信息板块", "一级分类与城市索引")
    performance_tab, lecture_tab = st.tabs(["舞剧资讯", "讲座信息"])

    with performance_tab:
        section_df = display_df[display_df["首页板块"] == "舞剧资讯"]
        if section_df.empty:
            st.caption("暂无相关信息")
        else:
            section_cities = sorted(section_df["城市"].unique(), key=city_sort_key)
            selected_city = st.radio("城市", section_cities, horizontal=True, label_visibility="collapsed")
            city_df = section_df[section_df["城市"] == selected_city]
            st.markdown(f'<span class="city-chip">{escape(selected_city)}</span>', unsafe_allow_html=True)
            for _, row in city_df.iterrows():
                render_performance_card(row)

    with lecture_tab:
        section_df = display_df[display_df["首页板块"] == "讲座信息"]
        if section_df.empty:
            st.caption("暂无相关信息")
        else:
            section_cities = sorted(section_df["城市"].unique(), key=city_sort_key)
            for city in section_cities:
                city_df = section_df[section_df["城市"] == city]
                st.markdown(f'<span class="city-chip">{escape(city)}</span>', unsafe_allow_html=True)
                st.dataframe(
                    city_df[["名称", "时间", "地点"]],
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
