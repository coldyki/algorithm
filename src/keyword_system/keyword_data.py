"""
keyword_system/keyword_data.py

역할2(키워드 분석 시스템)가 관리하는 장소 데이터 로딩 모듈.
역할3(개인화 추천)에서 장소별 키워드 및 장소 정보를 가져올 때 사용한다.

[역할2 연동 포인트]
- get_keyword_weights(): 역할2가 Topic-Sensitive Ranking / Inverted Index로
  계산한 키워드 중요도(가중치)를 반환하도록 역할2 팀원이 이 함수를 구현한다.
  역할3은 이 함수를 place_graph.py에서 호출하여 가중 Jaccard에 반영한다.
"""

import json
import os

# -------------------------------------------------------
# 경로 설정: 실행 위치에 무관하게 data/ 디렉토리를 찾는다
# (FastAPI 서버 통합 시에도 경로가 깨지지 않음)
# -------------------------------------------------------
_BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
_DEFAULT_PLACES_PATH = os.path.join(_BASE_DIR, "data", "places.json")


# -------------------------------------------------------
# 장소 데이터 로딩
# -------------------------------------------------------
def load_places(path: str = None) -> list[dict]:
    """
    places.json을 읽어 장소 목록을 반환한다.

    Args:
        path: JSON 파일 경로. None이면 기본 경로(data/places.json)를 사용.

    Returns:
        장소 dict의 리스트.
        각 dict에는 id, name, lat, lng, keywords 필드가 포함된다.
    """
    if path is None:
        path = _DEFAULT_PLACES_PATH

    with open(path, "r", encoding="utf-8") as f:
        places = json.load(f)

    return places


def get_place_keywords() -> dict[int, list[str]]:
    """
    place_id → 키워드 리스트 매핑을 반환한다.

    Returns:
        예) {1: ["감성적인", "사진맛집", ...], 2: [...], ...}
    """
    places = load_places()
    return {place["id"]: place["keywords"] for place in places}


def get_place_dict() -> dict[int, dict]:
    """
    place_id → 장소 전체 정보(name, lat, lng, keywords) 매핑을 반환한다.
    역할4(Dijkstra)가 좌표를 조회할 때도 이 함수를 사용한다.

    Returns:
        예) {1: {"id": 1, "name": "황리단길", "lat": 35.8362, "lng": 129.2181, ...}}
    """
    places = load_places()
    return {place["id"]: place for place in places}


# -------------------------------------------------------
# [역할2 연동 포인트]
# 역할2 팀원이 아래 함수를 Inverted Index / Topic-Sensitive Ranking
# 결과를 반영하여 완성한다.
# 역할3(place_graph.py)은 이 함수를 호출하여 키워드 가중치를 그래프에 반영한다.
# -------------------------------------------------------
def get_keyword_weights() -> dict[str, float]:
    """
    키워드별 중요도 가중치를 반환한다.

    역할2가 Inverted Index / Topic-Sensitive Ranking으로 계산한
    키워드 중요도를 여기서 반환한다.
    역할2 구현 전까지는 모든 키워드의 가중치를 1.0(동일)으로 처리한다.

    Returns:
        예) {"야경": 1.8, "힐링": 1.5, "감성적인": 1.3, "사진맛집": 1.2, ...}
        (역할2 구현 전 기본값: 빈 dict → place_graph.py에서 기본 Jaccard 적용)
    """
    # TODO: 역할2 팀원이 실제 가중치로 교체한다.
    # 현재는 빈 dict를 반환 → place_graph.py가 일반 Jaccard로 폴백(fallback)한다.
    return {}
