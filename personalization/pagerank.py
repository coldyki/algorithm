"""
personalization/pagerank.py

Random Walk with Restart의 방문 횟수를 정규화하여
Personalized PageRank(PPR) 점수로 변환한다.

[수학적 근거]
  충분히 많은 steps에서 RWR의 정상 분포(stationary distribution)는
  restart 벡터를 개인화 벡터로 사용하는 PPR의 수렴값과 동치이다.
  따라서 방문 횟수를 전체 방문 횟수로 나눈 값이 PPR 점수의 근사치가 된다.

  참고: Tong et al., "Fast Random Walk with Restart and Its Applications", ICDM 2006
"""


def personalized_pagerank(
    visit_count: dict[int, int],
    exclude_places: list[int] = None,
) -> dict[int, float]:
    """
    RWR 방문 횟수를 PPR 점수(0~1)로 정규화하여 반환한다.

    Args:
        visit_count:     random_walk_with_restart()의 반환값.
                         visit_count[place_id] = 방문 횟수.
        exclude_places:  점수 계산에서 제외할 장소 ID 리스트.
                         보통 사용자가 이미 좋아요를 누른 장소를 전달한다.

    Returns:
        scores[place_id] = PPR 점수(float, 0~1).
        방문 횟수가 0이거나 제외된 장소는 결과에 포함되지 않는다.
    """
    if exclude_places is None:
        exclude_places = []

    exclude_set = set(exclude_places)

    # 원본 visit_count를 수정하지 않기 위해 복사본을 사용
    filtered = {
        place_id: count
        for place_id, count in visit_count.items()
        if place_id not in exclude_set and count > 0
    }

    total_visits = sum(filtered.values())

    if total_visits == 0:
        return {}

    scores = {
        place_id: count / total_visits
        for place_id, count in filtered.items()
    }

    return scores
