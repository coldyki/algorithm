"""
GraphTrip - 팀원4 여행 코스 최적화 실행 파일

[실행 방법]
프로젝트 루트 폴더에서 아래 명령어 실행

python main.py

또는

py main.py
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from route_optimizer import (
    build_coordinate_graph,
    build_original_route,
    calculate_route_distance_by_dijkstra,
    create_optimized_route_by_dijkstra,
    create_optimized_route_by_floyd,
    floyd_warshall,
    get_route_segments_by_dijkstra,
    get_route_segments_by_floyd,
    load_places,
    optimize_travel_route,
    print_optimized_result_dict,
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

    original_route = build_original_route(
        start_place_id,
        recommended_place_ids
    )

    original_distance = calculate_route_distance_by_dijkstra(
        graph,
        original_route
    )

    # 알고리즘: Dijkstra Algorithm + Greedy Algorithm
    dijkstra_route, dijkstra_distance = create_optimized_route_by_dijkstra(
        graph,
        start_place_id,
        recommended_place_ids
    )

    # 알고리즘: Floyd-Warshall Algorithm + Greedy Algorithm
    # 비교용 추가 기능이다.
    floyd_route, floyd_distance = create_optimized_route_by_floyd(
        all_pairs_distances,
        start_place_id,
        recommended_place_ids
    )

    dijkstra_segments = get_route_segments_by_dijkstra(
        graph,
        dijkstra_route
    )

    floyd_segments = get_route_segments_by_floyd(
        all_pairs_distances,
        floyd_route
    )

    print_route_result(
        places=places,
        start_place_id=start_place_id,
        original_route=original_route,
        original_distance=original_distance,
        dijkstra_route=dijkstra_route,
        dijkstra_distance=dijkstra_distance,
        floyd_route=floyd_route,
        floyd_distance=floyd_distance,
        dijkstra_segments=dijkstra_segments,
        floyd_segments=floyd_segments
    )


def run_integration_function_demo():
    """
    팀원들과 통합할 때 사용할 optimize_travel_route() 함수 테스트

    팀원1, 2, 3이 나중에 아래 두 값만 넘겨주면 된다.
    - start_place_id
    - recommended_place_ids
    """

    print("\n\n")
    print("#" * 70)
    print("[팀원 통합용 함수 테스트]")
    print("#" * 70)

    start_place_id = 1
    recommended_place_ids = [1, 2, 3, 8, 10]

    result = optimize_travel_route(
        start_place_id=start_place_id,
        recommended_place_ids=recommended_place_ids,
        method="dijkstra"
    )

    print_optimized_result_dict(result)


def main():
    """
    팀원4 개인 모듈 실행 함수

    현재 버전은 data/places.json의 lat/lng 좌표를 이용하여
    장소 간 직선거리를 계산하고, 이를 기반으로 여행 코스를 최적화한다.
    """

    places_file = "data/places.json"

    places = load_places(places_file)
    graph = build_coordinate_graph(places)

    # 알고리즘: Floyd-Warshall Algorithm
    # 모든 장소 쌍 최단거리 테이블을 한 번 미리 계산한다.
    all_pairs_distances = floyd_warshall(graph)

    # 팀원1, 2, 3의 추천 결과를 가정한 더미 테스트 케이스
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
        },
        {
            "user_name": "사용자 D - 출발지가 추천 목록에 없는 경우",
            "start_place_id": 1,
            "recommended_place_ids": [2, 3, 8, 10]
        },
        {
            "user_name": "사용자 E - 추천 장소가 2개인 경우",
            "start_place_id": 1,
            "recommended_place_ids": [1, 10]
        }
    ]

    for test_case in test_cases:
        run_test_case(test_case, places, graph, all_pairs_distances)

    run_integration_function_demo()


if __name__ == "__main__":
    main()