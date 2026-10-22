
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="CINEBOX | 박스오피스",
    page_icon="🎬",
    layout="wide",
)

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

ASSET_DIR = Path(__file__).parent / "assets"

# 한국 시간 기준 어제 날짜
KST = ZoneInfo("Asia/Seoul")
YESTERDAY = (
    datetime.datetime.now(KST).date()
    - datetime.timedelta(days=1)
)


# =========================
# 영화 정보 직접 입력
# 추가 영화 정보 API는 사용하지 않음
# =========================
MOVIE_DETAILS = {
    "사냥개들": {
        "poster_file": "poster_saja.jpg",
        "director": "직접 입력해 주세요",
        "short_intro": "영화의 간단한 소개를 입력해 주세요.",
        "plot": "확인한 줄거리를 입력해 주세요.",
        "cast": [],
    },
    "치이카와": {
        "poster_file": "poster_chiikawa.jpg",
        "director": "직접 입력해 주세요",
        "short_intro": "영화의 간단한 소개를 입력해 주세요.",
        "plot": "확인한 줄거리를 입력해 주세요.",
        "cast": [],
    },
    "인어섬의 비밀": {
        "poster_file": "poster_chiikawa.jpg",
        "director": "직접 입력해 주세요",
        "short_intro": "영화의 간단한 소개를 입력해 주세요.",
        "plot": "확인한 줄거리를 입력해 주세요.",
        "cast": [],
    },
}


def get_details(movie_name):
    """직접 입력한 영화 정보를 찾습니다."""
    normalized = str(movie_name).replace(" ", "").lower()

    for keyword, details in MOVIE_DETAILS.items():
        if keyword.replace(" ", "").lower() in normalized:
            return details

    return {
        "poster_file": None,
        "director": "정보 없음",
        "short_intro": "아직 영화 소개가 등록되지 않았습니다.",
        "plot": "아직 줄거리 정보가 등록되지 않았습니다.",
        "cast": [],
    }


def get_poster(movie_name):
    """assets 폴더에서 포스터 파일을 찾습니다."""
    filename = get_details(movie_name).get("poster_file")

    if not filename:
        return None

    path = ASSET_DIR / filename
    return path if path.exists() else None


def format_movie_name(movie):
    """누적 관객수가 100만 명을 초과하면 트로피를 붙입니다."""
    name = str(movie["movieNm"])
    audience_total = int(movie["audiAcc"])

    if audience_total > 1_000_000:
        return f"🏆 {name}"

    return name


def format_rank_change(value):
    """전일 대비 순위 변동을 화살표로 표시합니다."""
    value = int(value)

    if value > 0:
        return f"🔺 +{value}"
    elif value < 0:
        return f"🔽 {value}"
    else:
        return "➖ 0"


# =========================
# 화면 디자인
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

.stApp {
    background:
        radial-gradient(ellipse at 8% 0%, #202044 0%, transparent 35%),
        radial-gradient(ellipse at 95% 10%, #162b45 0%, transparent 30%),
        #090d18;
    color: #f5f7ff;
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
    padding: 32px;
    margin-bottom: 26px;
}

.eyebrow {
    color: #aaa2ff;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 3px;
}

.hero-title {
    font-size: clamp(30px, 4vw, 46px);
    line-height: 1.25;
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
    margin-top: 30px;
    margin-bottom: 5px;
}

.section-subtitle {
    color: #9aa9c0;
    font-size: 13px;
    margin-bottom: 18px;
}

.metric-panel {
    background: linear-gradient(145deg, #172238, #101827);
    border: 1px solid #2a3850;
    border-radius: 18px;
    padding: 20px 22px;
    min-height: 112px;
}

.metric-label {
    color: #aab7ce;
    font-size: 13px;
    margin-bottom: 10px;
}

.metric-value {
    color: white;
    font-size: clamp(22px, 2.5vw, 32px);
    font-weight: 800;
    letter-spacing: -1px;
}

.metric-unit {
    font-size: 13px;
    color: #c0c9da;
    font-weight: 500;
}

.movie-name {
    font-size: 18px;
    font-weight: 800;
    line-height: 1.45;
    overflow-wrap: anywhere;
    margin-bottom: 6px;
}

.muted {
    color: #a8b4ca;
    font-size: 12px;
    line-height: 1.7;
}

div[data-testid="stButton"] > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 700;
}

div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(100deg, #7768f8, #9a73ff);
    border: none;
    color: white;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #29364b;
    border-radius: 14px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 제목
# =========================
st.markdown("""
<div class="hero">
    <div class="eyebrow">C I N E B O X / DAILY CHART</div>
    <div class="hero-title">어제의 영화,<br>오늘의 기록.</div>
    <div class="hero-desc">
        날짜별 박스오피스를 확인하고 영화 순위와 관객수를 비교해 보세요.<br>
        박스오피스 데이터: 영화관입장권통합전산망(KOBIS)
    </div>
</div>
""", unsafe_allow_html=True)


# =========================
# 날짜 선택
# =========================
st.markdown(
    '<div class="section-heading">📅 날짜 선택</div>',
    unsafe_allow_html=True,
)
st.caption("달력에서 조회할 날짜를 선택하세요. 오늘 날짜는 집계 전이므로 선택할 수 없습니다.")

selected_date = st.date_input(
    "박스오피스 조회 날짜",
    value=YESTERDAY,
    max_value=YESTERDAY,
    format="YYYY-MM-DD",
)

TARGET_DT = selected_date.strftime("%Y%m%d")

st.markdown(
    f"**조회 날짜: {selected_date.strftime('%Y년 %m월 %d일')}**",
)


# =========================
# KOBIS API 인증키
# =========================
try:
    api_key = str(st.secrets["KOBIS_KEY"]).strip()
except (KeyError, FileNotFoundError):
    st.error(
        "KOBIS_KEY를 찾을 수 없습니다. "
        "Streamlit Cloud의 Settings → Secrets에 인증키를 등록해 주세요."
    )
    st.stop()

if not api_key:
    st.error("KOBIS_KEY가 비어 있습니다. 인증키를 입력해 주세요.")
    st.stop()


@st.cache_data(ttl=3600)
def fetch_boxoffice(date_str, key):
    response = requests.get(
        API_URL,
        params={
            "key": key,
            "targetDt": date_str,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


try:
    data = fetch_boxoffice(TARGET_DT, api_key)

except requests.exceptions.Timeout:
    st.error("KOBIS 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

except requests.exceptions.HTTPError as error:
    st.error(f"HTTP 오류: {error}. API 주소와 서버 상태를 확인해 주세요.")
    st.stop()

except requests.exceptions.RequestException:
    st.error("KOBIS 서버에 연결하지 못했습니다. 네트워크를 확인해 주세요.")
    st.stop()

except ValueError:
    st.error("API 응답을 JSON으로 읽을 수 없습니다.")
    st.stop()


if not isinstance(data, dict):
    st.error("API 응답 형식이 올바르지 않습니다.")
    st.stop()

if "faultInfo" in data:
    fault = data.get("faultInfo", {})
    st.error(
        f"KOBIS API 오류: "
        f"{fault.get('message', '원인을 확인할 수 없습니다.')} "
        f"(코드: {fault.get('errorCode', '코드 없음')})"
    )
    st.info("Secrets에 입력한 KOBIS_KEY가 올바른지 확인해 주세요.")
    st.stop()

result = data.get("boxOfficeResult")

if not isinstance(result, dict):
    st.error("박스오피스 결과가 없습니다.")
    st.stop()

movies = result.get("dailyBoxOfficeList", [])

# 목록이 비어 있으면 집계 전 안내를 표시합니다.
if not movies:
    st.warning("그날은 아직 집계 전입니다")
    st.stop()

df = pd.DataFrame(movies)

required = [
    "rank",
    "rankInten",
    "movieNm",
    "openDt",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
]

missing = [col for col in required if col not in df.columns]

if missing:
    st.error("API 응답에 필요한 항목이 없습니다: " + ", ".join(missing))
    st.stop()

# 숫자 데이터 변환
for col in ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df[["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]].isna().any().any():
    st.error("순위, 순위 변동 또는 관객수 데이터에 잘못된 값이 있습니다.")
    st.stop()

df = df.sort_values("rank").reset_index(drop=True)


# =========================
# 1위 영화 지표
# =========================
top = df.iloc[0]
top_name = format_movie_name(top)

st.markdown(
    '<div class="section-heading">🏆 오늘의 박스오피스 리더</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">선택한 날짜의 박스오피스 1위 영화</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div style="background:#121a2a;border:1px solid #263248;
    border-radius:14px;padding:15px 18px;">
        <span style="color:#aaa2ff;font-weight:800;">NO. 01</span>
        &nbsp;&nbsp;
        <span style="font-size:20px;color:white;font-weight:800;">
            {top_name}
        </span>
        &nbsp;&nbsp;
        <span style="color:#aab7ce;">
            개봉일: {top['openDt'] or '정보 없음'}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

cols = st.columns(3)

metrics = [
    (cols[0], "👥 해당 날짜 관객수", int(top["audiCnt"]), "명"),
    (cols[1], "🎟️ 누적 관객수", int(top["audiAcc"]), "명"),
    (cols[2], "🖥️ 스크린수", int(top["scrnCnt"]), "개"),
]

for col, label, value, unit in metrics:
    with col:
        st.markdown(
            f"""
            <div class="metric-panel">
                <div class="metric-label">{label}</div>
                <div class="metric-value">
                    {value:,}<span class="metric-unit"> {unit}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================
# 영화 상세 정보 팝업
# =========================
@st.dialog("🎬 영화 상세 정보", width="large")
def show_movie_dialog(movie):
    name = str(movie["movieNm"])
    details = get_details(name)
    poster = get_poster(name)

    left, right = st.columns([0.8, 1.6], gap="large")

    with left:
        if poster:
            st.image(str(poster), width=220)
        else:
            st.info("등록된 포스터가 없습니다.")

    with right:
        st.title(format_movie_name(movie))
        st.caption(f"조회 날짜: {selected_date.strftime('%Y년 %m월 %d일')}")
        st.write(f"**박스오피스 순위:** {int(movie['rank'])}위")
        st.write(f"**전일 대비 순위 변동:** {format_rank_change(movie['rankInten'])}")
        st.write(f"**감독:** {details['director']}")
        st.write(f"**개봉일:** {movie.get('openDt') or '정보 없음'}")
        st.write(f"**해당 날짜 관객수:** {int(movie['audiCnt']):,}명")
        st.write(f"**누적 관객수:** {int(movie['audiAcc']):,}명")
        st.write(f"**스크린수:** {int(movie['scrnCnt']):,}개")

    st.divider()
    st.subheader("📖 줄거리")
    st.write(details["plot"])

    st.divider()
    st.subheader("🎭 등장인물 및 배우·성우")

    cast = details.get("cast", [])

    if cast:
        for start in range(0, len(cast), 2):
            cast_cols = st.columns(2)

            for offset, person in enumerate(cast[start:start + 2]):
                with cast_cols[offset]:
                    with st.container(border=True):
                        st.markdown(
                            f"**{person.get('character', '이름 정보 없음')}**"
                        )
                        st.write(
                            f"배우·성우: {person.get('actor', '정보 없음')}"
                        )

                        if person.get("note"):
                            st.caption(person["note"])
    else:
        st.info(
            "등장인물 및 배우·성우 정보는 아직 입력되지 않았습니다. "
            "main.py 위쪽 MOVIE_DETAILS에 직접 추가할 수 있습니다."
        )

    st.caption(
        "추가 영화 정보 API는 사용하지 않습니다. "
        "줄거리와 배역은 직접 입력한 정보만 표시됩니다."
    )

    if st.button("닫기", width="stretch"):
        st.session_state["selected_movie"] = None
        st.rerun()


# =========================
# TOP 3 영화 카드
# =========================
st.markdown(
    '<div class="section-heading">✨ TOP 3 영화</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    '포스터와 감독, 간단한 소개를 확인하세요.'
    '</div>',
    unsafe_allow_html=True,
)

for _, movie in df.head(3).iterrows():
    movie_dict = movie.to_dict()
    name = str(movie["movieNm"])
    rank = int(movie["rank"])
    details = get_details(name)
    poster = get_poster(name)

    with st.container(border=True):
        poster_col, text_col = st.columns([0.7, 2.8], gap="medium")

        with poster_col:
            if poster:
                st.image(str(poster), width=125)
            else:
                st.caption("🎞️ 포스터 없음")

        with text_col:
            st.caption(f"RANKING 0{rank}")
            st.markdown(
                f'<div class="movie-name">{format_movie_name(movie)}</div>',
                unsafe_allow_html=True,
            )
            st.write(f"🎬 **감독:** {details['director']}")
            st.write(details["short_intro"])

            st.markdown(
                f'<div class="muted">'
                f'개봉일: {movie["openDt"] or "정보 없음"}'
                f' · 관객수: {int(movie["audiCnt"]):,}명'
                f' · 순위 변동: {format_rank_change(movie["rankInten"])}'
                f'</div>',
                unsafe_allow_html=True,
            )

            if st.button(
                "상세 정보 보기 ↗",
                key=f"detail_{rank}_{name}",
                width="stretch",
                type="primary",
            ):
                st.session_state["selected_movie"] = movie_dict
                st.rerun()


selected = st.session_state.get("selected_movie")

if selected:
    show_movie_dialog(selected)


# =========================
# 전체 박스오피스 표
# =========================
st.markdown(
    '<div class="section-heading">📋 전체 박스오피스</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    '순위 변동과 누적 관객수 기준 트로피를 확인하세요.'
    '</div>',
    unsafe_allow_html=True,
)

search = st.text_input(
    "🔎 영화 검색",
    placeholder="영화명을 입력하세요.",
)

filtered = df.copy()

if search.strip():
    filtered = filtered[
        filtered["movieNm"].str.contains(
            search.strip(), case=False, na=False
        )
    ]

table = pd.DataFrame({
    "순위": filtered["rank"].astype(int),
    "순위 변동": filtered["rankInten"].apply(format_rank_change),
    "영화명": filtered.apply(format_movie_name, axis=1),
    "개봉일": filtered["openDt"],
    "관객수": filtered["audiCnt"].astype("int64").map(lambda x: f"{x:,}"),
    "누적 관객수": filtered["audiAcc"].astype("int64").map(lambda x: f"{x:,}"),
    "스크린수": filtered["scrnCnt"].astype("int64").map(lambda x: f"{x:,}"),
})

st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    height=450,
)


# =========================
# 관객수 TOP 5 그래프
# =========================
st.markdown(
    '<div class="section-heading">📊 관객수 TOP 5</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    '선택한 날짜에 관객수가 많았던 영화 다섯 편'
    '</div>',
    unsafe_allow_html=True,
)

top5 = df.sort_values("audiCnt", ascending=False).head(5).copy()
top5["표시명"] = top5.apply(format_movie_name, axis=1)
chart = top5[["표시명", "audiCnt"]].set_index("표시명")
chart.columns = ["관객수"]

st.bar_chart(
    chart,
    horizontal=True,
    x_label="관객수 (명)",
    y_label="영화명",
)


# =========================
# 하단 안내
# =========================
st.divider()

st.markdown("""
<div style="text-align:center;color:#8794ad;font-size:12px;line-height:2;">
    <b style="color:#c1c8ff;">CINEBOX</b><br>
    박스오피스 데이터: 영화관입장권통합전산망(KOBIS)<br>
    순위 변동: KOBIS rankInten · 영화 소개 및 배역: 직접 입력한 정보
</div>
""", unsafe_allow_html=True)
