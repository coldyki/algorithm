from route_optimizer import (
    load_places,
    load_distance_graph,
    floyd_warshall,
    create_optimized_route_by_dijkstra,
    create_optimized_route_by_floyd,
    calculate_route_distance_by_dijkstra,
    calculate_route_distance_by_floyd,
    get_route_segments_by_dijkstra,
    get_route_segments_by_floyd,
    print_route_result
)


def run_test_case(test_case, places, graph, all_pairs_distances):
    """
    하나의 사용자 추천 결과에 대해 코스 최적화를 수행한다.
    팀원1, 2, 3의 추천 결과가 연결되기 전까지는 더미 테스트 케이스를 사용한다.
    """

    user_name = test_case["user_name"]
    start_place_id = test_case["start_place_id"]
    recommended_place_ids = test_case["recommended_place_ids"]

    print(f"\n\n사용자 테스트 케이스: {user_name}")

    # 기존 추천 순서의 총 이동 거리 계산
    original_distance = calculate_route_distance_by_dijkstra(
        graph,
        recommended_place_ids
    )

    # Dijkstra + Greedy 방식 코스 생성
    dijkstra_route, dijkstra_distance = create_optimized_route_by_dijkstra(
        graph,
        start_place_id,
        recommended_place_ids
    )

    # Floyd-Warshall + Greedy 방식 코스 생성
    floyd_route, floyd_distance = create_optimized_route_by_floyd(
        all_pairs_distances,
        start_place_id,
        recommended_place_ids
    )

    # 구간별 이동 거리 계산
    dijkstra_segments = get_route_segments_by_dijkstra(graph, dijkstra_route)
    floyd_segments = get_route_segments_by_floyd(all_pairs_distances, floyd_route)

    # 출력
    print_route_result(
        places=places,
        start_place_id=start_place_id,
        recommended_place_ids=recommended_place_ids,
        original_distance=original_distance,
        dijkstra_route=dijkstra_route,
        dijkstra_distance=dijkstra_distance,
        floyd_route=floyd_route,
        floyd_distance=floyd_distance,
        dijkstra_segments=dijkstra_segments,
        floyd_segments=floyd_segments
    )


def main():
    """
    GraphTrip 팀원4 여행 코스 최적화 실행 파일

    현재 목표:
    - 팀원들과 기능을 합치기 전, 팀원4 개인 모듈을 독립 실행 가능하게 완성한다.
    - 팀원1, 2, 3의 추천 결과가 아직 연결되지 않았으므로 더미 추천 장소 ID를 사용한다.
    - 추후 팀원 추천 결과가 연결되면 recommended_place_ids만 교체하면 된다.

    담당 기능:
    - 추천된 경주 여행 장소들을 입력받는다.
    - 장소 간 거리 데이터를 Graph로 구성한다.
    - Dijkstra Algorithm과 Greedy Algorithm을 사용하여 효율적인 여행 코스를 생성한다.
    - Floyd-Warshall Algorithm을 사용하여 모든 장소 쌍 최단거리 테이블을 계산한다.
    - 기존 추천 순서와 최적화된 코스의 총 이동 거리를 비교한다.
    """

    places_file = "data/places.json"
    distances_file = "data/distances.csv"

    places = load_places(places_file)
    graph = load_distance_graph(distances_file)

    # 알고리즘: Floyd-Warshall Algorithm
    # 모든 장소 쌍 최단거리 테이블을 한 번 미리 계산한다.
    all_pairs_distances = floyd_warshall(graph)

    # 팀원1, 2, 3의 추천 결과를 가정한 더미 테스트 케이스
    # 추후 실제 추천 시스템과 연결하면 이 리스트 대신 추천 결과를 넘겨받으면 된다.
    test_cases = [
        {
            "user_name": "사용자 A - 감성/데이트 추천",
            "start_place_id": 1,
            "recommended_place_ids": [1, 2, 3, 8, 10]
        },
        {
            "user_name": "사용자 B - 역사/문화 추천",
            "start_place_id": 3,
            "recommended_place_ids": [3, 4, 5, 8, 9, 10]
        },
        {
            "user_name": "사용자 C - 힐링/자연 추천",
            "start_place_id": 7,
            "recommended_place_ids": [7, 2, 4, 5, 6]
        }
    ]

    for test_case in test_cases:
        run_test_case(test_case, places, graph, all_pairs_distances)


if __name__ == "__main__":
    main()