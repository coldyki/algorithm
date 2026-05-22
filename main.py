from route_optimizer import (
    load_places,
    load_distance_graph,
    create_optimized_route,
    print_route_result
)


def main():
    # Input 데이터
    # 경주 주요 여행지 데이터와 장소 간 거리 데이터 사용
    places_file = "data/places.csv"
    distances_file = "data/distances.csv"

    places = load_places(places_file)
    graph = load_distance_graph(distances_file)

    # 팀원1, 2, 3의 추천 결과가 아직 완성되지 않았으므로
    # 더미 추천 장소 ID 리스트를 사용한다.
    start_place_id = 1

    recommended_place_ids = [1, 2, 3, 8, 10]

    route, total_distance = create_optimized_route(
        graph,
        start_place_id,
        recommended_place_ids
    )

    print_route_result(
        places,
        start_place_id,
        recommended_place_ids,
        route,
        total_distance
    )


if __name__ == "__main__":
    main()