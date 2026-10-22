import datetime
import html
import re
import unicodedata
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="CINEBOX | 박스오피스",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/"
    "webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
)

KST = ZoneInfo("Asia/Seoul")
TODAY = datetime.datetime.now(KST).date()
YESTERDAY = TODAY - datetime.timedelta(days=1)
MIN_DATE = datetime.date(2004, 1, 1)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    :root {
        --bg: #090d18;
        --muted: #9aa9c0;
        --white: #f5f7ff;
    }
    .stApp {
        background:
            radial-gradient(ellipse at 10% 0%, #202044 0%, transparent 35%),
            radial-gradient(ellipse at 95% 10%, #162b45 0%, transparent 30%),
            var(--bg);
        color: var(--white);
        font-family: 'Noto Sans KR', sans-serif;
    }
    .block-container {
        max-width: 1440px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    .hero {
        background: linear-gradient(120deg, #202746, #151a30 60%, #20213c);
        border: 1px solid #38415e;
        border-radius: 24px;
        padding: 34px 36px;
        margin-bottom: 26px;
    }
    .eyebrow {
        color: #aaa2ff;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 3px;
    }
    .hero-title {
        font-size: clamp(30px, 4vw, 48px);
        line-height: 1.2;
        font-weight: 800;
        margin: 10px 0;
    }
    .hero-desc, .section-subtitle {
        color: #b7c1d7;
        font-size: 13px;
        line-height: 1.8;
    }
    .section-heading {
        font-size: 23px;
        font-weight: 800;
        margin-top: 32px;
        margin-bottom: 5px;
    }
    .metric-panel, .movie-card, .info-strip {
        background: linear-gradient(145deg, #172238, #101827);
        border: 1px solid #2a3850;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 12px;
    }
    .metric-label {
        color: #aab7ce;
        font-size: 13px;
        margin-bottom: 10px;
    }
    .metric-value {
        color: white;
        font-size: clamp(23px, 2.5vw, 34px);
        font-weight: 800;
    }
    .movie-rank {
        color: #aaa2ff;
        font-size: 12px;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .movie-name {
        font-size: 17px;
        line-height: 1.5;
        font-weight: 800;
        margin: 9px 0 4px;
        overflow-wrap: anywhere;
    }
    .movie-meta {
        font-size: 12px;
        color: #a8b4ca;
    }
    .movie-audience {
        font-size: 14px;
        font-weight: 700;
        color: #e7eaff;
        margin: 10px 0;
    }
    .poster-fallback {
        height: 290px;
        border-radius: 12px;
        background: linear-gradient(145deg, #292f52, #111726);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #b7b9e8;
        text-align: center;
        padding: 18px;
    }
    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 700;
    }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def fetch_boxoffice(date_str, api_key):
    response = requests.get(
        API_URL,
        params={"key": api_key, "targetDt": date_str},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_movie_info(movie_name, open_date=""):
    """위키백과에서 제목이 일치하는 영화 문서를 검색한다."""
    headers = {
        "User-Agent": "CineboxStreamlitApp/1.0 (movie information viewer)"
    }

    def normalize(text):
        text = unicodedata.normalize("NFKC", str(text)).casefold()
        return re.sub(r"[\W_]+", "", text)

    target = normalize(movie_name)

    for language in ["ko", "en"]:
        api = f"https://{language}.wikipedia.org/w/api.php"

        try:
            response = requests.get(
                api,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": movie_name,
                    "srlimit": 10,
                    "format": "json",
                },
                headers=headers,
                timeout=8,
            )
            response.raise_for_status()

            results = response.json().get("query", {}).get("search", [])

            for result in results:
                title = result.get("title", "")
                if target not in normalize(title):
                    continue

                page_response = requests.get(
                    api,
                    params={
                        "action": "query",
                        "prop": "extracts|pageimages|info",
                        "exintro": 1,
                        "explaintext": 1,
                        "pithumbsize": 800,
                        "inprop": "url",
                        "redirects": 1,
                        "titles": title,
                        "format": "json",
                    },
                    headers=headers,
                    timeout=8,
                )
                page_response.raise_for_status()

                pages = page_response.json().get("query", {}).get("pages", {})

                for page in pages.values():
                    if "missing" in page:
                        continue

                    final_title = page.get("title", "")
                    if target not in normalize(final_title):
                        continue

                    extract = page.get("extract", "").strip()
                    return {
                        "description": extract if len(extract) >= 40 else "",
                        "poster": page.get("thumbnail", {}).get("source"),
                        "url": page.get("fullurl", ""),
                        "source": f"{language.upper()} Wikipedia",
                    }

        except (
            requests.exceptions.RequestException,
            ValueError,
            KeyError,
        ):
            continue

    return {
        "description": "",
        "poster": None,
        "url": "",
        "source": "",
    }


def display_movie_name(movie):
    name = str(movie["movieNm"])
    if int(movie["audiAcc"]) >= 1_000_000:
        return f"🏆 {name}"
    return name


def rank_change_label(value):
    value = int(value)
    if value > 0:
        return f"🔺 +{value}"
    if value < 0:
        return f"🔻 {value}"
    return "−"


st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">C I N E B O X / DAILY CHART</div>
        <div class="hero-title">어제의 영화,<br>오늘의 기록.</div>
        <div class="hero-desc">
            대한민국 박스오피스 데이터로 살펴보는 영화 트렌드<br>
            한국 시간 기준 · KOBIS 일별 박스오피스
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-heading">📅 박스오피스 조회 날짜</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">오늘은 집계 전이므로 어제까지 조회할 수 있습니다.</div>',
    unsafe_allow_html=True,
)

selected_date = st.date_input(
    "조회 날짜",
    value=YESTERDAY,
    min_value=MIN_DATE,
    max_value=YESTERDAY,
    format="YYYY-MM-DD",
)
TARGET_DT = selected_date.strftime("%Y%m%d")

try:
    API_KEY = str(st.secrets["KOBIS_KEY"]).strip()
except (KeyError, FileNotFoundError):
    st.error("KOBIS_KEY를 Streamlit Secrets에 등록해 주세요.")
    st.stop()

if not API_KEY:
    st.error("KOBIS_KEY가 비어 있습니다.")
    st.stop()

try:
    data = fetch_boxoffice(TARGET_DT, API_KEY)
except requests.exceptions.Timeout:
    st.error("KOBIS 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()
except requests.exceptions.RequestException as error:
    st.error(f"KOBIS 서버 연결 오류: {error}")
    st.stop()
except ValueError:
    st.error("KOBIS API 응답을 해석할 수 없습니다.")
    st.stop()

if not isinstance(data, dict):
    st.error("API 응답 형식이 올바르지 않습니다.")
    st.stop()

if "faultInfo" in data:
    fault = data["faultInfo"]
    st.error(
        f"KOBIS API 오류: {fault.get('message', '알 수 없는 오류')} "
        f"(코드: {fault.get('errorCode', '없음')})"
    )
    st.stop()

result = data.get("boxOfficeResult")
if not isinstance(result, dict):
    st.error("박스오피스 결과가 없습니다.")
    st.stop()

movies = result.get("dailyBoxOfficeList", [])
if not movies:
    st.warning(
        f"{selected_date.strftime('%Y년 %m월 %d일')} "
        "그날은 아직 집계 전입니다."
    )
    st.info("다른 날짜를 선택하거나 잠시 후 다시 확인해 주세요.")
    st.stop()

df = pd.DataFrame(movies)

required_columns = [
    "rank", "rankInten", "movieNm", "openDt",
    "audiCnt", "audiAcc", "scrnCnt",
]
missing_columns = [c for c in required_columns if c not in df.columns]

if missing_columns:
    st.error("필수 데이터가 없습니다: " + ", ".join(missing_columns))
    st.stop()

for col in ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df[["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]].isna().any().any():
    st.error("순위 또는 관객수 데이터에 잘못된 값이 있습니다.")
    st.stop()

df = df.sort_values("rank").reset_index(drop=True)
top_movie = df.iloc[0]

st.markdown(
    '<div class="section-heading">🏆 오늘의 박스오피스 리더</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="info-strip">'
    f'<b>NO. 01</b>　{html.escape(display_movie_name(top_movie))}'
    f'　개봉일: {html.escape(str(top_movie["openDt"] or "정보 없음"))}'
    f'</div>',
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)
for col, label, value, unit in [
    (m1, "👥 일일 관객수", top_movie["audiCnt"], "명"),
    (m2, "🎟️ 누적 관객수", top_movie["audiAcc"], "명"),
    (m3, "🖥️ 스크린수", top_movie["scrnCnt"], "개"),
]:
    with col:
        st.markdown(
            f'<div class="metric-panel">'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value">{int(value):,} {unit}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown('<div class="section-heading">✨ TOP 3 영화</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">영화를 선택하면 상세 정보를 확인할 수 있습니다.</div>',
    unsafe_allow_html=True,
)

for index, (_, movie) in enumerate(df.head(3).iterrows(), start=1):
    movie_name = str(movie["movieNm"])
    info = fetch_movie_info(movie_name, str(movie.get("openDt", "")))

    with st.container(border=True):
        st.markdown(f"**RANKING 0{int(movie['rank'])}**")
        if info["poster"]:
            st.image(info["poster"], use_container_width=True)
        else:
            st.markdown(
                f'<div class="poster-fallback">'
                f'<div style="font-size:40px">🎞️</div>'
                f'<div>{html.escape(movie_name)}</div>'
                f'<div>포스터 이미지 없음</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"### {html.escape(display_movie_name(movie))}")
        st.caption(f"개봉일 · {movie['openDt'] or '정보 없음'}")
        st.write(f"👥 일일 관객수: {int(movie['audiCnt']):,}명")
        st.write(f"🎟️ 누적 관객수: {int(movie['audiAcc']):,}명")

        with st.expander("영화 상세 정보"):
            if info["description"]:
                st.write(info["description"])
            else:
                st.info("검색 가능한 영화 소개를 찾지 못했습니다.")
            if info["url"]:
                st.link_button("위키백과 원문", info["url"])

st.markdown('<div class="section-heading">📋 전체 박스오피스</div>', unsafe_allow_html=True)
st.caption(f"{selected_date:%Y년 %m월 %d일} 기준 · KOBIS 공식 데이터")

search_text = st.text_input("🔎 영화 검색", placeholder="영화명을 입력하세요.")
filtered_df = df.copy()

if search_text.strip():
    filtered_df = filtered_df[
        filtered_df["movieNm"].str.contains(
            search_text.strip(), case=False, na=False, regex=False
        )
    ]

table = pd.DataFrame({
    "순위": filtered_df["rank"].astype(int),
    "영화명": filtered_df.apply(display_movie_name, axis=1),
    "순위 변동": filtered_df["rankInten"].map(rank_change_label),
    "개봉일": filtered_df["openDt"],
    "관객수": filtered_df["audiCnt"].astype("int64").map(lambda x: f"{x:,}"),
    "누적 관객수": filtered_df["audiAcc"].astype("int64").map(lambda x: f"{x:,}"),
    "스크린수": filtered_df["scrnCnt"].astype("int64").map(lambda x: f"{x:,}"),
})

st.dataframe(table, hide_index=True, use_container_width=True, height=420)

st.markdown('<div class="section-heading">📊 관객수 TOP 5</div>', unsafe_allow_html=True)
top5 = df.nlargest(5, "audiCnt").copy()
chart_data = top5[["movieNm", "audiCnt"]].copy()
chart_data["movieNm"] = top5.apply(display_movie_name, axis=1)
chart_data = chart_data.set_index("movieNm")
chart_data.columns = ["관객수"]

st.bar_chart(
    chart_data,
    horizontal=True,
    x_label="관객수 (명)",
    y_label="영화명",
)

st.divider()
st.markdown(
    """
    <div style="text-align:center;color:#8794ad;font-size:12px;line-height:2;">
        <b style="color:#c1c8ff;">CINEBOX</b><br>
        데이터 출처: 영화관입장권통합전산망(KOBIS)<br>
        영화 소개 및 이미지: 위키백과 검색 결과<br>
        집계 기준: 한국 시간 기준 선택 날짜
    </div>
    """,
    unsafe_allow_html=True,
)
