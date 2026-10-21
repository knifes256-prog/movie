
# 필요한 라이브러리를 불러온다.
import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st


# 웹페이지의 기본 설정
st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide",
)

# KOBIS API 주소
API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/"
    "webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
)


# 한국 시간 기준으로 어제 날짜를 계산한다.
# 서버의 시간대가 한국과 달라도 날짜가 정확하게 계산된다.
KST = ZoneInfo("Asia/Seoul")
yesterday = datetime.datetime.now(KST).date() - datetime.timedelta(days=1)
target_dt = yesterday.strftime("%Y%m%d")


# KOBIS API에서 영화 데이터를 가져오는 함수
# 같은 날짜의 데이터는 1시간 동안 캐시에 저장한다.
@st.cache_data(ttl=3600)
def fetch_boxoffice(date_str, api_key):
    params = {
        "key": api_key,
        "targetDt": date_str,
    }

    # API 서버에 요청을 보내고 최대 15초 동안 기다린다.
    response = requests.get(API_URL, params=params, timeout=15)

    # HTTP 오류가 발생하면 예외를 발생시킨다.
    response.raise_for_status()

    # JSON 데이터를 파이썬 딕셔너리로 변환한다.
    return response.json()


# 페이지 제목과 조회 날짜
st.title("🎬 어제의 박스오피스")
st.caption(
    f"조회 날짜: {yesterday.strftime('%Y년 %m월 %d일')} "
    "(한국 시간 기준)"
)

# 비밀 금고에 API 인증키가 등록되어 있는지 확인한다.
try:
    API_KEY = st.secrets["KOBIS_KEY"]
except (KeyError, FileNotFoundError):
    st.error(
        "API 인증키를 찾을 수 없습니다. "
        "Streamlit Cloud의 Settings → Secrets에서 "
        "KOBIS_KEY가 등록되어 있는지 확인해 주세요."
    )
    st.stop()

if not str(API_KEY).strip():
    st.error(
        "KOBIS_KEY가 비어 있습니다. "
        "Secrets에 발급받은 인증키를 입력해 주세요."
    )
    st.stop()


# API 요청 및 응답 오류를 처리한다.
try:
    data = fetch_boxoffice(target_dt, str(API_KEY).strip())

except requests.exceptions.Timeout:
    st.error(
        "KOBIS 서버의 응답 시간이 초과되었습니다. "
        "잠시 기다린 후 새로고침해 주세요."
    )
    st.stop()

except requests.exceptions.HTTPError as e:
    st.error(
        f"API 서버에서 HTTP 오류가 발생했습니다: {e}. "
        "KOBIS API 주소와 서버 상태를 확인해 주세요."
    )
    st.stop()

except requests.exceptions.RequestException as e:
    st.error(
        f"KOBIS 서버에 연결하지 못했습니다: {e}. "
        "인터넷 연결과 API 서버 상태를 확인해 주세요."
    )
    st.stop()

except ValueError:
    st.error(
        "API 응답을 JSON으로 읽을 수 없습니다. "
        "KOBIS 서버의 응답 형식과 상태를 확인해 주세요."
    )
    st.stop()


# 인증키가 틀린 경우 HTTP 상태코드가 200이어도
# 응답 안에 faultInfo가 들어올 수 있으므로 따로 검사한다.
if "faultInfo" in data:
    fault = data.get("faultInfo", {})
    error_message = fault.get("message", "오류 메시지가 제공되지 않았습니다.")
    error_code = fault.get("errorCode", "코드 없음")

    st.error(
        f"KOBIS API 오류: {error_message} "
        f"(오류 코드: {error_code})"
    )
    st.info(
        "Secrets의 KOBIS_KEY가 올바른지 확인하고, "
        "KOBIS에서 발급받은 키가 유효한지도 확인해 주세요."
    )
    st.stop()


# 응답에 영화 목록이 있는지 확인한다.
boxoffice_result = data.get("boxOfficeResult")

if not isinstance(boxoffice_result, dict):
    st.error(
        "API 응답에 박스오피스 결과가 없습니다. "
        "KOBIS API 응답 구조와 서비스 상태를 확인해 주세요."
    )
    st.stop()

movies = boxoffice_result.get("dailyBoxOfficeList", [])

if not movies:
    st.warning(
        "해당 날짜의 영화 목록이 비어 있습니다. "
        "KOBIS에서 전날 집계가 완료되었는지 확인해 주세요. "
        "휴일이나 집계 지연으로 데이터가 아직 제공되지 않을 수 있습니다."
    )
    st.stop()


# 영화 목록을 표로 다루기 쉽게 판다스 데이터프레임으로 바꾼다.
df = pd.DataFrame(movies)

# API에서 숫자가 문자열로 오므로 숫자형으로 변환한다.
numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]

for col in numeric_columns:
    if col not in df.columns:
        st.error(
            f"API 응답에 '{col}' 항목이 없습니다. "
            "KOBIS 응답 구조를 확인해 주세요."
        )
        st.stop()

    df[col] = pd.to_numeric(df[col], errors="coerce")

# 핵심 데이터가 숫자로 변환되지 않았다면 안내한다.
if df[numeric_columns].isna().any().any():
    st.error(
        "영화 순위 또는 관객수 데이터를 숫자로 변환할 수 없습니다. "
        "KOBIS API 응답 내용을 확인해 주세요."
    )
    st.stop()

# 순위를 기준으로 오름차순 정렬한다.
df = df.sort_values("rank").reset_index(drop=True)


# 1위 영화의 주요 지표를 큰 카드 세 장으로 보여 준다.
top_movie = df.iloc[0]

st.subheader(f"🥇 오늘의 1위 영화: {top_movie['movieNm']}")

card1, card2, card3 = st.columns(3)

card1.metric(
    label="어제 관객수",
    value=f"{int(top_movie['audiCnt']):,}명",
)

card2.metric(
    label="누적 관객수",
    value=f"{int(top_movie['audiAcc']):,}명",
)

card3.metric(
    label="스크린수",
    value=f"{int(top_movie['scrnCnt']):,}개",
)


# 전체 영화 순위표를 보여 준다.
st.subheader("📋 일별 박스오피스 순위")

table_columns = [
    "rank",
    "movieNm",
    "openDt",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
]

table = df[table_columns].copy()

# 표의 열 이름을 한국어로 바꾼다.
table.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수",
]

# 숫자에 천 단위 쉼표를 표시한다.
for col in ["관객수", "누적관객", "스크린수"]:
    table[col] = table[col].astype("int64").map(lambda x: f"{x:,}")

st.dataframe(
    table,
    hide_index=True,
    use_container_width=True,
)


# 어제 관객수가 많은 영화 상위 5편을 막대그래프로 보여 준다.
st.subheader("📊 관객수 상위 5편")

top5 = (
    df.sort_values("audiCnt", ascending=False)
    .head(5)
    .copy()
)

# 영화 이름을 세로축, 관객수를 가로축으로 표시한다.
chart_data = top5.set_index("movieNm")[["audiCnt"]]
chart_data.columns = ["관객수"]

st.bar_chart(
    chart_data,
    horizontal=True,
    x_label="관객수 (명)",
    y_label="영화명",
)

# 데이터의 기준을 알려 준다.
st.caption(
    "자료: 영화관입장권통합전산망(KOBIS) "
    "| 기준: 한국 시간으로 계산한 어제의 일별 박스오피스"
)
