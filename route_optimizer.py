"""
GraphTrip - 팀원4 여행 코스 최적화 모듈

[실행 환경]
- Python 3.x
- 외부 패키지 설치 필요 없음

[Input 데이터]
- data/places.json
- data/distances.csv
"""

import csv
import heapq
import json


# 자료구조: Dictionary
# Input 데이터: data/places.json
def load_places(file_path):
    places = {}

    with open(file_path, "r", encoding="utf-8") as file:
        place_list = json.load(file)

    for place in place_list:
        place_id = int(place["id"])
        places[place_id] = {
            "name": place["name"],
            "keywords": place.get("keywords", [])
        }

    return places


# 자료구조: Graph
# Input 데이터: data/distances.csv
def load_distance_graph(file_path):
    graph = {}

    with open(file_path, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            from_place = int(row["from_place_id"])
            to_place = int(row["to_place_id"])
            distance = float(row["distance_km"])

            if from_place not in graph:
                graph[from_place] = {}

            if to_place not in graph:
                graph[to_place] = {}

            # 장소 간 이동은 양방향이라고 가정한다.
            graph[from_place][to_place] = distance
            graph[to_place][from_place] = distance

    return graph


def validate_place_ids(graph, place_ids):
    for place_id in place_ids:
        if place_id not in graph:
            raise ValueError(f"장소 ID {place_id}가 거리 그래프에 없습니다.")


def remove_duplicates_keep_order(place_ids):
    result = []
    seen = set()

    for place_id in place_ids:
        if place_id not in seen:
            result.append(place_id)
            seen.add(place_id)

    return result


def build_original_route(start_place_id, recommended_place_ids):
    unique_recommended = remove_duplicates_keep_order(recommended_place_ids)

    if not unique_recommended:
        return [start_place_id]

    if unique_recommended[0] == start_place_id:
        return unique_recommended

    if start_place_id in unique_recommended:
        unique_recommended.remove(start_place_id)

    return [start_place_id] + unique_recommended


# 최단경로탐색: Dijkstra Algorithm
# 자료구조: Priority Queue
def dijkstra(graph, start):
    if start not in graph:
        raise ValueError(f"시작 장소 ID {start}가 거리 그래프에 없습니다.")

    distances = {}

    for place_id in graph:
        distances[place_id] = float("inf")

    distances[start] = 0.0

    priority_queue = []
    heapq.heappush(priority_queue, (0.0, start))

    while priority_queue:
        current_distance, current_place = heapq.heappop(priority_queue)

        if current_distance > distances[current_place]:
            continue

        for next_place, weight in graph[current_place].items():
            new_distance = current_distance + weight

            if new_distance < distances[next_place]:
                distances[next_place] = new_distance
                heapq.heappush(priority_queue, (new_distance, next_place))

    return distances


# 모든 쌍 최단경로탐색: Floyd-Warshall Algorithm
# 자료구조: Dictionary
def floyd_warshall(graph):
    nodes = list(graph.keys())
    distances = {}

    for i in nodes:
        distances[i] = {}

        for j in nodes:
            if i == j:
                distances[i][j] = 0.0
            elif j in graph[i]:
                distances[i][j] = graph[i][j]
            else:
                distances[i][j] = float("inf")

    for k in nodes:
        for i in nodes:
            for j in nodes:
                if distances[i][k] + distances[k][j] < distances[i][j]:
                    distances[i][j] = distances[i][k] + distances[k][j]

    return distances


# 코스 생성: Greedy Algorithm
# 기반 최단거리탐색: Dijkstra Algorithm
# 자료구조: Set
def create_optimized_route_by_dijkstra(graph, start_place_id, recommended_place_ids):
    validate_place_ids(graph, [start_place_id])
    validate_place_ids(graph, recommended_place_ids)

    route = [start_place_id]
    current_place = start_place_id
    total_distance = 0.0

    unvisited = set(remove_duplicates_keep_order(recommended_place_ids))

    if start_place_id in unvisited:
        unvisited.remove(start_place_id)

    while unvisited:
        distances = dijkstra(graph, current_place)
        reachable_places = {}

        for place_id in unvisited:
            if place_id in distances and distances[place_id] != float("inf"):
                reachable_places[place_id] = distances[place_id]

        if not reachable_places:
            raise ValueError("방문 가능한 추천 장소가 없습니다. 거리 데이터를 확인하세요.")

        next_place = min(reachable_places, key=reachable_places.get)
        next_distance = reachable_places[next_place]

        route.append(next_place)
        total_distance += next_distance
        current_place = next_place
        unvisited.remove(next_place)

    return route, total_distance


# 코스 생성: Greedy Algorithm
# 기반 최단거리탐색: Floyd-Warshall Algorithm
# 자료구조: Set
def create_optimized_route_by_floyd(all_pairs_distances, start_place_id, recommended_place_ids):
    if start_place_id not in all_pairs_distances:
        raise ValueError(f"시작 장소 ID {start_place_id}가 거리 테이블에 없습니다.")

    route = [start_place_id]
    current_place = start_place_id
    total_distance = 0.0

    unvisited = set(remove_duplicates_keep_order(recommended_place_ids))

    if start_place_id in unvisited:
        unvisited.remove(start_place_id)

    while unvisited:
        reachable_places = {}

        for place_id in unvisited:
            if (
                current_place in all_pairs_distances
                and place_id in all_pairs_distances[current_place]
                and all_pairs_distances[current_place][place_id] != float("inf")
            ):
                reachable_places[place_id] = all_pairs_distances[current_place][place_id]

        if not reachable_places:
            raise ValueError("방문 가능한 추천 장소가 없습니다. 거리 데이터를 확인하세요.")

        next_place = min(reachable_places, key=reachable_places.get)
        next_distance = reachable_places[next_place]

        route.append(next_place)
        total_distance += next_distance
        current_place = next_place
        unvisited.remove(next_place)

    return route, total_distance


# 경로 거리 계산: Dijkstra Algorithm
def calculate_route_distance_by_dijkstra(graph, route):
    if len(route) <= 1:
        return 0.0

    validate_place_ids(graph, route)

    total_distance = 0.0

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        distances = dijkstra(graph, start)

        if end not in distances or distances[end] == float("inf"):
            raise ValueError(f"{start}에서 {end}까지 이동 가능한 경로가 없습니다.")

        total_distance += distances[end]

    return total_distance


# 경로 거리 계산: Floyd-Warshall Algorithm
def calculate_route_distance_by_floyd(all_pairs_distances, route):
    if len(route) <= 1:
        return 0.0

    total_distance = 0.0

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        if (
            start not in all_pairs_distances
            or end not in all_pairs_distances[start]
            or all_pairs_distances[start][end] == float("inf")
        ):
            raise ValueError(f"{start}에서 {end}까지 이동 가능한 경로가 없습니다.")

        total_distance += all_pairs_distances[start][end]

    return total_distance


def calculate_improvement(original_distance, optimized_distance):
    distance_difference = original_distance - optimized_distance

    if original_distance == 0:
        improvement_rate = 0.0
    else:
        improvement_rate = (distance_difference / original_distance) * 100

    return distance_difference, improvement_rate


def convert_route_to_names(route, places):
    route_names = []

    for place_id in route:
        if place_id in places:
            route_names.append(places[place_id]["name"])
        else:
            route_names.append(f"알 수 없는 장소({place_id})")

    return route_names


# 구간별 이동거리 계산: Dijkstra Algorithm
def get_route_segments_by_dijkstra(graph, route):
    segments = []

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        distances = dijkstra(graph, start)

        if end not in distances or distances[end] == float("inf"):
            raise ValueError(f"{start}에서 {end}까지 이동 가능한 경로가 없습니다.")

        segments.append((start, end, distances[end]))

    return segments


# 구간별 이동거리 계산: Floyd-Warshall Algorithm
def get_route_segments_by_floyd(all_pairs_distances, route):
    segments = []

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        if (
            start not in all_pairs_distances
            or end not in all_pairs_distances[start]
            or all_pairs_distances[start][end] == float("inf")
        ):
            raise ValueError(f"{start}에서 {end}까지 이동 가능한 경로가 없습니다.")

        segments.append((start, end, all_pairs_distances[start][end]))

    return segments


def convert_segments_to_dicts(segments, places):
    segment_dicts = []

    for start, end, distance in segments:
        segment_dicts.append({
            "from_place_id": start,
            "from_place_name": places[start]["name"],
            "to_place_id": end,
            "to_place_name": places[end]["name"],
            "distance_km": round(distance, 2)
        })

    return segment_dicts


# 키워드 분석: Frequency Counting
# 자료구조: Dictionary
def get_top_keywords(route, places, top_n=5):
    keyword_count = {}

    for place_id in route:
        if place_id not in places:
            continue

        for keyword in places[place_id]["keywords"]:
            if keyword not in keyword_count:
                keyword_count[keyword] = 0

            keyword_count[keyword] += 1

    sorted_keywords = sorted(
        keyword_count.items(),
        key=lambda item: (-item[1], item[0])
    )

    return sorted_keywords[:top_n]


def convert_keywords_to_dicts(top_keywords):
    keyword_dicts = []

    for keyword, count in top_keywords:
        keyword_dicts.append({
            "keyword": keyword,
            "count": count
        })

    return keyword_dicts


def infer_course_type(top_keywords):
    keyword_set = set(keyword for keyword, count in top_keywords)

    if "데이트" in keyword_set and "사진맛집" in keyword_set:
        return "감성 데이트 코스"

    if "역사탐방" in keyword_set and "전통적인" in keyword_set:
        return "역사 문화 탐방 코스"

    if "힐링" in keyword_set and "자연친화적인" in keyword_set:
        return "자연 힐링 코스"

    if "야경" in keyword_set:
        return "야경 중심 코스"

    return "개인 맞춤 추천 코스"


def print_segments(segments, places):
    for start, end, distance in segments:
        start_name = places[start]["name"]
        end_name = places[end]["name"]
        print(f"- {start_name} -> {end_name}: {distance:.2f}km")


def print_route_result(
    places,
    start_place_id,
    original_route,
    original_distance,
    dijkstra_route,
    dijkstra_distance,
    floyd_route,
    floyd_distance,
    dijkstra_segments,
    floyd_segments
):
    original_names = convert_route_to_names(original_route, places)
    dijkstra_route_names = convert_route_to_names(dijkstra_route, places)
    floyd_route_names = convert_route_to_names(floyd_route, places)

    dijkstra_difference, dijkstra_rate = calculate_improvement(
        original_distance,
        dijkstra_distance
    )

    floyd_difference, floyd_rate = calculate_improvement(
        original_distance,
        floyd_distance
    )

    top_keywords = get_top_keywords(dijkstra_route, places)
    course_type = infer_course_type(top_keywords)

    print("=" * 70)
    print("[GraphTrip 여행 코스 최적화 결과]")
    print("=" * 70)
    print(f"출발지: {places[start_place_id]['name']}")

    print("\n[기존 추천 순서]")
    print(" -> ".join(original_names))
    print(f"기존 추천 순서 총 이동 거리: {original_distance:.2f}km")

    print("\n[Dijkstra + Greedy 결과]")
    print(" -> ".join(dijkstra_route_names))
    print("\n구간별 이동 거리:")
    print_segments(dijkstra_segments, places)
    print(f"Dijkstra + Greedy 총 이동 거리: {dijkstra_distance:.2f}km")
    print(f"거리 차이: {dijkstra_difference:.2f}km")
    print(f"개선율: {dijkstra_rate:.2f}%")

    print("\n[Floyd-Warshall + Greedy 결과: 비교용 추가 기능]")
    print(" -> ".join(floyd_route_names))
    print("\n구간별 이동 거리:")
    print_segments(floyd_segments, places)
    print(f"Floyd-Warshall + Greedy 총 이동 거리: {floyd_distance:.2f}km")
    print(f"거리 차이: {floyd_difference:.2f}km")
    print(f"개선율: {floyd_rate:.2f}%")

    print("\n[코스 주요 키워드]")
    if top_keywords:
        keyword_text = ", ".join([f"{keyword}({count})" for keyword, count in top_keywords])
        print(keyword_text)
    else:
        print("키워드 없음")

    print("\n[코스 유형]")
    print(course_type)
    print("=" * 70)


def optimize_travel_route(
    start_place_id,
    recommended_place_ids,
    places_file="data/places.json",
    distances_file="data/distances.csv",
    method="dijkstra"
):
    places = load_places(places_file)
    graph = load_distance_graph(distances_file)

    recommended_place_ids = remove_duplicates_keep_order(recommended_place_ids)
    original_route = build_original_route(start_place_id, recommended_place_ids)
    validate_place_ids(graph, original_route)

    original_distance = calculate_route_distance_by_dijkstra(
        graph,
        original_route
    )

    if method == "dijkstra":
        optimized_route, optimized_distance = create_optimized_route_by_dijkstra(
            graph,
            start_place_id,
            recommended_place_ids
        )

        route_segments = get_route_segments_by_dijkstra(
            graph,
            optimized_route
        )

        algorithm_name = "Dijkstra + Greedy"

    elif method == "floyd":
        all_pairs_distances = floyd_warshall(graph)

        optimized_route, optimized_distance = create_optimized_route_by_floyd(
            all_pairs_distances,
            start_place_id,
            recommended_place_ids
        )

        route_segments = get_route_segments_by_floyd(
            all_pairs_distances,
            optimized_route
        )

        algorithm_name = "Floyd-Warshall + Greedy"

    else:
        raise ValueError("method는 'dijkstra' 또는 'floyd'만 사용할 수 있습니다.")

    distance_difference, improvement_rate = calculate_improvement(
        original_distance,
        optimized_distance
    )

    top_keywords = get_top_keywords(optimized_route, places)
    course_type = infer_course_type(top_keywords)

    result = {
        "algorithm": algorithm_name,
        "start_place_id": start_place_id,
        "start_place_name": places[start_place_id]["name"],
        "input_recommended_place_ids": recommended_place_ids,
        "input_recommended_place_names": convert_route_to_names(
            recommended_place_ids,
            places
        ),
        "original_route_ids": original_route,
        "original_route_names": convert_route_to_names(
            original_route,
            places
        ),
        "original_distance_km": round(original_distance, 2),
        "optimized_route_ids": optimized_route,
        "optimized_route_names": convert_route_to_names(
            optimized_route,
            places
        ),
        "optimized_distance_km": round(optimized_distance, 2),
        "distance_difference_km": round(distance_difference, 2),
        "improvement_rate_percent": round(improvement_rate, 2),
        "segments": convert_segments_to_dicts(route_segments, places),
        "top_keywords": convert_keywords_to_dicts(top_keywords),
        "course_type": course_type
    }

    return result


def print_optimized_result_dict(result):
    print("=" * 70)
    print("[GraphTrip 통합용 여행 코스 최적화 결과]")
    print("=" * 70)

    print(f"사용 알고리즘: {result['algorithm']}")
    print(f"출발지: {result['start_place_name']}")

    print("\n[입력 추천 장소]")
    print(" -> ".join(result["input_recommended_place_names"]))

    print("\n[기존 추천 순서]")
    print(" -> ".join(result["original_route_names"]))
    print(f"기존 추천 순서 총 이동 거리: {result['original_distance_km']:.2f}km")

    print("\n[최적화된 여행 코스]")
    print(" -> ".join(result["optimized_route_names"]))
    print(f"최적화 후 총 이동 거리: {result['optimized_distance_km']:.2f}km")

    print("\n[구간별 이동 거리]")
    for segment in result["segments"]:
        print(
            f"- {segment['from_place_name']} -> "
            f"{segment['to_place_name']}: "
            f"{segment['distance_km']:.2f}km"
        )

    print("\n[거리 비교 결과]")
    print(f"거리 차이: {result['distance_difference_km']:.2f}km")
    print(f"개선율: {result['improvement_rate_percent']:.2f}%")

    print("\n[코스 주요 키워드]")
    if result["top_keywords"]:
        keyword_text = ", ".join(
            [
                f"{item['keyword']}({item['count']})"
                for item in result["top_keywords"]
            ]
        )
        print(keyword_text)
    else:
        print("키워드 없음")

    print("\n[코스 유형]")
    print(result["course_type"])
    print("=" * 70)