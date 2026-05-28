"""
personalization/recommender.py

GraphTrip 개인화 추천 시스템의 핵심 모듈.
역할1(CF), 역할2(키워드 가중치), 역할4(여행 코스 최적화)와의 연동 포인트를 포함한다.

추천 흐름:
  1. 사용자의 liked_places + 역할1 CF 결과(cf_places)를 합쳐 씨드 노드를 구성한다.
  2. place_graph.build_place_graph()로 키워드 유사도 기반 Weighted Graph를 생성한다.
     (역할2의 keyword_weights가 있으면 Weighted Jaccard 자동 적용)
  3. random_walk_with_restart()로 씨드 노드 주변 장소의 방문 횟수를 수집한다.
  4. personalized_pagerank()로 방문 횟수를 PPR 점수로 정규화한다.
  5. 이미 좋아요를 누른 장소를 제외하고 top_k개의 장소를 반환한다.
  6. 반환값에 lat/lng을 포함하여 역할4(Dijkstra)가 바로 활용할 수 있게 한다.
"""

from personalization.place_graph import build_place_graph
from personalization.random_walk import random_walk_with_restart
from personalization.pagerank import personalized_pagerank
from keyword_system.keyword_data import get_place_dict, get_place_keywords


# -------------------------------------------------------
# 내부 유틸: 추천 이유 생성
# -------------------------------------------------------
def _get_matched_keywords(
    seed_places: list[int],
    target_place_id: int,
    place_keywords: dict[int, list[str]],
) -> list[str]:
    """
    씨드 장소들의 키워드와 추천 장소의 키워드 교집합을 반환한다.

    Args:
        seed_places:      좋아요 + CF 결과를 합친 씨드 장소 ID 리스트.
        target_place_id:  매칭할 추천 후보 장소 ID.
        place_keywords:   get_place_keywords()의 캐시 결과.

    Returns:
        교집합 키워드 리스트. 추천 이유 문자열 생성에 사용한다.
    """
    seed_keywords: set[str] = set()

    for place_id in seed_places:
        if place_id in place_keywords:
            seed_keywords.update(place_keywords[place_id])

    target_keywords = set(place_keywords.get(target_place_id, []))

    return list(seed_keywords & target_keywords)


def _build_reason_string(matched_keywords: list[str]) -> str:
    """
    매칭된 키워드로 사람이 읽기 좋은 추천 이유 문자열을 생성한다.

    Returns:
        예) "'야경', '로맨틱한' 키워드 기반 추천"
            또는 "취향과 유사한 장소 추천" (매칭 키워드 없을 때)
    """
    if not matched_keywords:
        return "취향과 유사한 장소 추천"

    keyword_str = ", ".join(f"'{kw}'" for kw in matched_keywords[:3])
    suffix = f" 외 {len(matched_keywords) - 3}개" if len(matched_keywords) > 3 else ""
    return f"{keyword_str}{suffix} 키워드 기반 추천"


# -------------------------------------------------------
# 메인 추천 함수
# -------------------------------------------------------
def recommend_places(
    liked_places: list[int],
    cf_places: list[int] = None,
    top_k: int = 5,
    graph_threshold: float = 0.2,
    walk_steps: int = None,
    walk_seed: int = None,
) -> list[dict]:
    """
    Personalized PageRank 기반 장소 추천을 수행한다.

    [역할1 연동]
    cf_places에 역할1의 Collaborative Filtering 결과(유사 사용자가 선호한 장소 ID 리스트)를
    전달하면, liked_places와 합쳐진 확장 씨드로 Random Walk를 수행한다.
    역할1 구현 전에는 cf_places=None으로 호출해도 정상 동작한다.

    [역할4 연동]
    반환값의 각 항목에 "lat", "lng" 필드를 포함한다.
    역할4(여행 코스 최적화)는 이 좌표로 Dijkstra 최적 경로를 계산한다.

    Args:
        liked_places:     사용자가 좋아요/저장한 장소 ID 리스트. (필수)
        cf_places:        역할1 CF가 찾아낸 유사 사용자의 선호 장소 ID 리스트.
                          None이면 liked_places만으로 추천한다.
        top_k:            반환할 추천 장소 수. 기본값 5.
        graph_threshold:  장소 그래프 생성 시 최소 유사도. 기본값 0.2.
        walk_steps:       Random Walk 스텝 수.
                          None이면 max(1000, 장소 수 × 100)으로 자동 결정.
        walk_seed:        랜덤 시드. 발표/테스트 시 고정값(예: 42)을 권장한다.
                          None이면 매번 다른 결과를 반환한다.

    Returns:
        추천 장소 리스트 (score 내림차순 정렬, 최대 top_k개).
        각 항목의 구조:
        {
            "place_id":        int,          # 장소 고유 ID
            "place_name":      str,          # 장소명
            "lat":             float,        # 위도  (역할4 Dijkstra용)
            "lng":             float,        # 경도  (역할4 Dijkstra용)
            "score":           float,        # PPR 점수 (0~1)
            "matched_keywords": list[str],   # 씨드 장소와 공통 키워드
            "reason":          str,          # 추천 이유 요약 문자열
            "score_breakdown": {             # 점수 세부 내역 (디버깅/발표용)
                "visit_count":       int,    # RWR 방문 횟수
                "max_graph_weight":  float,  # 씨드 노드와의 최대 엣지 가중치
                "seed_source":       str,    # "liked" | "cf" | "liked+cf"
            }
        }

    Raises:
        ValueError: liked_places가 비어 있는 경우.
    """
    if not liked_places:
        raise ValueError("liked_places가 비어 있습니다. 좋아요한 장소를 1개 이상 전달하세요.")

    # 씨드 구성: liked_places + CF 결과(있으면) → 중복 제거
    cf_places = cf_places or []
    seed_places = list(dict.fromkeys(liked_places + cf_places))  # 순서 유지 중복 제거

    # 씨드 출처 표시 (score_breakdown용)
    liked_set = set(liked_places)
    cf_set = set(cf_places)

    def _seed_source(place_id: int) -> str:
        in_liked = place_id in liked_set
        in_cf = place_id in cf_set
        if in_liked and in_cf:
            return "liked+cf"
        if in_liked:
            return "liked"
        return "cf"

    # 데이터 로딩
    place_dict = get_place_dict()
    place_keywords = get_place_keywords()

    # 1단계: 키워드 유사도 기반 Weighted Graph 생성 (역할2 가중치 자동 반영)
    graph = build_place_graph(threshold=graph_threshold)

    # 2단계: Random Walk with Restart
    visit_count = random_walk_with_restart(
        graph=graph,
        start_nodes=seed_places,
        steps=walk_steps,
        seed=walk_seed,
    )

    # 3단계: PPR 점수 정규화 (이미 좋아요한 장소 제외)
    scores = personalized_pagerank(
        visit_count=visit_count,
        exclude_places=liked_places,  # CF 장소는 새로운 발견이므로 제외하지 않음
    )

    # 4단계: 결과 조립
    result = []

    for place_id, score in scores.items():
        place_info = place_dict.get(place_id, {})
        matched_keywords = _get_matched_keywords(
            seed_places, place_id, place_keywords
        )

        # 씨드 노드와의 최대 엣지 가중치 (그래프에서의 직접 연결 강도)
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
            "reason":           _build_reason_string(matched_keywords),

            # 점수 세부 내역: 디버깅 및 발표 설명용
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
# 역할4 연결 함수
# -------------------------------------------------------
def get_place_ids_for_route(
    liked_places: list[int],
    cf_places: list[int] = None,
    top_k: int = 5,
    walk_seed: int = None,
) -> list[int]:
    """
    역할4(optimize_travel_route)에 바로 넘길 수 있는
    추천 장소 ID 리스트만 반환하는 편의 함수.

    사용 예:
        from personalization.recommender import get_place_ids_for_route
        from route_optimizer import optimize_travel_route

        place_ids = get_place_ids_for_route(liked_places=[1, 10])
        result = optimize_travel_route(
            start_place_id=1,
            recommended_place_ids=place_ids
        )
    """
    recommendations = recommend_places(
        liked_places=liked_places,
        cf_places=cf_places,
        top_k=top_k,
        walk_seed=walk_seed,
    )
    return [r["place_id"] for r in recommendations]
