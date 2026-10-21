
import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st


# ==================================================
# 1. 기본 설정
# ==================================================

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
YESTERDAY = datetime.datetime.now(KST).date() - datetime.timedelta(days=1)
TARGET_DT = YESTERDAY.strftime("%Y%m%d")


# ==================================================
# 2. 디자인 CSS
# ==================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #090d18;
        --panel: #121a2a;
        --border: #263248;
        --muted: #9aa9c0;
        --accent: #8b7cff;
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

    h1, h2, h3 {
        letter-spacing: -0.7px;
    }

    .hero {
        background: linear-gradient(120deg, #202746, #151a30 60%, #20213c);
        border: 1px solid #38415e;
        border-radius: 24px;
        padding: 34px 36px;
        margin-bottom: 26px;
        position: relative;
        overflow: hidden;
    }

    .hero:after {
        content: 'C';
        position: absolute;
        right: 35px;
        top: -75px;
        font-size: 260px;
        font-weight: 800;
        color: rgba(255,255,255,0.035);
        pointer-events: none;
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

    .hero-desc {
        color: #b7c1d7;
        font-size: 14px;
        line-height: 1.8;
    }

    .section-heading {
        font-size: 23px;
        font-weight: 800;
        margin-top: 32px;
        margin-bottom: 5px;
    }

    .section-subtitle {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 18px;
    }

    .metric-panel {
        background: linear-gradient(145deg, #172238, #101827);
        border: 1px solid #2a3850;
        border-radius: 18px;
        padding: 20px 22px;
        min-height: 120px;
    }

    .metric-label {
        color: #aab7ce;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .metric-value {
        color: #ffffff;
        font-size: clamp(23px, 2.5vw, 34px);
        font-weight: 800;
        letter-spacing: -1px;
    }

    .metric-unit {
        font-size: 14px;
        color: #c0c9da;
        font-weight: 500;
    }

    .movie-card {
        background: linear-gradient(155deg, #172136, #101522);
        border: 1px solid #2b374c;
        border-radius: 18px;
        padding: 12px;
        min-height: 100%;
    }

    .movie-rank {
        color: #aaa2ff;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.5px;
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
        margin-bottom: 8px;
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

    .poster-icon {
        font-size: 45px;
        margin-bottom: 12px;
    }

    .info-strip {
        background: #121a2a;
        border: 1px solid #263248;
        border-radius: 14px;
        padding: 15px 18px;
        color: #c3cee1;
        font-size: 13px;
        line-height: 1.8;
    }

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 700;
        transition: all 0.15s ease;
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(100deg, #7768f8, #9a73ff);
        border: none;
        color: white;
    }

    div[data-testid="stButton"] > button:hover {
        border-color: #a69bff;
        color: white;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #29364b;
        border-radius: 14px;
        overflow: hidden;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# 3. KOBIS API에서 박스오피스 데이터 가져오기
# ==================================================

@st.cache_data(ttl=3600)
def fetch_boxoffice(date_str, api_key):
    response = requests.get(
        API_URL,
        params={"key": api_key, "targetDt": date_str},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


# ==================================================
# 4. 위키백과에서 영화 포스터와 소개 검색
#    별도의 영화 정보 API 키가 필요하지 않다.
# ==================================================

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_movie_info(movie_name):
    """
    한국어 위키백과에서 영화를 검색한다.
    결과가 없으면 영어 위키백과도 검색한다.
    검색에 실패하면 빈 정보를 반환한다.
    """
    headers = {
        "User-Agent": "CineboxStreamlitApp/1.0 (movie information viewer)"
    }

    for language in ["ko", "en"]:
        api = f"https://{language}.wikipedia.org/w/api.php"

        try:
            # 영화 제목과 관련된 문서 검색
            search_response = requests.get(
                api,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": movie_name,
                    "srlimit": 5,
                    "format": "json",
                },
                headers=headers,
                timeout=8,
            )
            search_response.raise_for_status()

            search_results = search_response.json().get(
                "query", {}
            ).get("search", [])

            if not search_results:
                continue

            # 검색 결과 중 영화 제목과 가장 가까운 문서를 선택한다.
            # 위키백과 검색 결과이므로 정확한 영화 일치는 보장되지 않는다.
            page_title = search_results[0]["title"]

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
                    "titles": page_title,
                    "format": "json",
                },
                headers=headers,
                timeout=8,
            )
            page_response.raise_for_status()

            pages = (
                page_response.json()
                .get("query", {})
                .get("pages", {})
            )

            for page in pages.values():
                if page.get("missing") is not None:
                    continue

                extract = page.get("extract", "").strip()
                thumbnail = page.get("thumbnail", {}).get("source")
                page_url = page.get("fullurl", "")

                # 소개 문서가 지나치게 짧으면 소개로 사용하지 않는다.
                if len(extract) < 40:
                    extract = ""

                return {
                    "description": extract,
                    "poster": thumbnail,
                    "url": page_url,
                    "source": f"{language.upper()} Wikipedia",
                }

        except (
            requests.exceptions.RequestException,
            ValueError,
            KeyError,
        ):
            # 위키백과 접속에 실패해도 앱 전체는 계속 실행한다.
            continue

    return {
        "description": "",
        "poster": None,
        "url": "",
        "source": "",
    }


# ==================================================
# 5. 영화 상세 정보 창
# ==================================================

def show_movie_dialog(movie):
    """선택한 영화의 상세 정보를 팝업 창으로 보여 준다."""

    @st.dialog(f"🎬 {movie['movieNm']}", width="large")
    def movie_dialog():
        info = fetch_movie_info(str(movie["movieNm"]))

        left, right = st.columns([0.85, 1.5], gap="large")

        with left:
            if info["poster"]:
                st.image(
                    info["poster"],
                    use_container_width=True,
                )
            else:
                st.markdown(
                    """
                    <div class="poster-fallback">
                        <div class="poster-icon">🎞️</div>
                        <div>포스터를 찾을 수 없습니다.</div>
                        <div style="font-size:12px;margin-top:8px;">
                            영화 소개 자료를 확인해 주세요.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with right:
            st.markdown(f"### {movie['movieNm']}")
            st.caption(f"박스오피스 {int(movie['rank'])}위")

            open_date = str(movie.get("openDt", "")).strip()
            st.write(f"**개봉일:** {open_date or '정보 없음'}")

            st.write(
                f"**일일 관객수:** {int(movie['audiCnt']):,}명"
            )
            st.write(
                f"**누적 관객수:** {int(movie['audiAcc']):,}명"
            )
            st.write(
                f"**스크린수:** {int(movie['scrnCnt']):,}개"
            )

            st.divider()
            st.markdown("#### 영화 소개")

            if info["description"]:
                st.write(info["description"])

                if info["url"]:
                    st.link_button(
                        "원문에서 더 알아보기",
                        info["url"],
                        use_container_width=True,
                    )
            else:
                st.info(
                    "검색 가능한 영화 소개를 찾지 못했습니다. "
                    "영화 제목으로 검색하거나 공식 영화 소개를 확인해 주세요."
                )

            if info["poster"]:
                st.caption(
                    "포스터 이미지는 위키백과 검색 결과에서 가져옵니다. "
                    "박스오피스 순위와 영화 통계는 KOBIS 자료입니다."
                )

        if st.button("닫기", use_container_width=True):
            st.session_state["selected_movie"] = None
            st.rerun()

    movie_dialog()


# ==================================================
# 6. 페이지 상단
# ==================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">C I N E B O X &nbsp; / &nbsp; DAILY CHART</div>
        <div class="hero-title">어제의 영화,<br>오늘의 기록.</div>
        <div class="hero-desc">
            대한민국 박스오피스 데이터로 살펴보는 영화 트렌드<br>
            {YESTERDAY.strftime('%Y년 %m월 %d일')} 기준 · KOBIS 일별 박스오피스
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# 7. 인증키 확인 및 API 오류 처리
# ==================================================

try:
    API_KEY = str(st.secrets["KOBIS_KEY"]).strip()
except (KeyError, FileNotFoundError):
    st.error(
        "KOBIS_KEY를 찾을 수 없습니다. "
        "Streamlit Cloud의 Settings → Secrets에 "
        "인증키를 등록해 주세요."
    )
    st.stop()

if not API_KEY:
    st.error("KOBIS_KEY가 비어 있습니다. 인증키를 입력해 주세요.")
    st.stop()

try:
    data = fetch_boxoffice(TARGET_DT, API_KEY)

except requests.exceptions.Timeout:
    st.error(
        "KOBIS 서버의 응답 시간이 초과되었습니다. "
        "잠시 후 다시 시도해 주세요."
    )
    st.stop()

except requests.exceptions.HTTPError as error:
    st.error(
        f"HTTP 오류가 발생했습니다: {error}. "
        "API 주소와 서버 상태를 확인해 주세요."
    )
    st.stop()

except requests.exceptions.RequestException:
    st.error(
        "KOBIS 서버에 연결하지 못했습니다. "
        "네트워크와 API 서버 상태를 확인해 주세요."
    )
    st.stop()

except ValueError:
    st.error(
        "API 응답을 읽을 수 없습니다. "
        "KOBIS 응답 형식을 확인해 주세요."
    )
    st.stop()

if not isinstance(data, dict):
    st.error("API 응답 형식이 올바르지 않습니다.")
    st.stop()

if "faultInfo" in data:
    fault = data.get("faultInfo", {})
    message = fault.get("message", "원인을 확인할 수 없습니다.")
    code = fault.get("errorCode", "코드 없음")

    st.error(f"KOBIS API 오류: {message} (코드: {code})")
    st.info(
        "Secrets에 입력한 인증키가 올바른지, "
        "KOBIS에서 키가 정상 발급되었는지 확인해 주세요."
    )
    st.stop()

result = data.get("boxOfficeResult")

if not isinstance(result, dict):
    st.error(
        "박스오피스 결과가 없습니다. API 응답과 서버 상태를 확인해 주세요."
    )
    st.stop()

movies = result.get("dailyBoxOfficeList", [])

if not movies:
    st.warning(
        "해당 날짜의 영화 목록이 비어 있습니다. "
        "KOBIS 집계가 완료되었는지 확인해 주세요."
    )
    st.stop()


# ==================================================
# 8. 데이터 정리
# ==================================================

df = pd.DataFrame(movies)

required_columns = [
    "rank",
    "movieNm",
    "openDt",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    st.error(
        "API 응답에 필요한 항목이 없습니다: "
        + ", ".join(missing_columns)
    )
    st.stop()

for col in ["rank", "audiCnt", "audiAcc", "scrnCnt"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df[["rank", "audiCnt", "audiAcc", "scrnCnt"]].isna().any().any():
    st.error("순위 또는 관객수 데이터에 잘못된 값이 있습니다.")
    st.stop()

df = df.sort_values("rank").reset_index(drop=True)


# ==================================================
# 9. 1위 영화 지표 카드
# ==================================================

top_movie = df.iloc[0]

st.markdown(
    '<div class="section-heading">🏆 오늘의 박스오피스 리더</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    '어제 가장 많은 관객이 선택한 영화</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="info-strip">
        <span style="color:#aaa2ff;font-weight:800;">NO. 01</span>
        &nbsp;&nbsp; <span style="font-size:20px;color:white;font-weight:800;">
        {top_movie['movieNm']}</span>
        &nbsp;&nbsp; <span style="color:#aab7ce;">
        개봉일: {top_movie['openDt'] or '정보 없음'}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown(
        f"""
        <div class="metric-panel">
            <div class="metric-label">👥 어제 관객수</div>
            <div class="metric-value">
                {int(top_movie['audiCnt']):,}<span class="metric-unit"> 명</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-panel">
            <div class="metric-label">🎟️ 누적 관객수</div>
            <div class="metric-value">
                {int(top_movie['audiAcc']):,}<span class="metric-unit"> 명</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-panel">
            <div class="metric-label">🖥️ 스크린수</div>
            <div class="metric-value">
                {int(top_movie['scrnCnt']):,}<span class="metric-unit"> 개</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# 10. 1~3위 영화 포스터 카드
# ==================================================

st.markdown(
    '<div class="section-heading">✨ TOP 3 영화</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    '영화를 선택하면 상세 정보와 소개를 확인할 수 있어요.</div>',
    unsafe_allow_html=True,
)

top3 = df.head(3)
card_columns = st.columns(3, gap="medium")

for index, (_, movie) in enumerate(top3.iterrows()):
    movie_dict = movie.to_dict()
    movie_name = str(movie["movieNm"])
    rank = int(movie["rank"])

    # 위키백과에서 포스터를 검색한다.
    # 검색 결과가 없으면 기본 포스터 안내 화면을 보여 준다.
    with card_columns[index]:
        info = fetch_movie_info(movie_name)

        st.markdown(
            f'<div class="movie-card">'
            f'<div class="movie-rank">RANKING 0{rank}</div>',
            unsafe_allow_html=True,
        )

        if info["poster"]:
            st.image(info["poster"], use_container_width=True)
        else:
            st.markdown(
                f"""
                <div class="poster-fallback">
                    <div class="poster-icon">🎞️</div>
                    <div style="font-size:17px;font-weight:800;">
                        {movie_name}
                    </div>
                    <div style="font-size:12px;margin-top:10px;">
                        포스터 이미지 없음
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="movie-name">{movie_name}</div>
            <div class="movie-meta">
                개봉일 · {movie['openDt'] or '정보 없음'}
            </div>
            <div class="movie-audience">
                👥 {int(movie['audiCnt']):,}명
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 클릭한 영화 정보를 세션에 저장하고 상세 창을 연다.
        if st.button(
            "영화 상세 정보 보기  ↗",
            key=f"movie_detail_{rank}_{movie_name}",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["selected_movie"] = movie_dict
            st.rerun()


# 선택한 영화가 있다면 상세 팝업을 표시한다.
selected_movie = st.session_state.get("selected_movie")

if selected_movie:
    show_movie_dialog(selected_movie)


# ==================================================
# 11. 전체 박스오피스 순위표
# ==================================================

st.markdown(
    '<div class="section-heading">📋 전체 박스오피스</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    'KOBIS 공식 일별 집계 데이터</div>',
    unsafe_allow_html=True,
)

search_text = st.text_input(
    "🔎 영화 검색",
    placeholder="영화명을 입력하세요.",
)

filtered_df = df.copy()

if search_text.strip():
    filtered_df = filtered_df[
        filtered_df["movieNm"].str.contains(
            search_text.strip(),
            case=False,
            na=False,
        )
    ]

table = filtered_df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt",
    ]
].copy()

table.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적 관객수",
    "스크린수",
]

table["순위"] = table["순위"].astype(int)

for col in ["관객수", "누적 관객수", "스크린수"]:
    table[col] = table[col].astype("int64").map(
        lambda value: f"{value:,}"
    )

st.dataframe(
    table,
    hide_index=True,
    use_container_width=True,
    height=420,
)


# ==================================================
# 12. 관객수 TOP 5 막대그래프
# ==================================================

st.markdown(
    '<div class="section-heading">📊 관객수 TOP 5</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    '어제 관객수가 많았던 영화 다섯 편 비교</div>',
    unsafe_allow_html=True,
)

top5 = df.sort_values(
    "audiCnt",
    ascending=False,
).head(5).copy()

chart_data = top5[["movieNm", "audiCnt"]].copy()
chart_data = chart_data.set_index("movieNm")
chart_data.columns = ["관객수"]

st.bar_chart(
    chart_data,
    horizontal=True,
    x_label="관객수 (명)",
    y_label="영화명",
)


# ==================================================
# 13. 하단 정보
# ==================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center;color:#8794ad;font-size:12px;line-height:2;">
        <b style="color:#c1c8ff;">CINEBOX</b><br>
        데이터 출처: 영화관입장권통합전산망(KOBIS)<br>
        영화 소개 및 이미지: 위키백과 검색 결과<br>
        집계 기준: 한국 시간 기준 어제
    </div>
    """,
    unsafe_allow_html=True,
)
