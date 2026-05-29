"""
personalization/place_graph.py

장소 간 키워드 유사도 기반 Weighted Graph를 생성한다.

[역할2 연동]
- keyword_data.get_keyword_weights()를 통해 역할2가 계산한 키워드 중요도를
  가중 Jaccard 유사도 계산에 반영한다.
- 역할2 구현 전에는 모든 키워드 가중치를 1.0으로 취급(일반 Jaccard와 동일).

[역할3 내부 사용]
- recommender.py의 recommend_places()에서 호출한다.
"""

from keyword_system.keyword_data import (
    get_place_keywords,
    get_keyword_weights,
)


# -------------------------------------------------------
# 유사도 계산
# -------------------------------------------------------
def jaccard_similarity(
    keywords1: list[str],
    keywords2: list[str],
) -> float:
    """
    두 장소의 키워드 집합에 대해 일반 Jaccard 유사도를 계산한다.

    Returns:
        0.0 ~ 1.0 사이의 유사도 값.
    """
    set1 = set(keywords1)
    set2 = set(keywords2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union


def weighted_jaccard_similarity(
    keywords1: list[str],
    keywords2: list[str],
    keyword_weights: dict[str, float],
) -> float:
    """
    키워드별 중요도 가중치를 반영한 Weighted Jaccard 유사도를 계산한다.

    교집합 가중치 합 / 합집합 가중치 합으로 계산한다.
    역할2가 get_keyword_weights()에 가중치를 채워 넣으면 자동으로 반영된다.

    Args:
        keywords1: 첫 번째 장소의 키워드 리스트.
        keywords2: 두 번째 장소의 키워드 리스트.
        keyword_weights: 키워드 → 가중치 dict (역할2 제공).
                         없는 키워드는 기본값 1.0으로 처리.

    Returns:
        0.0 ~ 1.0 사이의 가중 유사도 값.
    """
    set1 = set(keywords1)
    set2 = set(keywords2)

    union_kw = set1 | set2

    if not union_kw:
        return 0.0

    intersection_score = sum(
        keyword_weights.get(kw, 1.0) for kw in set1 & set2
    )
    union_score = sum(
        keyword_weights.get(kw, 1.0) for kw in union_kw
    )

    return intersection_score / union_score


# -------------------------------------------------------
# 그래프 생성
# -------------------------------------------------------
def build_place_graph(threshold: float = 0.2) -> dict[int, dict[int, float]]:
    """
    모든 장소 쌍에 대해 키워드 유사도를 계산하고,
    threshold 이상인 쌍만 엣지로 연결한 Weighted Graph를 반환한다.

    역할2의 keyword_weights가 비어 있으면 일반 Jaccard를 사용하고,
    채워져 있으면 Weighted Jaccard를 적용한다.

    Args:
        threshold: 그래프에 엣지를 추가할 최소 유사도. 기본값 0.2.

    Returns:
        graph[place_id][neighbor_id] = 유사도(float) 형태의 인접 딕셔너리.

    Raises:
        ValueError: threshold가 0 이상 1 이하 범위를 벗어난 경우.
    """
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(
            f"threshold는 0.0 ~ 1.0 사이여야 합니다. 입력값: {threshold}"
        )

    place_keywords = get_place_keywords()
    keyword_weights = get_keyword_weights()  # 역할2 연동: 가중치 가져오기
    use_weighted = bool(keyword_weights)     # 역할2 구현 전이면 일반 Jaccard 사용

    graph: dict[int, dict[int, float]] = {}
    place_ids = list(place_keywords.keys())

    for place1_id in place_ids:
        graph[place1_id] = {}

        for place2_id in place_ids:
            if place1_id == place2_id:
                continue

            if use_weighted:
                similarity = weighted_jaccard_similarity(
                    place_keywords[place1_id],
                    place_keywords[place2_id],
                    keyword_weights,
                )
            else:
                similarity = jaccard_similarity(
                    place_keywords[place1_id],
                    place_keywords[place2_id],
                )

            if similarity >= threshold:
                graph[place1_id][place2_id] = similarity

    # 고립 노드 경고: threshold가 너무 높으면 Random Walk가 start_nodes 루프만 돔
    isolated = [
        pid for pid, neighbors in graph.items() if not neighbors
    ]
    if isolated:
        print(
            f"[경고] 고립 노드 {len(isolated)}개 발생 (threshold={threshold}): "
            f"{isolated}\n"
            f"  → threshold를 낮추거나 데이터에 키워드를 추가하세요."
        )

    return graph
