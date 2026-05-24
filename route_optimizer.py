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

            # 양방향 이동이 가능하다고 가정한다.
            graph[from_place][to_place] = distance
            graph[to_place][from_place] = distance

    return graph


def dijkstra(graph, start):
    """
    알고리즘: Dijkstra Algorithm
    자료구조: Priority Queue

    현재 위치(start)에서 다른 모든 장소까지의 최단 거리를 계산한다.
    Priority Queue를 사용하여 현재까지의 거리가 가장 짧은 장소를 먼저 탐색한다.
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


def create_optimized_route(graph, start_place_id, recommended_place_ids):
    """
    알고리즘: Greedy Algorithm

    추천된 장소 목록 중에서 현재 위치와 가장 가까운 장소를 다음 방문지로 선택한다.
    각 단계에서 Dijkstra 알고리즘을 사용하여 현재 위치 기준 최단 거리를 계산한다.
    """

    validate_place_ids(graph, [start_place_id])
    validate_place_ids(graph, recommended_place_ids)

    route = [start_place_id]
    current_place = start_place_id
    total_distance = 0.0

    unvisited = set(recommended_place_ids)

    # 출발지가 추천 목록에 포함되어 있으면 이미 방문한 것으로 처리한다.
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

        # 현재 위치에서 최단 거리가 가장 짧은 미방문 장소 선택
        next_place = min(reachable_places, key=reachable_places.get)
        next_distance = reachable_places[next_place]

        route.append(next_place)
        total_distance += next_distance

        current_place = next_place
        unvisited.remove(next_place)

    return route, total_distance


def calculate_route_distance(graph, route):
    """
    입력된 방문 순서대로 이동했을 때의 총 이동 거리를 계산한다.

    각 구간의 이동 거리는 Dijkstra 알고리즘으로 계산한다.
    따라서 직접 연결된 간선만 보는 것이 아니라,
    그래프 상에서 이동 가능한 최단 경로 거리를 사용한다.
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


def validate_place_ids(graph, place_ids):
    """
    입력된 장소 ID들이 거리 그래프에 존재하는지 확인한다.
    """

    for place_id in place_ids:
        if place_id not in graph:
            raise ValueError(f"장소 ID {place_id}가 거리 그래프에 없습니다.")


def print_route_result(
    places,
    start_place_id,
    recommended_place_ids,
    route,
    original_distance,
    optimized_distance
):
    """
    코스 최적화 결과를 출력하는 함수
    """

    recommended_names = convert_route_to_names(recommended_place_ids, places)
    route_names = convert_route_to_names(route, places)

    saved_distance, improvement_rate = calculate_improvement(
        original_distance,
        optimized_distance
    )

    print("=" * 60)
    print("[GraphTrip 여행 코스 최적화 결과]")
    print("=" * 60)

    print(f"출발지: {places[start_place_id]['name']}")

    print("\n기존 추천 순서:")
    print(" → ".join(recommended_names))
    print(f"기존 순서 총 이동 거리: {original_distance:.2f}km")

    print("\n최적화된 여행 코스:")
    print(" → ".join(route_names))
    print(f"최적화 후 총 이동 거리: {optimized_distance:.2f}km")

    print("\n거리 비교:")
    print(f"절약 거리: {saved_distance:.2f}km")
    print(f"개선율: {improvement_rate:.2f}%")

    print("=" * 60)