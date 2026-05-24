import csv
import heapq
import json


def load_places(file_path):
    """
    장소 정보를 JSON에서 읽어오는 함수

    자료구조: Dictionary
    - place_id를 key로 사용한다.
    - 장소명과 키워드를 빠르게 조회하기 위해 사용한다.
    """

    places = {}

    with open(file_path, "r", encoding="utf-8") as file:
        place_list = json.load(file)

    for place in place_list:
        place_id = int(place["id"])

        places[place_id] = {
            "name": place["name"],
            "keywords": place["keywords"]
        }

    return places


def load_distance_graph(file_path):
    """
    장소 간 거리 데이터를 CSV에서 읽어 그래프로 변환하는 함수

    자료구조: Graph
    - 장소를 정점(Vertex)으로 표현한다.
    - 장소 간 이동 거리를 간선(Edge)의 가중치로 표현한다.
    """

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

            # 경로는 양방향 이동이 가능하다고 가정한다.
            graph[from_place][to_place] = distance
            graph[to_place][from_place] = distance

    return graph


def validate_place_ids(graph, place_ids):
    """
    입력된 장소 ID들이 거리 그래프에 존재하는지 확인한다.
    """

    for place_id in place_ids:
        if place_id not in graph:
            raise ValueError(f"장소 ID {place_id}가 거리 그래프에 없습니다.")


def dijkstra(graph, start):
    """
    알고리즘: Dijkstra Algorithm
    자료구조: Priority Queue

    하나의 출발 장소에서 다른 모든 장소까지의 최단 거리를 계산한다.
    Priority Queue를 사용하여 현재까지 거리가 가장 짧은 장소를 우선 탐색한다.
    """

    if start not in graph:
        raise ValueError(f"시작 장소 ID {start}가 거리 그래프에 없습니다.")

    distances = {}

    for place_id in graph:
        distances[place_id] = float("inf")

    distances[start] = 0.0

    # 자료구조: Priority Queue
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


def floyd_warshall(graph):
    """
    알고리즘: Floyd-Warshall Algorithm

    모든 장소 쌍 사이의 최단 거리를 계산한다.
    경주처럼 장소 수가 제한된 프로토타입에서는 전체 최단거리 테이블을 미리 계산하여
    코스 생성 시 장소 간 이동 거리를 빠르게 조회할 수 있다.
    """

    nodes = list(graph.keys())

    # 자료구조: Dictionary
    # distances[i][j] = i번 장소에서 j번 장소까지의 최단 거리
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


def create_optimized_route_by_dijkstra(graph, start_place_id, recommended_place_ids):
    """
    알고리즘: Greedy Algorithm
    기반 최단거리 계산: Dijkstra Algorithm

    현재 위치에서 아직 방문하지 않은 추천 장소들까지의 최단 거리를
    Dijkstra 알고리즘으로 계산한 뒤, 가장 가까운 장소를 다음 방문지로 선택한다.
    """

    validate_place_ids(graph, [start_place_id])
    validate_place_ids(graph, recommended_place_ids)

    route = [start_place_id]
    current_place = start_place_id
    total_distance = 0.0

    # 자료구조: Set
    # 아직 방문하지 않은 추천 장소를 관리한다.
    unvisited = set(recommended_place_ids)

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


def create_optimized_route_by_floyd(all_pairs_distances, start_place_id, recommended_place_ids):
    """
    알고리즘: Greedy Algorithm
    기반 최단거리 계산: Floyd-Warshall Algorithm

    Floyd-Warshall 알고리즘으로 미리 계산된 모든 장소 쌍 최단거리 테이블을 사용하여,
    현재 위치에서 가장 가까운 미방문 추천 장소를 다음 방문지로 선택한다.
    """

    route = [start_place_id]
    current_place = start_place_id
    total_distance = 0.0

    # 자료구조: Set
    # 아직 방문하지 않은 추천 장소를 관리한다.
    unvisited = set(recommended_place_ids)

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


def calculate_route_distance_by_dijkstra(graph, route):
    """
    입력된 방문 순서대로 이동했을 때의 총 이동 거리를 계산한다.

    각 구간의 이동 거리는 Dijkstra 알고리즘으로 계산한다.
    직접 연결된 거리만 보는 것이 아니라 그래프 상의 최단 경로 거리를 사용한다.
    """

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


def calculate_route_distance_by_floyd(all_pairs_distances, route):
    """
    Floyd-Warshall 결과를 이용하여 입력된 방문 순서의 총 이동 거리를 계산한다.
    """

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
    """
    기존 추천 순서와 최적화된 코스의 이동 거리 차이를 계산한다.
    """

    saved_distance = original_distance - optimized_distance

    if original_distance == 0:
        improvement_rate = 0.0
    else:
        improvement_rate = (saved_distance / original_distance) * 100

    return saved_distance, improvement_rate


def convert_route_to_names(route, places):
    """
    장소 ID로 구성된 경로를 장소 이름 목록으로 변환한다.
    """

    route_names = []

    for place_id in route:
        if place_id in places:
            route_names.append(places[place_id]["name"])
        else:
            route_names.append(f"알 수 없는 장소({place_id})")

    return route_names


def get_route_segments_by_dijkstra(graph, route):
    """
    Dijkstra 알고리즘을 사용해 경로의 구간별 이동 거리를 구한다.
    """

    segments = []

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        distances = dijkstra(graph, start)
        distance = distances[end]

        segments.append((start, end, distance))

    return segments


def get_route_segments_by_floyd(all_pairs_distances, route):
    """
    Floyd-Warshall 결과를 사용해 경로의 구간별 이동 거리를 구한다.
    """

    segments = []

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]
        distance = all_pairs_distances[start][end]

        segments.append((start, end, distance))

    return segments


def get_top_keywords(route, places, top_n=5):
    """
    최적화된 코스에 포함된 장소들의 키워드를 집계한다.

    알고리즘: Frequency Counting
    자료구조: Dictionary
    - 키워드를 key로 하고 등장 횟수를 value로 저장한다.
    """

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
        key=lambda item: item[1],
        reverse=True
    )

    return sorted_keywords[:top_n]


def infer_course_type(top_keywords):
    """
    주요 키워드를 바탕으로 코스 유형을 간단히 추론한다.
    """

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
    """
    구간별 이동 거리를 출력한다.
    """

    for start, end, distance in segments:
        start_name = places[start]["name"]
        end_name = places[end]["name"]
        print(f"- {start_name} → {end_name}: {distance:.2f}km")


def print_route_result(
    places,
    start_place_id,
    recommended_place_ids,
    original_distance,
    dijkstra_route,
    dijkstra_distance,
    floyd_route,
    floyd_distance,
    dijkstra_segments,
    floyd_segments
):
    """
    코스 최적화 결과를 출력하는 함수
    """

    recommended_names = convert_route_to_names(recommended_place_ids, places)
    dijkstra_route_names = convert_route_to_names(dijkstra_route, places)
    floyd_route_names = convert_route_to_names(floyd_route, places)

    dijkstra_saved, dijkstra_rate = calculate_improvement(
        original_distance,
        dijkstra_distance
    )

    floyd_saved, floyd_rate = calculate_improvement(
        original_distance,
        floyd_distance
    )

    top_keywords = get_top_keywords(floyd_route, places)
    course_type = infer_course_type(top_keywords)

    print("=" * 70)
    print("[GraphTrip 여행 코스 최적화 결과]")
    print("=" * 70)

    print(f"출발지: {places[start_place_id]['name']}")

    print("\n[기존 추천 순서]")
    print(" → ".join(recommended_names))
    print(f"기존 추천 순서 총 이동 거리: {original_distance:.2f}km")

    print("\n[Dijkstra + Greedy 결과]")
    print(" → ".join(dijkstra_route_names))
    print("\n구간별 이동 거리:")
    print_segments(dijkstra_segments, places)
    print(f"Dijkstra + Greedy 총 이동 거리: {dijkstra_distance:.2f}km")
    print(f"절약 거리: {dijkstra_saved:.2f}km")
    print(f"개선율: {dijkstra_rate:.2f}%")

    print("\n[Floyd-Warshall + Greedy 결과]")
    print(" → ".join(floyd_route_names))
    print("\n구간별 이동 거리:")
    print_segments(floyd_segments, places)
    print(f"Floyd-Warshall + Greedy 총 이동 거리: {floyd_distance:.2f}km")
    print(f"절약 거리: {floyd_saved:.2f}km")
    print(f"개선율: {floyd_rate:.2f}%")

    print("\n[코스 주요 키워드]")
    if top_keywords:
        keyword_text = ", ".join([f"{keyword}({count})" for keyword, count in top_keywords])
        print(keyword_text)
    else:
        print("키워드 없음")

    print(f"\n[코스 유형]")
    print(course_type)

    print("=" * 70)