"""
personalization/recommender.py

GraphTrip 개인화 추천 시스템의 핵심 모듈.
역할1(CF), 역할2(키워드 가중치), 역할4(여행 코스 최적화)와의 연동 포인트를 포함한다.

추천 흐름:
  1. 사용자가 선택한 키워드(user_keywords)와 매칭되는 장소들을 찾아 씨드로 구성한다.
  2. 역할1 CF 결과(cf_places)가 있으면 씨드에 추가한다.
  3. place_graph.build_place_graph()로 키워드 유사도 기반 Weighted Graph를 생성한다.
     (역할2의 keyword_weights가 있으면 Weighted Jaccard 자동 적용)
  4. random_walk_with_restart()로 씨드 노드 주변 장소의 방문 횟수를 수집한다.
  5. personalized_pagerank()로 방문 횟수를 PPR 점수로 정규화한다.
  6. 이미 좋아요를 누른 장소를 제외하고 top_k개의 장소를 반환한다.
  7. 반환값에 lat/lng을 포함하여 역할4(Dijkstra)가 바로 활용할 수 있게 한다.
"""

from personalization.place_graph import build_place_graph
from personalization.random_walk import random_walk_with_restart
from personalization.pagerank import personalized_pagerank
from keyword_system.keyword_data import get_place_dict, get_place_keywords


# -------------------------------------------------------
# 내부 유틸: 키워드 → 매칭 장소 탐색
# -------------------------------------------------------
def _find_places_by_keywords(
    user_keywords: list[str],
    place_keywords: dict[int, list[str]],
) -> list[int]:
    """
    사용자가 선택한 키워드 중 하나라도 포함하는 장소 ID 리스트를 반환한다.
    이 장소들이 RWR의 씨드 노드가 된다.

    Args:
        user_keywords:  사용자가 선택한 관심 키워드 리스트.
                        예) ["야경", "힐링"]
        place_keywords: get_place_keywords()의 캐시 결과.

    Returns:
        키워드 매칭 장소 ID 리스트. 매칭 키워드 수가 많은 장소가 앞에 온다.
    """
    user_kw_set = set(user_keywords)

    # 장소별 매칭 키워드 수 계산 → 많이 매칭될수록 씨드 우선순위 높음
    scored = []
    for place_id, keywords in place_keywords.items():
        match_count = len(set(keywords) & user_kw_set)
        if match_count > 0:
            scored.append((place_id, match_count))

    # 매칭 수 내림차순 정렬
    scored.sort(key=lambda x: x[1], reverse=True)
    return [place_id for place_id, _ in scored]


# -------------------------------------------------------
# 내부 유틸: 추천 이유 생성
# -------------------------------------------------------
def _get_matched_keywords(
    user_keywords: list[str],
    target_place_id: int,
    place_keywords: dict[int, list[str]],
) -> list[str]:
    """
    사용자 선택 키워드와 추천 장소의 키워드 교집합을 반환한다.

    Args:
        user_keywords:    사용자가 선택한 관심 키워드 리스트.
        target_place_id:  매칭할 추천 후보 장소 ID.
        place_keywords:   get_place_keywords()의 캐시 결과.

    Returns:
        교집합 키워드 리스트. 추천 이유 문자열 생성에 사용한다.
    """
    user_kw_set = set(user_keywords)
    target_kw_set = set(place_keywords.get(target_place_id, []))
    return list(user_kw_set & target_kw_set)


def _build_reason_string(
    matched_keywords: list[str],
    from_cf: bool = False,
) -> str:
    """
    매칭된 키워드로 사람이 읽기 좋은 추천 이유 문자열을 생성한다.

    Returns:
        예) "'야경', '힐링' 키워드 기반 추천"
            또는 "취향이 비슷한 사용자들이 선호한 장소" (CF 장소, 매칭 없을 때)
    """
    if not matched_keywords:
        if from_cf:
            return "취향이 비슷한 사용자들이 선호한 장소"
        return "선택 키워드와 연관된 장소 추천"

    keyword_str = ", ".join(f"'{kw}'" for kw in matched_keywords[:3])
    suffix = f" 외 {len(matched_keywords) - 3}개" if len(matched_keywords) > 3 else ""
    return f"{keyword_str}{suffix} 키워드 기반 추천"


# -------------------------------------------------------
# 메인 추천 함수
# -------------------------------------------------------
def recommend_places(
    user_keywords: list[str],
    liked_places: list[int] = None,
    cf_places: list[int] = None,
    top_k: int = 5,
    graph_threshold: float = 0.2,
    walk_steps: int = None,
) -> list[dict]:
    """
    사용자가 선택한 키워드 기반 Personalized PageRank 장소 추천을 수행한다.

    [씨드 구성 전략]
    사용자가 선택한 키워드(user_keywords)와 매칭되는 장소들을 RWR의 씨드로 사용한다.
    역할1 CF 결과(cf_places)가 있으면 씨드에 추가하여 추천을 강화한다.

    [역할1 연동]
    cf_places에 역할1의 Collaborative Filtering 결과(유사 사용자가 선호한 장소 ID 리스트)를
    전달하면, 키워드 매칭 씨드에 추가하여 RWR을 수행한다.
    역할1 구현 전에는 cf_places=None으로 호출해도 정상 동작한다.

    [역할2 연동]
    place_graph.build_place_graph() 내부에서 역할2의 get_keyword_weights()를 자동 호출한다.
    역할2 구현 전에는 일반 Jaccard로 폴백하여 정상 동작한다.

    [역할4 연동]
    반환값의 각 항목에 "lat", "lng" 필드를 포함한다.
    역할4(여행 코스 최적화)는 이 좌표로 Dijkstra 최적 경로를 계산한다.

    Args:
        user_keywords:    사용자가 선택한 관심 키워드 리스트. (필수)
                          예) ["야경", "힐링", "사진맛집"]
                          이 키워드와 매칭되는 장소들이 RWR 씨드가 된다.
        liked_places:     사용자가 이미 좋아요/저장한 장소 ID 리스트.
                          추천 결과에서 제외하는 데 사용한다.
                          None이면 제외 없이 전체 추천한다.
        cf_places:        역할1 CF가 찾아낸 유사 사용자의 선호 장소 ID 리스트.
                          None이면 키워드 씨드만으로 추천한다.
        top_k:            반환할 추천 장소 수. 기본값 5.
        graph_threshold:  장소 그래프 생성 시 최소 유사도. 기본값 0.2.
        walk_steps:       Random Walk 스텝 수.
                          None이면 max(1000, 장소 수 × 100)으로 자동 결정.

    Returns:
        추천 장소 리스트 (score 내림차순 정렬, 최대 top_k개).
        각 항목의 구조:
        {
            "place_id":         int,        # 장소 고유 ID
            "place_name":       str,        # 장소명
            "lat":              float,      # 위도  (역할4 Dijkstra용)
            "lng":              float,      # 경도  (역할4 Dijkstra용)
            "score":            float,      # PPR 점수 (0~1)
            "matched_keywords": list[str],  # 사용자 키워드와 공통 키워드
            "reason":           str,        # 추천 이유 요약 문자열
            "score_breakdown": {
                "visit_count":      int,    # RWR 방문 횟수
                "max_graph_weight": float,  # 씨드 노드와의 최대 엣지 가중치
                "seed_source":      str,    # "keyword" | "cf" | "keyword+cf"
            }
        }

    Raises:
        ValueError: user_keywords가 비어 있는 경우.
        ValueError: user_keywords와 매칭되는 장소가 하나도 없는 경우.
    """
    if not user_keywords:
        raise ValueError(
            "user_keywords가 비어 있습니다. 관심 키워드를 1개 이상 전달하세요."
        )

    liked_places = liked_places or []
    cf_places = cf_places or []

    # 데이터 로딩
    place_dict = get_place_dict()
    place_keywords = get_place_keywords()

    # 1단계: 키워드 매칭 장소 탐색 → RWR 씨드
    keyword_seed_places = _find_places_by_keywords(user_keywords, place_keywords)

    if not keyword_seed_places:
        raise ValueError(
            f"선택한 키워드 {user_keywords}와 매칭되는 장소가 없습니다. "
            "키워드를 변경하거나 places.json 데이터를 확인하세요."
        )

    # 2단계: CF 결과를 씨드에 추가 (중복 제거, 순서 유지)
    seed_places = list(dict.fromkeys(keyword_seed_places + cf_places))

    # 씨드 출처 표시 (score_breakdown용)
    keyword_seed_set = set(keyword_seed_places)
    cf_set = set(cf_places)

    def _seed_source(place_id: int) -> str:
        in_kw = place_id in keyword_seed_set
        in_cf = place_id in cf_set
        if in_kw and in_cf:
            return "keyword+cf"
        if in_kw:
            return "keyword"
        return "cf"

    # 3단계: 키워드 유사도 기반 Weighted Graph 생성 (역할2 가중치 자동 반영)
    graph = build_place_graph(threshold=graph_threshold)

    # 4단계: Random Walk with Restart
    visit_count = random_walk_with_restart(
        graph=graph,
        start_nodes=seed_places,
        steps=walk_steps,
    )

    # 5단계: PPR 점수 정규화 (이미 좋아요한 장소 제외)
    scores = personalized_pagerank(
        visit_count=visit_count,
        exclude_places=liked_places,
    )

    # 6단계: 결과 조립
    result = []

    for place_id, score in scores.items():
        place_info = place_dict.get(place_id, {})
        matched_keywords = _get_matched_keywords(
            user_keywords, place_id, place_keywords
        )
        from_cf = place_id in cf_set and place_id not in keyword_seed_set

        max_graph_weight = max(
            (graph.get(s, {}).get(place_id, 0.0) for s in seed_places),
            default=0.0,
        )

        result.append({
            "place_id":         place_id,
            "place_name":       place_info.get("name", f"장소_{place_id}"),

            # 역할4(Dijkstra)가 사용할 좌표
            "lat":              place_info.get("lat"),
            "lng":              place_info.get("lng"),

            "score":            round(score, 4),
            "matched_keywords": matched_keywords,
            "reason":           _build_reason_string(matched_keywords, from_cf),

            "score_breakdown": {
                "visit_count":      visit_count.get(place_id, 0),
                "max_graph_weight": round(max_graph_weight, 4),
                "seed_source":      _seed_source(place_id)
                                    if place_id in seed_places else "recommended",
            },
        })

    # score 내림차순 정렬 후 top_k 반환
    result.sort(key=lambda x: x["score"], reverse=True)
    return result[:top_k]


# -------------------------------------------------------
# 역할4 연동용 진입점
# -------------------------------------------------------
def get_place_ids_for_route(
    recommendations: list[dict],
) -> list[int]:
    """
    recommend_places()의 결과를 받아
    역할4(optimize_travel_route)에 넘길 place_id 리스트만 추출한다.

    실제 서비스 흐름:
        recommendations = recommend_places(
            user_keywords=["야경", "힐링"],
            liked_places=user_liked_places,
            cf_places=cf_result,
        )
        # 상세 정보 출력
        for r in recommendations:
            print(r["place_name"], r["reason"])

        # 역할4에 ID 리스트 전달
        place_ids = get_place_ids_for_route(recommendations)
        result = optimize_travel_route(
            start_place_id=...,
            recommended_place_ids=place_ids,
        )

    Args:
        recommendations: recommend_places()의 반환값.

    Returns:
        추천 장소 ID 리스트. 예) [2, 7, 3, 5, 4]
    """
    return [r["place_id"] for r in recommendations]
