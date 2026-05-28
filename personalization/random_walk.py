"""
personalization/random_walk.py

Weighted Graph 위에서 Random Walk with Restart(RWR)를 수행한다.

RWR 작동 원리:
  1. start_nodes 중 하나에서 출발한다.
  2. 매 스텝마다 restart_prob 확률로 start_nodes 중 하나로 돌아간다.
  3. 그렇지 않으면 현재 노드의 이웃 중 엣지 가중치에 비례해 다음 노드를 선택한다.
  4. 충분한 steps 후 각 노드의 방문 횟수가 Personalized PageRank 점수에 근사한다.
"""

import random


def random_walk_with_restart(
    graph: dict[int, dict[int, float]],
    start_nodes: list[int],
    restart_prob: float = 0.3,
    steps: int = None,
    seed: int = None,
) -> dict[int, int]:
    """
    Weighted Graph에서 Random Walk with Restart를 수행한다.

    Args:
        graph:        place_graph.build_place_graph()의 반환값.
                      graph[node][neighbor] = 가중치(float).
        start_nodes:  워크를 시작하거나 재시작할 씨드 노드 리스트.
                      역할1의 CF 결과(유사 사용자 선호 장소)가 합쳐진 리스트를 받는다.
        restart_prob: 매 스텝마다 start_nodes로 돌아갈 확률. 기본값 0.3.
        steps:        총 워크 스텝 수.
                      None이면 max(1000, 장소 수 × 100)으로 자동 결정한다.
        seed:         재현 가능한 결과를 원할 때 사용할 랜덤 시드.
                      None이면 매번 다른 결과를 반환한다.

    Returns:
        visit_count[node] = 해당 노드를 방문한 횟수 (int).

    Raises:
        ValueError: start_nodes가 비어 있거나 graph에 없는 노드를 포함한 경우.
    """
    if not start_nodes:
        raise ValueError("start_nodes가 비어 있습니다.")

    # start_nodes에 그래프에 없는 노드가 있으면 제거하고 경고
    valid_start_nodes = [n for n in start_nodes if n in graph]
    if len(valid_start_nodes) < len(start_nodes):
        missing = set(start_nodes) - set(valid_start_nodes)
        print(
            f"[경고] start_nodes에 그래프에 없는 노드 포함: {missing} → 제외됨"
        )
    if not valid_start_nodes:
        raise ValueError(
            "start_nodes의 모든 노드가 그래프에 존재하지 않습니다."
        )

    # steps 자동 결정: 장소 수가 많을수록 수렴에 더 많은 스텝이 필요
    if steps is None:
        steps = max(1000, len(graph) * 100)

    # 재현성을 위한 시드 고정 (데모/발표 시 seed=42 등 고정 권장)
    if seed is not None:
        random.seed(seed)

    # 방문 횟수 초기화
    visit_count: dict[int, int] = {node: 0 for node in graph}

    current = random.choice(valid_start_nodes)

    for _ in range(steps):
        visit_count[current] += 1

        # restart_prob 확률로 씨드 노드 중 하나로 복귀
        if random.random() < restart_prob:
            current = random.choice(valid_start_nodes)
            continue

        neighbors = graph[current]

        # 고립 노드(이웃 없음)면 restart
        if not neighbors:
            current = random.choice(valid_start_nodes)
            continue

        # 엣지 가중치에 비례한 확률적 이동
        nodes = list(neighbors.keys())
        weights = list(neighbors.values())

        current = random.choices(nodes, weights=weights, k=1)[0]

    return visit_count
