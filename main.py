"""
GraphTrip - Team 4 travel route optimization runner.

Run this file from the project root:

python main.py

or

py main.py
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from route_optimizer import (
    build_original_route,
    calculate_route_distance_by_dijkstra,
    create_optimized_route_by_dijkstra,
    create_optimized_route_by_floyd,
    floyd_warshall,
    get_route_segments_by_dijkstra,
    get_route_segments_by_floyd,
    load_distance_graph,
    load_places,
    optimize_travel_route,
    print_optimized_result_dict,
    print_route_result
)


def run_test_case(test_case, places, graph, all_pairs_distances):
    """
    Run route optimization for one dummy recommendation result.
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

    # Algorithm: Dijkstra Algorithm + Greedy Algorithm
    dijkstra_route, dijkstra_distance = create_optimized_route_by_dijkstra(
        graph,
        start_place_id,
        recommended_place_ids
    )

    # Algorithm: Floyd-Warshall Algorithm + Greedy Algorithm
    # This is used as an additional comparison method.
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
    Test the final function that other team members can call.

    Other modules only need to pass:
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
    Run the Team 4 module independently before team integration.
    """

    places_file = "data/places.json"
    distances_file = "data/distances.csv"

    places = load_places(places_file)
    graph = load_distance_graph(distances_file)

    # Algorithm: Floyd-Warshall Algorithm
    # Precompute all-pairs shortest distances for comparison.
    all_pairs_distances = floyd_warshall(graph)

    # Dummy test cases that represent recommendation results from Team 1, 2, 3.
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