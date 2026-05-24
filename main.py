from route_optimizer import (
    load_places,
    load_distance_graph,
    create_optimized_route,
    calculate_route_distance,
    print_route_result
)


def main():
    """
    GraphTrip 팀원4 여행 코스 최적화 실행 파일

    담당 기능:
    - 추천된 경주 여행 장소들을 입력받는다.
    - 장소 간 거리 데이터를 그래프로 구성한다.
    - Dijkstra Algorithm과 Greedy Algorithm을 사용하여 효율적인 여행 코스를 생성한다.
    - 기존 추천 순서와 최적화된 코스의 총 이동 거리를 비교한다.
    """

    # Input 데이터
    # 경주 주요 여행지 데이터와 장소 간 거리 데이터 사용
    places_file = "data/places.json"
    distances_file = "data/distances.csv"

    places = load_places(places_file)
    graph = load_distance_graph(distances_file)

    # 팀원1, 2, 3의 추천 결과가 아직 완성되지 않았으므로
    # 현재는 더미 추천 장소 ID 리스트를 사용한다.
    #
    # 나중에 팀원들의 추천 결과가 연결되면
    # recommended_place_ids 값만 추천 시스템 결과로 교체하면 된다.
    start_place_id = 1

    recommended_place_ids = [1, 2, 3, 8, 10]

    # 기존 추천 순서의 총 이동 거리 계산
    original_distance = calculate_route_distance(
        graph,
        recommended_place_ids
    )

    # 최적화된 여행 코스 생성
    optimized_route, optimized_distance = create_optimized_route(
        graph,
        start_place_id,
        recommended_place_ids
    )

    # 결과 출력
    print_route_result(
        places,
        start_place_id,
        recommended_place_ids,
        optimized_route,
        original_distance,
        optimized_distance
    )


if __name__ == "__main__":
    main()