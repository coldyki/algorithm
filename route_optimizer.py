"""
GraphTrip - 팀원4 여행 코스 최적화 모듈

[실행 환경]
- 개발 환경: Visual Studio Code
- 실행 언어: Python 3.x
- 실행 방법: 터미널에서 python main.py 또는 py main.py 실행

[실행 시 필요한 라이브러리]
- csv: Python 표준 라이브러리
- heapq: Python 표준 라이브러리
- json: Python 표준 라이브러리
- 별도의 외부 패키지 설치는 필요하지 않음

[Input 데이터]
1. data/places.json
   - 내용: 경주 주요 여행지 ID, 장소명, 키워드
   - 출처: 팀에서 경주 주요 여행지를 기준으로 직접 구성한 프로토타입용 장소/키워드 데이터

2. data/distances.csv
   - 내용: 경주 주요 여행지 간 이동 거리
   - 출처: 팀원4가 경주 주요 여행지 간 이동 관계를 기준으로 직접 구성한 프로토타입용 거리 데이터

[사용 자료구조]
- Graph: 장소를 정점, 장소 간 이동 거리를 간선 가중치로 표현
- Priority Queue: Dijkstra 알고리즘에서 최단 거리 후보 관리
- Dictionary: 장소 ID, 장소명, 키워드, 최단거리 테이블 조회
- Set: 아직 방문하지 않은 추천 장소 관리
- List: 추천 장소 목록과 최종 코스 저장

[사용 알고리즘]
- Dijkstra Algorithm
- Floyd-Warshall Algorithm
- Greedy Algorithm
- Frequency Counting
"""

import csv
import heapq
import json


# 자료구조: Dictionary
# Input 데이터: data/places.json
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


# 자료구조: Graph
# Input 데이터: data/distances.csv
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

            # 경주 여행지 간 이동은 양방향 이동이 가능하다고 가정한다.
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


def remove_duplicates_keep_order(place_ids):
    """
    추천 장소 ID 목록에서 중복을 제거하되, 기존 순서는 유지한다.

    자료구조: Set
    - 이미 등장한 장소 ID를 빠르게 확인하기 위해 사용한다.
    """

    result = []
    seen = set()

    for place_id in place_ids:
        if place_id not in seen:
            result.append(place_id)
            seen.add(place_id)

    return result


def build_original_route(start_place_id, recommended_place_ids):
    """
    기존 추천 순서 기준 경로를 만든다.

    출발지가 추천 장소 목록에 이미 있으면 그대로 사용하고,
    출발지가 추천 장소 목록에 없으면 맨 앞에 출발지를 추가한다.
    """

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


# 모든 쌍 최단경로탐색: Floyd-Warshall Algorithm
# 자료구조: Dictionary
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


# 코스 생성: Greedy Algorithm
# 기반 최단거리탐색: Dijkstra Algorithm
# 자료구조: Set
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

        # Greedy Algorithm:
        # 현재 위치에서 가장 가까운 미방문 장소를 다음 방문지로 선택한다.
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

        # Greedy Algorithm:
        # 현재 위치에서 가장 가까운 미방문 장소를 다음 방문지로 선택한다.
        next_place = min(reachable_places, key=reachable_places.get)
        next_distance = reachable_places[next_place]

        route.append(next_place)
        total_distance += next_distance

        current_place = next_place
        unvisited.remove(next_place)

    return route, total_distance


# 경로 거리 계산: Dijkstra Algorithm
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


# 경로 거리 계산: Floyd-Warshall Algorithm
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

    자료구조: Dictionary
    - place_id를 이용해 장소명을 조회한다.
    """

    route_names = []

    for place_id in route:
        if place_id in places:
            route_names.append(places[place_id]["name"])
        else:
            route_names.append(f"알 수 없는 장소({place_id})")

    return route_names


# 구간별 이동거리 계산: Dijkstra Algorithm
def get_route_segments_by_dijkstra(graph, route):
    """
    Dijkstra 알고리즘을 사용해 경로의 구간별 이동 거리를 구한다.
    """

    segments = []

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        distances = dijkstra(graph, start)

        if end not in distances or distances[end] == float("inf"):
            raise ValueError(f"{start}에서 {end}까지 이동 가능한 경로가 없습니다.")

        distance = distances[end]
        segments.append((start, end, distance))

    return segments


# 구간별 이동거리 계산: Floyd-Warshall Algorithm
def get_route_segments_by_floyd(all_pairs_distances, route):
    """
    Floyd-Warshall 결과를 사용해 경로의 구간별 이동 거리를 구한다.
    """

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

        distance = all_pairs_distances[start][end]
        segments.append((start, end, distance))

    return segments


def convert_segments_to_dicts(segments, places):
    """
    구간별 이동 거리 튜플을 팀원들이 활용하기 쉬운 Dictionary 리스트로 변환한다.
    """

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


def convert_keywords_to_dicts(top_keywords):
    """
    키워드 빈도 튜플을 Dictionary 리스트로 변환한다.
    """

    keyword_dicts = []

    for keyword, count in top_keywords:
        keyword_dicts.append({
            "keyword": keyword,
            "count": count
        })

    return keyword_dicts


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
    original_route,
    original_distance,
    dijkstra_route,
    dijkstra_distance,
    floyd_route,
    floyd_distance,
    dijkstra_segments,
    floyd_segments
):
    """
    콘솔 테스트용 코스 최적화 결과 출력 함수
    """

    original_names = convert_route_to_names(original_route, places)
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
    print(" → ".join(original_names))
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


def optimize_travel_route(
    start_place_id,
    recommended_place_ids,
    places_file="data/places.json",
    distances_file="data/distances.csv",
    method="floyd"
):
    """
    팀원들과 통합할 때 사용할 최종 연결용 함수

    입력:
    - start_place_id: 출발 장소 ID
    - recommended_place_ids: 팀원1, 2, 3의 추천 결과로 나온 장소 ID 리스트
    - places_file: 장소 정보 JSON 파일 경로
    - distances_file: 장소 간 거리 CSV 파일 경로
    - method: "floyd" 또는 "dijkstra"

    출력:
    - 코스 최적화 결과를 Dictionary 형태로 반환한다.
    - 나중에 UI, 발표 출력, 다른 팀원 코드에서 쉽게 사용할 수 있다.
    """

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

    saved_distance, improvement_rate = calculate_improvement(
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
        "saved_distance_km": round(saved_distance, 2),
        "improvement_rate_percent": round(improvement_rate, 2),
        "segments": convert_segments_to_dicts(route_segments, places),
        "top_keywords": convert_keywords_to_dicts(top_keywords),
        "course_type": course_type
    }

    return result


def print_optimized_result_dict(result):
    """
    optimize_travel_route()의 반환 결과를 콘솔에 보기 좋게 출력하는 함수
    """

    print("=" * 70)
    print("[GraphTrip 통합용 최적 여행 코스 결과]")
    print("=" * 70)

    print(f"사용 알고리즘: {result['algorithm']}")
    print(f"출발지: {result['start_place_name']}")

    print("\n[입력 추천 장소]")
    print(" → ".join(result["input_recommended_place_names"]))

    print("\n[기존 추천 순서]")
    print(" → ".join(result["original_route_names"]))
    print(f"기존 추천 순서 총 이동 거리: {result['original_distance_km']:.2f}km")

    print("\n[최적화된 여행 코스]")
    print(" → ".join(result["optimized_route_names"]))
    print(f"최적화 후 총 이동 거리: {result['optimized_distance_km']:.2f}km")

    print("\n[구간별 이동 거리]")
    for segment in result["segments"]:
        print(
            f"- {segment['from_place_name']} → "
            f"{segment['to_place_name']}: "
            f"{segment['distance_km']:.2f}km"
        )

    print("\n[거리 개선 결과]")
    print(f"절약 거리: {result['saved_distance_km']:.2f}km")
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

    print(f"\n[코스 유형]")
    print(result["course_type"])

    print("=" * 70)