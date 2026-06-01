import collections
import json
import math
import random

# JSON 데이터 파일 경로 정의
PLACES_JSON_PATH = "data/places.json"
USERS_JSON_PATH = "data/users.json"

# JSON에서 데이터 읽어오기
def load_places() -> list[dict]:
    """places.json 파일을 읽어옵니다."""
    try:
        with open(PLACES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[오류] {PLACES_JSON_PATH} 파일을 찾을 수 없습니다.")
        return []

def load_users() -> list[dict]:
    """users.json 파일을 읽어옵니다."""
    try:
        with open(USERS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[오류] {USERS_JSON_PATH} 파일을 찾을 수 없습니다.")
        return []
    
# get_place_keywords 함수
def get_place_keywords() -> dict[int, list[str]]:
    """장소 ID를 Key로, 키워드 리스트를 Value로 하는 딕셔너리를 반환합니다."""
    places = load_places()
    return {place["id"]: place["keywords"] for place in places}

# [자료구조 1] Trie (트리형 자료구조)
# 사용 목적: 키워드 문자열을 접두사(Prefix) 단위로 효율적으로 저장하고 검색하기 위함
class TrieNode:
    def __init__(self):
        self.children = {}  # HashMap 구조를 활용해 자식 노드 저장
        self.is_end = False  # 하나의 완성된 키워드가 끝나는 지점 표시

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

# [알고리즘 1] TF-IDF (Term Frequency-Inverse Document Frequency)
# 사용 목적: 각 장소에서 특정 키워드가 가지는 상대적 중요도(가중치)를 계산하여 벡터화
# 원래 리뷰에서 계산해야 하지만, 여기서는 장소별 키워드 리스트를 하나의 문서로 취급하여 계산

def calculate_idf(places: list[dict]) -> dict[str, float]:
    #모든 장소 데이터를 기반으로 키워드별 IDF(역문서 빈도)를 계산
    if not places:
        return {}

    N = len(places)
    df = collections.defaultdict(int)

    # 1. 모든 장소에서 키워드 문서 빈도(DF) 집계
    for place in places:
        for kw in set(place["keywords"]):
            df[kw] += 1

    # 2. 키워드별 베이스 IDF 가중치 계산
    base_idf = {}
    for kw, count in df.items():
        base_idf[kw] = math.log(N / (1 + count)) + 1.0 # idf 계산식(분모 0 방지)

    return base_idf


def calculate_tfidf(places, kw_to_idx, total_kws_count):
    N = len(places)

    global_idf = calculate_idf(places)

    # TF-IDF 벡터 생성
    places_vectors = []
    for place in places:
        vector = [0.0] * total_kws_count
        # 해당 장소의 전체 키워드 수
        total_place_kws = len(place["keywords"])

        # 각 키워드별 TF-IDF 계산
        kw_counts = collections.Counter(place["keywords"])
        for kw, count in kw_counts.items():
            if kw in kw_to_idx:
                tf = count / total_place_kws
                idf = global_idf.get(kw, 1.0)
                # 딕셔너리에 단어가 없더라도 에러를 내지 않고, 지정해 둔 기본값(1.0)을 대신 반환
                idx = kw_to_idx[kw]
                vector[idx] = tf * idf

        places_vectors.append(vector)

    return places_vectors

# [알고리즘 2] K-Means Clustering (K-평균 군집화)
# 사용 목적: TF-IDF로 계산된 가중치 벡터를 기반으로 유사한 키워드 성향을 가진 장소들을 K개의 군집으로 '분류'
def euclidean_distance(v1, v2):
    #두 벡터 간의 유클리드 거리 계산
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(v1, v2)))


def kmeans_clustering(vectors, k=3, max_iters=100):
    # 1. 초기 중심점(Centroid)을 랜덤하게 K개 선택
    random.seed(42)  # 일관된 결과를 위해 시드 고정(42는 관용적인 숫자로 의미는 없음)
    centroids = random.sample(vectors, k)

    for _ in range(max_iters):
        # 2. 각 데이터 포인트를 가장 가까운 중심점의 군집에 할당
        clusters = [[] for _ in range(k)]
        for idx, vec in enumerate(vectors):
            distances = [euclidean_distance(vec, c) for c in centroids]
            closest_centroid_idx = distances.index(min(distances))
            clusters[closest_centroid_idx].append(idx)

        # 3. 새로운 중심점 계산 (각 군집에 속한 벡터들의 평균)
        new_centroids = []
        for cluster in clusters:
            if not cluster:  # 빈 군집 예외 처리
                new_centroids.append([0.0] * len(vectors[0]))
                continue
            # 군집 내 벡터들의 합 계산
            vector_sum = [0.0] * len(vectors[0])
            for idx in cluster:
                for i in range(len(vectors[0])):
                    vector_sum[i] += vectors[idx][i]
            # 평균 계산
            mean_vector = [val / len(cluster) for val in vector_sum]
            new_centroids.append(mean_vector)

        # 중심점 변화가 없으면 조기 종료
        if centroids == new_centroids:
            break
        centroids = new_centroids

    return clusters, centroids

# 팀원 연동용 클러스터 매핑 함수
def get_place_cluster_mapping() -> dict[int, int]:
    """
    모든 장소가 각각 몇 번 군집(0, 1, 2)에 속해있는지 
    {장소ID: 군집번호} 형태의 해시맵(dict)을 반환합니다.
    """
    places = load_places()
    if not places:
        return {}
        
    # 1. 모든 유니크 키워드 추출 및 인덱스 매핑
    all_keywords = set()
    for p in places:
        for kw in p["keywords"]:
            all_keywords.add(kw)
    unique_keywords = sorted(list(all_keywords))
    kw_to_idx = {kw: i for i, kw in enumerate(unique_keywords)}
    
    # 2. TF-IDF, K-Means
    vectors = calculate_tfidf(places, kw_to_idx, len(unique_keywords))
    clusters, _ = kmeans_clustering(vectors, k=3)
    
    # 3. 팀원이 쓰기 편하게 {장소ID: 군집번호} 구조로 변환
    place_to_cluster = {}
    for cluster_idx, place_indices in enumerate(clusters):
        for p_idx in place_indices:
            place_id = places[p_idx]["id"]
            place_to_cluster[place_id] = cluster_idx
            
    return place_to_cluster

# [알고리즘 3]Topic-Sensitive Ranking
def get_keyword_weights(target_user_id: int = None) -> dict[str, float]:
    """Topic-Sensitive Ranking 원리를 활용하여 키워드별 최종 가중치를 계산한다. 
    기본적으로 IDF를 베이스 가중치로 잡고, target_user_id가 주어지면 해당 유저의 선호
    키워드 가중치를 증폭(Boosting)한다.
    """
    places = load_places()
    if not places:
        return {}

    # 키워드별 IDF 가중치 계산
    keyword_weights = calculate_idf(places)

    # 유저 개인화 취향 가중치 반영 (Topic-Sensitivity)
    if target_user_id is not None:
        users = load_users()
        target_user = next((u for u in users if u["id"] == target_user_id), None)

        if target_user:
            preferred = target_user["preferred_keywords"]
            boost_factor = 2.5  # 유저 선호 토픽 가중치 배율

            for kw in keyword_weights.keys():
                if kw in preferred:
                    keyword_weights[kw] *= boost_factor

    return keyword_weights

# -------------------------------------------------------
# [메인 관리자 전용 함수] 데이터 정제 및 행렬 변환 자동화
# -------------------------------------------------------
def _prepare_keyword_matrix(places: list[dict]):
    # 메인 로직 실행을 위해 키워드 추출, Trie 생성, HashMap 인덱싱을 일괄 처리
    all_keywords = set()
    trie_store = Trie()
    
    for place in places:
        for kw in place["keywords"]:
            all_keywords.add(kw)
            trie_store.insert(kw)

    unique_keywords_list = sorted(list(all_keywords))
    keyword_to_idx = {kw: i for i, kw in enumerate(unique_keywords_list)}
    
    return trie_store, unique_keywords_list, keyword_to_idx


# -------------------------------------------------------
# [스크립트 실행부] 메인 로직 가동
# -------------------------------------------------------
if __name__ == "__main__":
    # 1. 데이터 로드 및 유효성 검사
    places_data = load_places()
    if not places_data:
        print("[종료] 장소 데이터가 없어 분석을 진행할 수 없습니다.")
        exit()

    # 2. 데이터 전처리 (Trie 사전 구축 및 해시맵 매핑)
    trie_store, unique_keywords_list, keyword_to_idx = _prepare_keyword_matrix(places_data)
    num_keywords = len(unique_keywords_list)

    # 3. 알고리즘 구동 (TF-IDF -> K-Means 군집화)
    places_vectors = calculate_tfidf(places_data, keyword_to_idx, num_keywords)
    clusters, centroids = kmeans_clustering(places_vectors, k=3)

    # 4. 분석 결과 시각화 출력
    print("=" * 60)
    print("키워드 데이터 분석 및 장소 군집화 결과")
    print("=" * 60)
    print(f"시스템 인지 유니크 키워드 총량: {num_keywords}개")
    print("-" * 60)

    for cluster_idx, p_indices in enumerate(clusters):
        print(f"[군집 {cluster_idx + 1}] 성향 카테고리")
        
        # 대표 키워드 상위 3개 추출
        centroid_vec = centroids[cluster_idx]
        top_kw_indices = sorted(enumerate(centroid_vec), key=lambda x: x[1], reverse=True)[:3]
        representative_keywords = [unique_keywords_list[idx] for idx, val in top_kw_indices if val > 0]
        print(f"중심 특징 키워드: {representative_keywords}")

        # 군집 소속 장소 출력
        place_names = [f"{places_data[p_idx]['name']}(ID:{places_data[p_idx]['id']})" for p_idx in p_indices]
        print(f"분류된 장소 목록: {', '.join(place_names)}")
        print("-" * 60)

    # 5. 팀원 1(Collaborative Filtering) 협업용 데이터셋 테스트
    print("\n" + "=" * 60)
    print("[팀원 1 연동 테스트] get_place_cluster_mapping() 호출 결과")
    print("=" * 60)
    cluster_mapping = get_place_cluster_mapping()
    print(f"수신된 {len(cluster_mapping)}개 장소의 클러스터 매핑 정보:")
    print(f"{cluster_mapping}")
    # 팀원 1은 이 해시맵을 CF 가중치 필터링 또는 Cold Start 방어에 활용
    print("=" * 60)

    # 6. 팀원 3 토픽 민감도 점수판 테스트
    print("\n" + "=" * 60)
    print(" [팀원 3 연동 테스트] ID: 2 (이서연) 유저 맞춤형 토픽 부스팅")
    print("=" * 60)
    user_weights = get_keyword_weights(target_user_id=2)
    print(user_weights)
    print("=" * 60)

aadfafd