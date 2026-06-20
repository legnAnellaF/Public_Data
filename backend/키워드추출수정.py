import os
import csv
import re
import tkinter as tk
from collections import Counter
ALLOWED_CATEGORIES = (
    "부동산", "교통", "주식", "금융", "경제", "에너지", "날씨", "환경", "인구",
    "복지", "관광", "의료", "교육", "안전", "문화", "행정", "고용", "산업", "일반",
)

# 한국어 조사/어미/접속 표현과 공공데이터 검색에 불필요한 일반 표현을 제거합니다.
STOPWORDS = {
    "그리고", "그러나", "하지만", "또는", "혹은", "및", "등", "것", "수", "때", "중", "안",
    "위해", "대한", "대해", "대해서", "관한", "관해", "관해서", "관련", "기반", "특정", "사용자", "입력", "문장", "프롬포트", "프롬프트",
    "정보", "내용", "방법", "기능", "결과", "화면", "파일", "저장", "있는", "없는", "있는지", "있어", "있나요", "있냐", "있니", "있나", "있을까", "위치한", "위치하는", "소재한", "소재하는", "하고",
    "하는", "한다", "된다", "싶다", "만들고", "만드는", "만들", "있다", "어디", "어딘지", "어디에", "어디서", "으로", "에서",
    "에게", "부터", "까지", "보다", "처럼", "통해", "알려줘", "알려주세요", "보여줘", "보여주세요",
    "찾아줘", "찾아주세요", "찾고싶어", "찾고", "찾아보고싶어", "조회해줘", "조회해주세요",
    "조회하고싶어", "확인해줘", "확인해주세요", "확인하고싶습니다", "검색해줘", "검색해주세요",
    "현재", "지금", "알고", "싶어", "주세요", "궁금해", "필요해",
    "나", "내가", "저", "저는", "제가", "우리", "우리가", "내", "제", "방금", "요즘", "최근",
    "근데", "그런데", "그래서", "혹시", "만약", "인데", "하는데", "중인데", "중이야", "중입니다",
    "지나가", "지나가는", "가는중", "이동중", "타려고", "하려고", "가려고", "알고싶어", "궁금합니다",
    "보고싶어", "보고싶습니다", "확인하고싶어", "확인", "볼만한", "있을까", "있을까요", "있나요",
    "알려줄래", "알려주실수있나요", "알수있을까", "알수있나요", "자료찾아줘", "통계보고싶어",
    "오전", "오후", "구매할거야", "구매할거", "구매", "살거야", "사려고", "얼마인지",
    "얼마", "얼마나", "인지", "개나", "개야", "밤에", "밤에도", "빌리", "빌리는",
    "어느", "정도", "정도야", "오는지", "나오는지", "놀러", "가는", "많은지", "심한지",
    "많이", "많은", "많아", "타는", "막히는지", "받을", "났는지", "나는", "곳", "곳이", "붐비는지", "타는지",
    "변한", "생산되는지", "태어났는지", "맡길", "돈이", "어떻게", "됐는지", "쓰는지",
    "되는", "되는지", "되고", "어떤지", "뭐가", "태어", "잠깐", "들를", "들르는",
    "들르려고", "들러", "들릴", "건데", "있는데", "가려는데", "갈까", "고민", "고민중",
    "고민하고", "고민돼", "고민이야", "차가", "너무", "막히는데", "막히", "알아보",
    "알아보는", "알아보는데", "났을", "참고", "걱정돼서", "걱정", "아침마다",
    "늦는데", "늦어", "먹을", "찾는데", "친구", "결혼식", "때문",
    "출근길", "출근", "퇴근", "퇴근하고", "다음", "달", "달에", "수도",
    "있어서", "해서", "주말", "과제", "비가", "뒤라서", "잡으려고", "주차해야",
    "공부", "시작", "시작해서", "아이", "심한", "날", "날이", "잡혀서",
    "캠핑", "준비", "출퇴근", "출퇴근해서", "부담돼서", "가족", "살아서",
    "뉴스", "수업", "듣고", "자주", "코스", "짜는", "중이라", "집",
    "시끄러워서", "타야", "노후", "이직", "휴대폰", "부족", "부족해서",
    "여름휴", "여름휴가", "고르", "고르는", "타고", "다니려고", "일이",
    "생겨서", "보러", "계획이라", "불편", "보고", "발표", "해외", "예산",
    "짜고", "준비하면서", "출장", "오른", "같아서", "붐비", "붐벼서",
    "시간", "계약", "앞두고", "밤길", "약을", "사야", "공기", "좋은",
    "점심", "찾는", "시험", "상태", "하루", "묵어야", "통학길", "인터넷",
    "보고서", "쓰고", "면서", "장마철이라", "길어서", "예약", "전에",
    "동네", "차를", "체험학습", "겨울", "대비", "진학", "자료", "이동해야",
    "문자", "불안", "불안해서", "접근성", "보려고", "가기", "헷갈려서",
    "늘어난", "부족한", "보여서", "기간",
}

PARTICLE_SUFFIXES = (
    "으로부터", "로부터", "에서는", "에게서", "한테서", "까지", "부터", "처럼", "보다",
    "으로", "으로써", "로써", "에게", "한테", "에서", "에는", "은", "는", "이", "가",
    "을", "를", "과", "와", "도", "만", "의", "에", "로", "며", "나", "랑",
)

ENDING_SUFFIXES = (
    "입니다", "합니다", "됩니다", "하였다", "했다", "한다", "된다", "하는", "하고",
    "하며", "하여", "해서", "되며", "되어", "싶다", "있다", "없는", "있는", "할",
)

CATEGORY_KEYWORDS = {
    "부동산": {
        "아파트", "전세", "월세", "매매", "부동산", "주택", "빌라", "오피스텔", "땅값",
        "토지", "건축", "면적", "공시지가", "실거래가", "강남", "부지", "집값",
        "임대료", "공동주택", "전월세",
    },
    "교통": {
        "버스", "지하철", "도로", "교통", "정류장", "노선", "혼잡도", "주차", "사고",
        "자전거", "대중교통", "승하차", "차량", "정체", "혼잡", "통행", "대교", "다리",
        "터널", "ic", "나들목", "공공와이파이", "와이파이",
    },
    "주식": {
        "주식", "주가", "시세", "종가", "현재가", "상장", "증권", "코스피", "코스닥",
        "sk하이닉스", "하이닉스", "삼성전자", "네이버", "카카오", "현대차", "기아",
        "lg에너지솔루션", "포스코", "셀트리온", "kb금융", "신한지주", "삼성바이오로직스",
    },
    "금융": {
        "환율", "금리", "물가", "금융", "은행", "대출", "예금", "채권", "보험",
    },
    "경제": {
        "코스피", "코스닥", "주식", "환율", "금리", "물가", "시장", "지수", "경제",
        "금융", "증권", "휘발유", "경유", "유가", "기름값", "가격",
    },
    "에너지": {"휘발유", "경유", "유가", "기름값", "주유소", "전기", "가스", "전력", "에너지"},
    "날씨": {"날씨", "기상", "기상청", "기상예보", "예보", "기온", "강수량", "미세먼지", "습도", "태풍", "폭염", "한파"},
    "환경": {"대기", "오염", "수질", "폐기물", "탄소", "에너지", "환경"},
    "인구": {"인구", "출생", "사망", "연령", "가구", "세대", "유동인구"},
    "복지": {"복지", "지원금", "보조금", "취약계층", "노인", "장애인", "아동"},
    "관광": {"관광", "관광지", "여행", "축제", "맛집", "숙박", "명소", "문화재", "제주도"},
    "의료": {"병원", "약국", "응급실", "진료", "질병", "건강", "의료"},
    "교육": {"학교", "학원", "교육", "대학", "학생", "도서관", "강의"},
    "안전": {"사고", "화재", "범죄", "치안", "재난", "홍수", "지진", "안전", "구조", "신고"},
    "문화": {"문화", "공연", "전시", "박물관", "미술관", "도서관", "체육", "행사"},
    "행정": {"민원", "행정", "기관", "공공기관", "주민센터", "구청", "시청", "허가"},
    "고용": {"취업", "고용", "일자리", "채용", "실업", "임금", "근로"},
    "산업": {"기업", "공장", "산업", "제조", "수출", "수입", "생산", "사업체"},
}


ONE_CHAR_MAP = {
    "가": "가격",
    "값": "가격",
}

TOKEN_NORMALIZATION_MAP = {
    "지난해": "작년",
    "전년도": "작년",
    "금년": "올해",
    "올해는": "올해",
    "올해의": "올해",
    "작년의": "작년",
    "지난달": "지난달",
    "이번달": "이번달",
    "강변북로": "강변북로",
    "상수도": "상수도",
    "체험마을": "체험마을",
    "울릉도": "울릉도",
    "몇개": "개수",
    "몇개나": "개수",
    "몇개인지": "개수",
    "개나": "개수",
    "개야": "개수",
    "방문자수": "방문객",
    "방문자수가": "방문객",
    "방문자수를": "방문객",
    "방문객수": "방문객",
    "방문객수가": "방문객",
    "방문객수를": "방문객",
    "관강객": "관광객",
    "관강객수": "관광객",
    "몇명": "인원",
    "몇명인지": "인원",
    "어디": "위치",
    "어딘지": "위치",
    "어디에": "위치",
    "어디서": "위치",
    "와이파": "와이파이",
    "공공와이파": "공공와이파이",
    "청년들이": "청년",
    "청년들": "청년",
    "사람": "인원",
    "사람이": "인원",
    "사람들": "인원",
    "바닷가": "해수욕장",
    "숙소": "숙박업소",
    "애기들": "출생아",
    "애기들이": "출생아",
    "우리나라": "한국",
    "나라": "한국",
    "값이": "가격",
    "값은": "가격",
    "값을": "가격",
    "값도": "가격",
    "가격이": "가격",
    "가격은": "가격",
    "가격을": "가격",
    "가격의": "가격",
    "시세가": "시세",
    "시세는": "시세",
    "시세를": "시세",
    "현황이": "현황",
    "현황은": "현황",
    "현황을": "현황",
    "통계가": "통계",
    "통계는": "통계",
    "통계를": "통계",
    "목록이": "목록",
    "목록은": "목록",
    "목록을": "목록",
    "위치가": "위치",
    "위치는": "위치",
    "위치를": "위치",
    "비율이": "비율",
    "비율은": "비율",
    "비율을": "비율",
    "추이가": "추이",
    "추이는": "추이",
    "추이를": "추이",
    "변화가": "변화",
    "변화는": "변화",
    "변화를": "변화",
    "평균이": "평균",
    "평균은": "평균",
    "평균을": "평균",
    "순위가": "순위",
    "순위는": "순위",
    "순위를": "순위",
    "수가": "개수",
    "수는": "개수",
    "수를": "개수",
    "수도": "수도",
    "수의": "개수",
    "개수가": "개수",
    "개수는": "개수",
    "개수를": "개수",
    "개수도": "개수",
    "수량이": "수량",
    "수량은": "수량",
    "수량을": "수량",
    "기름값": "유가",
    "집값": "주택가격",
    "땅값": "토지가격",
    "미세먼지농도": "미세먼지",
}

PUBLIC_DATA_TERMS = set().union(*CATEGORY_KEYWORDS.values())

TIME_KEYWORDS = {"오늘", "어제", "내일", "작년", "지난해", "올해", "지난달", "이번달", "전년도"}

LOCATION_KEYWORDS = {
    "서울", "서울시", "부산", "부산시", "대구", "대구시", "인천", "인천시", "광주", "광주시",
    "광주광역시", "대전", "대전시", "울산", "울산시", "세종", "세종시", "경기", "경기도",
    "강원", "강원도", "충북", "충청북도", "충남", "충청남도", "전북", "전라북도",
    "전남", "전라남도", "경북", "경상북도", "경남", "경상남도", "제주", "제주도",
    "익산", "익산시", "전주", "전주시", "군산", "군산시", "담양", "담양군", "강남",
    "마포", "종로", "송파", "서초", "마포대교", "강남역",
}

INTENT_TO_KEYWORD_MAP = {
    "얼마": "가격",
    "얼마인지": "가격",
    "얼마나": "수량",
    "몇개": "개수",
    "몇 개": "개수",
    "몇명": "인원",
    "몇 명": "인원",
    "어디": "위치",
    "비교": "비교",
    "비교하고": "비교",
    "추이": "추이",
    "현황": "현황",
    "목록": "목록",
    "순위": "순위",
    "평균": "평균",
}

PUBLIC_DATA_SYNONYM_RULES = (
    ({"병원", "개수"}, ["의료기관현황"]),
    ({"약국", "개수"}, ["약국현황"]),
    ({"아파트", "전세"}, ["아파트 전세 실거래가", "부동산 실거래가"]),
    ({"아파트", "매매"}, ["아파트 매매 실거래가", "부동산 실거래가"]),
    ({"버스", "노선"}, ["버스 노선 정보"]),
    ({"버스", "승하차"}, ["버스 승하차 인원"]),
    ({"휘발유", "가격"}, ["휘발유 가격", "유가"]),
    ({"경유", "가격"}, ["경유 가격", "유가"]),
    ({"인구", "개수"}, ["주민등록인구"]),
    ({"기상청", "기상예보"}, ["기상청 기상예보 데이터"]),
)

STOCK_COMPANY_ALIASES = {
    "sk하이닉스": {"sk하이닉스", "하이닉스"},
    "삼성전자": {"삼성전자"},
    "네이버": {"네이버", "naver"},
    "카카오": {"카카오"},
    "현대차": {"현대차", "현대자동차"},
    "기아": {"기아", "기아차"},
    "lg에너지솔루션": {"lg에너지솔루션", "엘지에너지솔루션"},
    "포스코": {"포스코", "posco"},
    "셀트리온": {"셀트리온"},
    "kb금융": {"kb금융", "케이비금융"},
    "신한지주": {"신한지주"},
    "삼성바이오로직스": {"삼성바이오로직스", "삼성바이오"},
}

STOCK_PRICE_INTENT_TERMS = {"주가", "시세", "가격", "현재가", "얼마", "얼마인지"}

NOISE_PATTERNS = (
    r"데이터가\s*있을까",
    r"데이터가\s*있을까요",
    r"데이터\s*있을까",
    r"데이터\s*있을까요",
    r"출근길에",
    r"다음\s*달에",
    r"이사할\s*수도\s*있어서",
    r"부모님\s*병원\s*알아보는\s*중인데",
    r"주말에",
    r"여행을\s*가려고\s*해서",
    r"학교\s*과제\s*때문에",
    r"비가\s*많이\s*온\s*뒤라서",
    r"친구랑",
    r"숙소를\s*잡으려고\s*하는데",
    r"퇴근하고",
    r"주차해야\s*해서",
    r"주식\s*공부를\s*시작해서",
    r"아이\s*학교를\s*알아보는\s*중인데",
    r"미세먼지가\s*심한\s*날이\s*많아서",
    r"심한\s*날이\s*많아서",
    r"택시가\s*잘\s*안\s*잡혀서",
    r"캠핑을\s*준비\s*중인데",
    r"지하철로\s*출퇴근해서",
    r"기름값이\s*부담돼서",
    r"가족이\s*살아서",
    r"태풍\s*뉴스가\s*걱정돼서",
    r"[가-힣A-Za-z0-9]+\s*수업을\s*듣고\s*있어서",
    r"버스가\s*자주\s*늦어서",
    r"청년\s*지원\s*정책을\s*알아보는\s*중인데",
    r"여행\s*코스를\s*짜는\s*중이라",
    r"집\s*근처가\s*시끄러워서",
    r"출근할\s*때",
    r"버스를\s*타야\s*해서",
    r"노후\s*준비를\s*하면서",
    r"이직\s*준비\s*중이라",
    r"휴대폰\s*데이터가\s*부족해서",
    r"여름휴가\s*장소를\s*고르는\s*중인데",
    r"자전거를\s*타고\s*다니려고\s*해서",
    r"병원\s*갈\s*일이\s*생겨서",
    r"창업을\s*준비\s*중인데",
    r"공연\s*보러\s*갈\s*계획이라",
    r"부동산\s*공부를\s*하고\s*있어서",
    r"주차\s*때문에\s*자주\s*불편해서",
    r"지진\s*뉴스를\s*보고\s*걱정돼서",
    r"급식\s*메뉴가\s*궁금해서",
    r"농업\s*관련\s*발표를\s*준비해서",
    r"해외\s*경제\s*뉴스를\s*보다가",
    r"아이\s*어린이집을\s*알아보는\s*중인데",
    r"여행\s*예산을\s*짜고\s*있어서",
    r"아파트\s*매매를\s*고민\s*중이라",
    r"가족\s*여행을\s*준비하면서",
    r"출장이\s*많아서",
    r"물가가\s*오른\s*것\s*같아서",
    r"버스가\s*붐비는\s*시간이\s*많아서",
    r"월세\s*계약을\s*앞두고\s*있어서",
    r"밤길이\s*걱정돼서",
    r"약을\s*사야\s*해서",
    r"공기가\s*안\s*좋은\s*날이\s*많아서",
    r"공항\s*갈\s*일이\s*있어서",
    r"취업\s*준비\s*중이라",
    r"행정기관\s*방문할\s*일이\s*있어서",
    r"화재\s*뉴스를\s*보고",
    r"산책할\s*곳을\s*찾다가",
    r"점심\s*먹을\s*곳을\s*찾는\s*중인데",
    r"대출\s*금리가\s*걱정돼서",
    r"지하철이\s*너무\s*붐벼서",
    r"시험\s*공부할\s*장소를\s*찾고\s*있어서",
    r"어촌\s*여행을\s*준비\s*중인데",
    r"학교\s*위치를\s*비교하려고",
    r"바다\s*쓰레기\s*문제가\s*궁금해서",
    r"대기\s*상태가\s*걱정돼서",
    r"병원\s*진료를\s*알아보는\s*중인데",
    r"하루\s*묵어야\s*해서",
    r"아이\s*통학길이\s*걱정돼서",
    r"인터넷\s*쓸\s*곳이\s*필요해서",
    r"부모님\s*복지시설을\s*알아보면서",
    r"주식\s*시장을\s*공부하려고",
    r"전기차\s*관련\s*보고서를\s*쓰고\s*있어서",
    r"여행을\s*고민\s*중인데",
    r"아파트\s*청약을\s*준비하면서",
    r"장마철이라",
    r"출퇴근\s*시간이\s*길어서",
    r"병원\s*예약\s*전에",
    r"반려동물\s*등록\s*제도가\s*궁금해서",
    r"동네가\s*시끄러워서",
    r"새\s*차를\s*사려고\s*해서",
    r"아이\s*체험학습\s*장소를\s*찾고\s*있어서",
    r"폭염이\s*걱정돼서",
    r"겨울\s*대비를\s*하면서",
    r"창업\s*지역을\s*고르는\s*중이라",
    r"대학\s*진학\s*자료를\s*찾고\s*있어서",
    r"주말에\s*버스를\s*타고\s*이동해야\s*해서",
    r"동네\s*안전이\s*걱정돼서",
    r"관광\s*보고서를\s*쓰고\s*있어서",
    r"재난\s*문자\s*보고\s*불안해서",
    r"이사\s*갈\s*동네를\s*비교하려고",
    r"병원\s*접근성을\s*보려고",
    r"공장\s*취업을\s*알아보는\s*중인데",
    r"장\s*보러\s*가기\s*전에",
    r"정류장이\s*헷갈려서",
    r"기차\s*여행을\s*준비하면서",
    r"물\s*사용량이\s*늘어난\s*것\s*같아서",
    r"동네\s*공원이\s*부족한\s*것\s*같아서",
    r"폐업이\s*많아\s*보여서",
    r"시험\s*기간에\s*공부할\s*곳이\s*필요해서",
    r"출산\s*지원을\s*알아보는\s*중인데",
    r"지나가는\s*중인데",
    r"지나가는\s*중",
    r"가는\s*중인데",
    r"가는\s*중",
    r"가려고\s*하는데",
    r"가려고",
    r"가려는데",
    r"잠깐\s*들를\s*건데",
    r"들를\s*건데",
    r"들르려고\s*하는데",
    r"이사\s*갈까\s*고민(?:하고\s*있는데|중인데|중이야|이야|돼)?",
    r"이사\s*가려고\s*하는데",
    r"차가\s*너무\s*막히는데",
    r"너무\s*막히는데",
    r"아이\s*학교\s*알아보는\s*중인데",
    r"알아보는\s*중인데",
    r"차\s*사고가\s*났을\s*때\s*참고할\s*수\s*있는",
    r"부모님\s*병원\s*알아보는데",
    r"알아보는데",
    r"났을\s*때\s*참고할\s*수\s*있는",
    r"참고할\s*수\s*있는",
    r"전기요금이\s*걱정돼서",
    r"걱정돼서",
    r"아침마다\s*버스가\s*늦는데",
    r"버스가\s*늦는데",
    r"회사\s*근처\s*점심\s*먹을\s*곳\s*찾는데",
    r"먹을\s*곳\s*찾는데",
    r"친구\s*결혼식\s*때문에",
    r"알고\s*싶어",
    r"찾고\s*싶어",
    r"보고\s*싶어",
    r"확인하고\s*싶어",
    r"확인해\s*줘",
    r"확인해\s*주세요",
    r"검색해\s*줘",
    r"검색해\s*주세요",
    r"어디에\s*있어",
    r"어디에\s*있나요",
    r"어디\s*있어",
    r"어디\s*있나요",
    r"구매할\s*거야",
    r"구매할\s*거",
    r"살\s*거야",
    r"사려고",
    r"얼마인지",
)

NOISE_PHRASES = (
    "지나가는중인데", "지나가는중", "지나가는", "지나가", "가는중인데", "가는중",
    "중인데", "중이야", "중입니다", "알고싶어", "찾고싶어", "궁금합니다", "궁금해", "알려주세요",
    "알려줘", "보고싶어", "확인하고싶어", "확인해줘", "확인해주세요", "검색해줘", "검색해주세요",
    "볼만한", "타려고", "하려고", "가려고", "가려는데", "있을까요",
    "있을까", "있나요", "있어", "있냐", "있니", "있나", "있는지", "어디에", "어디서", "어디", "지금", "현재", "방금", "요즘", "최근",
    "내가", "제가", "저는", "우리가", "우리", "근데", "그런데", "그래서", "혹시", "만약",
    "하는데", "인데", "대해", "대해서", "관한", "관해", "관해서", "위치한", "위치하는", "소재한", "소재하는", "오전", "오후", "구매할거야", "구매할거", "구매", "살거야",
    "사려고", "얼마인지", "얼마나", "얼마", "인지", "개나", "개야", "밤에", "밤에도",
    "빌리", "빌리는", "어느", "정도", "정도인지", "정도야", "오는지", "나오는지",
    "놀러", "가는", "많은지", "심한지", "많이", "많은", "많아", "타는", "막히는지", "받을",
    "났는지", "나는", "곳", "곳이", "붐비는지", "타는지", "변한", "생산되는지",
    "태어났는지", "태어", "맡길", "돈이", "어떻게", "됐는지", "쓰는지", "되는", "되고",
    "되는지", "어떤지", "뭐가", "필요해", "확인", "잠깐", "들를", "들르는",
    "들르려고", "들러", "들릴", "건데", "있는데", "갈까", "고민중", "고민하고",
    "고민돼", "고민이야", "고민", "차가", "너무", "막히는데", "막히", "알아보",
    "알아보는", "알아보는데", "났을", "참고", "걱정돼서", "걱정", "아침마다",
    "늦는데", "늦어", "먹을", "찾는데", "친구", "결혼식", "때문에", "때문",
)


def normalize_token(token):
    """토큰에서 조사와 흔한 어미를 제거해 키워드 후보로 정리합니다."""
    token = token.strip().lower()
    token = re.sub(r"^[^0-9a-zA-Z가-힣]+|[^0-9a-zA-Z가-힣]+$", "", token)

    if token in TOKEN_NORMALIZATION_MAP:
        return TOKEN_NORMALIZATION_MAP[token]

    if token in PUBLIC_DATA_TERMS or token in LOCATION_KEYWORDS:
        return token

    for suffix in ENDING_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            token = token[: -len(suffix)]
            break

    for suffix in PARTICLE_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            token = token[: -len(suffix)]
            break

    return ONE_CHAR_MAP.get(token, token)


def is_location_keyword(keyword):
    """지역명 또는 장소명으로 볼 수 있는 키워드인지 판단합니다."""
    if keyword in LOCATION_KEYWORDS:
        return True
    if keyword in PUBLIC_DATA_TERMS or keyword in ALLOWED_CATEGORIES or keyword in {"주민등록인구", "인구", "가구"}:
        return False
    return len(keyword) >= 3 and keyword.endswith(("시", "군", "구", "동", "읍", "면", "역", "대교", "터널"))


def extract_core_segments(text):
    """긴 문장에서 검색 목적이 들어 있는 구간을 우선 남깁니다."""
    segments = re.split(r"[.!?]|[,，]|(?:\s+그리고\s+)|(?:\s+그런데\s+)|(?:\s+근데\s+)|(?:\s+하지만\s+)", text)
    if len(segments) <= 1:
        return text

    signal_terms = (
        set(PUBLIC_DATA_TERMS)
        | LOCATION_KEYWORDS
        | set(INTENT_TO_KEYWORD_MAP.keys())
        | {"데이터", "현황", "통계", "목록", "위치", "가격", "개수", "수량", "인원", "평균", "순위", "추이", "비교"}
    )
    core_segments = []
    for segment in segments:
        segment_lower = segment.lower()
        if any(term.lower() in segment_lower for term in signal_terms):
            core_segments.append(segment.strip())

    return " ".join(core_segments) if core_segments else text


def clean_user_query(text):
    """일상 대화 표현을 제거해 공공데이터 검색 목적이 드러나도록 정제합니다."""
    cleaned_text = extract_core_segments(text)

    for pattern in NOISE_PATTERNS:
        cleaned_text = re.sub(pattern, " ", cleaned_text)

    for phrase in NOISE_PHRASES:
        cleaned_text = cleaned_text.replace(phrase, " ")

    cleaned_text = re.sub(r"[,.!?;:()\[\]{}\"'“”‘’]", " ", cleaned_text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    return cleaned_text


def remove_duplicates(items):
    unique_items = []
    for item in items:
        if item and item not in unique_items:
            unique_items.append(item)
    return unique_items


def find_stock_company(text, keywords):
    searchable_text = text.lower() + " " + " ".join(keywords).lower()
    for company, aliases in STOCK_COMPANY_ALIASES.items():
        if any(alias in searchable_text for alias in aliases):
            return company
    return None


def refine_intent_keywords(keywords, original_text, cleaned_text):
    """사용자 요구를 반영해 검색 목적 중심 키워드로 재구성합니다."""
    refined = list(keywords)
    searchable_text = original_text.lower() + " " + cleaned_text.lower()

    stock_company = find_stock_company(searchable_text, refined)
    has_stock_context = stock_company or "주식" in refined or "주가" in searchable_text
    has_price_intent = any(term in searchable_text for term in STOCK_PRICE_INTENT_TERMS)

    if stock_company and has_stock_context:
        other_keywords = [
            keyword
            for keyword in refined
            if keyword not in STOCK_COMPANY_ALIASES[stock_company] and keyword not in {"오늘", "주식"}
        ]
        refined = []
        if "오늘" in searchable_text and "오늘" not in refined:
            refined.append("오늘")
        refined.append(stock_company)
        if "주식" not in refined:
            refined.append("주식")
        if has_price_intent:
            refined.append(f"{stock_company} 주가")
        refined.extend(other_keywords)
        return remove_duplicates(refined)

    return remove_duplicates(refined)


def add_intent_keywords(keywords, original_text, cleaned_text):
    """얼마, 어디, 몇 개 같은 의도어를 검색용 키워드로 바꿔 추가합니다."""
    expanded = list(keywords)
    searchable_text = original_text.lower() + " " + cleaned_text.lower()
    stock_company = find_stock_company(searchable_text, expanded)

    for phrase, mapped_keyword in INTENT_TO_KEYWORD_MAP.items():
        if phrase == "얼마" and "얼마나" in searchable_text:
            continue
        if stock_company and mapped_keyword == "가격":
            continue
        if phrase in searchable_text and mapped_keyword not in expanded:
            expanded.append(mapped_keyword)

    ability_phrases = (
        "갈 수", "볼 수", "받을 수", "댈 수", "알 수", "할 수", "쓸 수", "사용할 수",
        "갈 수도", "볼 수도", "받을 수도", "알 수도", "할 수도", "쓸 수도", "사용할 수도",
    )
    if (
        re.search(r"(?<![가-힣A-Za-z0-9])수[가은을의도]?(?![가-힣A-Za-z0-9])", searchable_text)
        and not any(phrase in searchable_text for phrase in ability_phrases)
        and "개수" not in expanded
    ):
        expanded.append("개수")

    if "자전거" in searchable_text and any(term in searchable_text for term in ("빌리", "대여")):
        expanded.extend(["대여소"])
    if "버스" in searchable_text and any(term in searchable_text for term in ("사람", "타는", "승하차")):
        expanded.extend(["승하차", "인원"])
    if any(term in searchable_text for term in ("막히", "붐비", "혼잡")):
        expanded.append("혼잡도")
    if any(term in searchable_text for term in ("방문객", "방문자", "입장객", "관광객", "놀러")) or ("사람" in searchable_text and "오는지" in searchable_text):
        expanded.append("방문객")
    if any(term in searchable_text for term in ("쓰레기", "폐기물", "음식물쓰레기")) and any(term in searchable_text for term in ("나오는", "나오는지", "배출")):
        expanded.append("배출량")
    if "산불" in searchable_text and any(term in searchable_text for term in ("났", "발생", "현황")):
        expanded.extend(["발생", "현황"])
    if "전기" in searchable_text and any(term in searchable_text for term in ("쓰는", "사용")):
        expanded.append("사용량")
    if "농산물" in searchable_text and "생산" in searchable_text:
        expanded.append("생산량")
    if any(term in searchable_text for term in ("태어", "출생")):
        expanded.append("출생아")
    if any(term in searchable_text for term in ("변한", "변화")):
        expanded.append("추이")
    if any(term in searchable_text for term in ("코스피", "코스닥")) and any(term in searchable_text for term in ("어떻게", "됐는지", "지수")):
        expanded.append("지수")
    if "공장" in searchable_text and any(term in searchable_text for term in ("얼마나", "있는지", "현황")):
        expanded.append("현황")
    if "문화재" in searchable_text and any(term in searchable_text for term in ("뭐가", "있는지", "현황")):
        expanded.append("현황")
    if any(term in searchable_text for term in ("정도", "얼마나")) and "가격" in expanded and not any(term in searchable_text for term in ("가격", "값", "주가", "환율", "기름값", "집값")):
        expanded = [keyword for keyword in expanded if keyword != "가격"]

    return remove_duplicates(expanded)


def add_public_data_synonyms(keywords):
    """공공데이터포털 검색에 더 잘 맞는 동의어와 복합 키워드를 추가합니다."""
    expanded = list(keywords)
    keyword_set = set(keywords)

    for required_keywords, synonym_keywords in PUBLIC_DATA_SYNONYM_RULES:
        if required_keywords.issubset(keyword_set):
            for synonym in synonym_keywords:
                if synonym not in expanded:
                    expanded.append(synonym)

    if {"주택가격", "부동산"} & keyword_set and "부동산 가격" not in expanded:
        expanded.append("부동산 가격")
    if {"토지가격", "토지"} & keyword_set and "공시지가" not in expanded:
        expanded.append("공시지가")
    if {"미세먼지", "농도"} <= keyword_set and "대기오염" not in expanded:
        expanded.append("대기오염")

    return remove_duplicates(expanded)


def prioritize_keywords(keywords):
    """검색 조건이 잘 보이도록 시간, 지역, 나머지 순서로 정렬합니다."""
    time_keywords = [keyword for keyword in keywords if keyword in TIME_KEYWORDS]
    location_keywords = [keyword for keyword in keywords if keyword not in time_keywords and is_location_keyword(keyword)]
    other_keywords = [keyword for keyword in keywords if keyword not in time_keywords and keyword not in location_keywords]
    return remove_duplicates(time_keywords + location_keywords + other_keywords)


def extract_keywords(text):
    """입력 문장에서 공공데이터포털 검색에 필요한 핵심 키워드를 추출합니다."""
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", text)
    candidates = []

    for token in tokens:
        normalized = normalize_token(token)

        if len(normalized) < 2:
            continue
        if normalized in STOPWORDS:
            continue
        if normalized.isdigit() and len(normalized) < 2:
            continue

        candidates.append(normalized)

    counts = Counter(candidates)
    ranked = sorted(
        counts.items(),
        key=lambda item: (-item[1], -len(item[0]), candidates.index(item[0])),
    )
    selected = [word for word, _ in ranked[:20]]

    return remove_duplicates([word for word in candidates if word in selected])


def classify_category(keywords, text):
    """키워드와 원문을 바탕으로 공공데이터 카테고리를 분류합니다."""
    searchable_text = " ".join(keywords) + " " + text
    scores = {}

    for category, category_keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for category_keyword in category_keywords:
            if category_keyword in searchable_text:
                score += 1
        if score:
            scores[category] = score

    if not scores:
        return "일반"

    return sorted(scores.items(), key=lambda item: (-item[1], ALLOWED_CATEGORIES.index(item[0])))[0][0]


def expand_keywords_for_public_data(keywords, category):
    """공공데이터포털 검색에 도움이 되는 보조 키워드를 자연스럽게 추가합니다."""
    expanded = list(keywords)
    keyword_set = set(keywords)

    if category == "부동산":
        if {"아파트", "전세"} & keyword_set and "주택" not in expanded:
            expanded.append("주택")
        if {"땅값", "부지", "면적", "건축", "공시지가"} & keyword_set and "토지" not in expanded:
            expanded.append("토지")
    elif category == "교통":
        if {"교통", "상황", "도로", "차량", "정체", "혼잡", "혼잡도", "사고", "통행", "대교", "다리", "터널"} & keyword_set:
            if "도로" not in expanded:
                expanded.append("도로")
        if {"버스", "지하철", "노선", "혼잡도", "승하차"} & keyword_set and "대중교통" not in expanded:
            expanded.append("대중교통")
    elif category in {"주식", "경제"}:
        if {"코스피", "코스닥", "지수", "주식"} & keyword_set:
            for related in ("증권", "금융"):
                if related not in expanded:
                    expanded.append(related)
    elif category == "에너지":
        if {"휘발유", "경유", "가격"} & keyword_set and "유가" not in expanded:
            expanded.append("유가")
    elif category == "의료":
        if {"병원", "개수"} <= keyword_set and "의료기관현황" not in expanded:
            expanded.append("의료기관현황")
    elif category == "인구":
        if {"인구", "개수"} & keyword_set and "주민등록인구" not in expanded:
            expanded.append("주민등록인구")
    elif category == "날씨":
        if {"기상청", "기상예보"} <= keyword_set and "기상청 기상예보 데이터" not in expanded:
            expanded.append("기상청 기상예보 데이터")

    if category not in expanded:
        expanded.append(category)

    return remove_duplicates(expanded)


def analyze_with_rules(text):
    """규칙 기반으로 공공데이터 검색용 키워드만 분석합니다."""
    cleaned_text = clean_user_query(text)
    keywords = extract_keywords(cleaned_text)
    keywords = add_intent_keywords(keywords, text, cleaned_text)
    keywords = refine_intent_keywords(keywords, text, cleaned_text)
    if not keywords:
        return []

    category = classify_category(keywords, cleaned_text)
    keywords = expand_keywords_for_public_data(keywords, category)
    keywords = add_public_data_synonyms(keywords)
    return prioritize_keywords(keywords)


def analyze_query(text):
    """입력 문장을 규칙 기반 로직으로 분석합니다."""
    return analyze_with_rules(text)


def format_keywords(keywords):
    """키워드를 #키워드 형식의 문자열로 변환합니다."""
    return " ".join(f"#{keyword}" for keyword in keywords)


def sanitize_filename(filename):
    """Windows 파일명에 사용할 수 없는 문자를 제거합니다."""
    filename = filename.strip()
    return re.sub(r'[\\/:*?"<>|]', "_", filename)


def save_keywords_to_desktop(text, filename):
    """현재 키워드 결과를 Windows 바탕화면에 지정한 파일명으로 저장합니다."""
    safe_filename = sanitize_filename(filename)
    if not safe_filename:
        raise ValueError("파일명을 입력하세요.")
    if not safe_filename.lower().endswith(".txt"):
        safe_filename += ".txt"

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(desktop_path, exist_ok=True)
    file_path = os.path.join(desktop_path, safe_filename)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)

    return file_path


def append_result_to_desktop_csv(input_sentence, keyword_text):
    """검색 결과를 바탕화면 CSV 파일에 누적 저장합니다."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(desktop_path, exist_ok=True)
    file_path = os.path.join(desktop_path, "keyword_results.csv")
    file_exists = os.path.exists(file_path)

    with open(file_path, "a", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["입력문장", "추출키워드"])
        writer.writerow([input_sentence, keyword_text])

    return file_path


def set_message(message):
    message_label.config(text=message)


def set_result(text):
    result_text.config(state="normal")
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, text)
    result_text.config(state="disabled")


def get_result_text():
    return result_text.get("1.0", tk.END).strip()


def search_keywords():
    """검색 버튼 동작: 공공데이터 검색용 키워드만 화면에 표시합니다."""
    text = input_text.get("1.0", tk.END).strip()

    if not text:
        set_result("")
        set_message("문장을 입력하세요.")
        return

    keywords = analyze_query(text)

    if not keywords:
        set_result("")
        set_message("추출된 키워드가 없습니다.")
        return

    formatted_keywords = format_keywords(keywords)
    set_result(formatted_keywords)

    try:
        saved_path = append_result_to_desktop_csv(text, formatted_keywords)
        set_message(f"키워드 추출 완료. {os.path.basename(saved_path)} 파일에 저장되었습니다.")
    except Exception as error:
        set_message(f"키워드 추출 완료. CSV 저장 중 오류가 발생했습니다: {error}")


def save_keywords():
    """저장 버튼 동작: 결과 영역의 키워드 문자열만 바탕화면에 저장합니다."""
    keyword_text = get_result_text()

    if not keyword_text:
        set_message("저장할 키워드가 없습니다.")
        return

    try:
        filename = filename_entry.get().strip()
        saved_path = save_keywords_to_desktop(keyword_text, filename)
        set_message(f"바탕화면에 {os.path.basename(saved_path)} 파일로 저장되었습니다.")
    except Exception as error:
        set_message(f"저장 중 오류가 발생했습니다: {error}")


root = tk.Tk()
root.title("프롬포트 키워드 추출 앱")
root.geometry("600x450")
root.resizable(False, False)

main_frame = tk.Frame(root, padx=16, pady=16)
main_frame.pack(fill="both", expand=True)

input_label = tk.Label(main_frame, text="프롬포트 또는 문장 입력", anchor="w")
input_label.pack(fill="x")

input_text = tk.Text(main_frame, height=8, wrap="word")
input_text.pack(fill="x", pady=(6, 12))

filename_label = tk.Label(main_frame, text="저장 파일명", anchor="w")
filename_label.pack(fill="x")

filename_entry = tk.Entry(main_frame)
filename_entry.insert(0, "keywords.txt")
filename_entry.pack(fill="x", pady=(6, 12))

button_frame = tk.Frame(main_frame)
button_frame.pack(fill="x", pady=(0, 12))

search_button = tk.Button(button_frame, text="검색", width=12, command=search_keywords)
search_button.pack(side="left", padx=(0, 8))

save_button = tk.Button(button_frame, text="저장", width=12, command=save_keywords)
save_button.pack(side="left")

result_label = tk.Label(main_frame, text="추출된 키워드", anchor="w")
result_label.pack(fill="x")

result_text = tk.Text(main_frame, height=5, wrap="word", state="disabled")
result_text.pack(fill="x", pady=(6, 12))

message_label = tk.Label(main_frame, text="", anchor="w", fg="#14532d")
message_label.pack(fill="x")

root.mainloop()

