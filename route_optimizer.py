import csv
import heapq


def load_places(file_path):
    """
    장소 정보를 CSV에서 읽어오는 함수

    자료구조: Dictionary
    - place_id를 key로 사용하여 장소명과 키워드를 빠르게 조회한다.
    """

    places = {}

    with open(file_path, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            place_id = int(row["place_id"])
            place_name = row["place_name"]
            keywords = row["keywords"].split("|")

            places[place_id] = {
                "name": place_name,
                "keywords": keywords
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

    distances = {}

    for place_id in graph:
        distances[place_id] = float("inf")

    distances[start] = 0

    # 자료구조: Priority Queue
    priority_queue = []
    heapq.heappush(priority_queue, (0, start))

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

    if start_place_id not in graph:
        raise ValueError(f"출발지 ID {start_place_id}가 거리 그래프에 없습니다.")

    route = [start_place_id]
    current_place = start_place_id
    total_distance = 0.0

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


def print_route_result(places, start_place_id, recommended_place_ids, route, total_distance):
    """
    코스 최적화 결과를 출력하는 함수
    """

    recommended_names = convert_route_to_names(recommended_place_ids, places)
    route_names = convert_route_to_names(route, places)

    print("=" * 60)
    print("[GraphTrip 여행 코스 최적화 결과]")
    print("=" * 60)

    print(f"출발지: {places[start_place_id]['name']}")

    print("\n추천 장소 목록:")
    print(" → ".join(recommended_names))

    print("\n최적화된 여행 코스:")
    print(" → ".join(route_names))

    print(f"\n총 이동 거리: {total_distance:.2f}km")

    print("=" * 60)