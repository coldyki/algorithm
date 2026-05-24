"""
GraphTrip - 팀원4 여행 코스 최적화 실행 파일

[실행 환경]
- 개발 환경: Visual Studio Code
- 실행 언어: Python 3.x
- 실행 방법: 터미널에서 python main.py 또는 py main.py 실행

[실행 시 필요한 라이브러리]
- 본 모듈은 Python 표준 라이브러리만 사용한다.
- 별도의 외부 패키지 설치는 필요하지 않다.

[Input 데이터]
1. data/places.json
   - 내용: 경주 주요 여행지 ID, 장소명, 키워드
   - 출처: 팀에서 경주 주요 여행지를 기준으로 직접 구성한 프로토타입용 장소/키워드 데이터

2. data/distances.csv
   - 내용: 경주 주요 여행지 간 이동 거리
   - 출처: 팀원4가 경주 주요 여행지 간 이동 관계를 기준으로 직접 구성한 프로토타입용 거리 데이터

[담당 기능]
- 장소 거리 데이터 정리
- 최단경로 알고리즘 구현
- 추천 장소 기반 여행 코스 생성
- 기존 추천 순서와 최적화된 코스 비교
- 팀원들과 통합 가능한 optimize_travel_route() 함수 테스트
"""

from route_optimizer import (
    load_places,
    load_distance_graph,
    floyd_warshall,
    create_optimized_route_by_dijkstra,
    create_optimized_route_by_floyd,
    calculate_route_distance_by_dijkstra,
    get_route_segments_by_dijkstra,
    get_route_segments_by_floyd,
    print_route_result,
    optimize_travel_route,
    print_optimized_result_dict,
    build_original_route
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

    # 기존 추천 순서 생성
    original_route = build_original_route(
        start_place_id,
        recommended_place_ids
    )

    # 기존 추천 순서의 총 이동 거리 계산
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
    floyd_route, floyd_distance = create_optimized_route_by_floyd(
        all_pairs_distances,
        start_place_id,
        recommended_place_ids
    )

    # 구간별 이동 거리 계산
    dijkstra_segments = get_route_segments_by_dijkstra(
        graph,
        dijkstra_route
    )

    floyd_segments = get_route_segments_by_floyd(
        all_pairs_distances,
        floyd_route
    )

    # 테스트용 출력
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
        method="floyd"
    )

    print_optimized_result_dict(result)


def main():
    """
    팀원4 개인 모듈 실행 함수

    현재 목표:
    - 팀원들과 기능을 합치기 전, 팀원4 개인 모듈을 독립 실행 가능하게 완성한다.
    - 팀원1, 2, 3의 추천 결과가 아직 연결되지 않았으므로 더미 추천 장소 ID를 사용한다.
    - 추후 팀원 추천 결과가 연결되면 recommended_place_ids만 교체하면 된다.
    """

    places_file = "data/places.json"
    distances_file = "data/distances.csv"

    places = load_places(places_file)
    graph = load_distance_graph(distances_file)

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

    # 팀원들과 합칠 때 사용할 최종 함수 테스트
    run_integration_function_demo()


if __name__ == "__main__":
    main()