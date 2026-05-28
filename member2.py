import collections
import math
import random

# 경주 여행지 10개 더미 데이터
places_data = [
    {"id": 1, "name": "황리단길", "keywords": ["감성적인", "사진맛집", "카페투어", "데이트", "먹방", "로맨틱한"]},
    {"id": 2, "name": "동궁과 월지", "keywords": ["야경", "로맨틱한", "산책", "힐링", "사진맛집", "데이트"]},
    {"id": 3, "name": "첨성대", "keywords": ["전통적인", "역사탐방", "사진맛집", "산책", "고즈넉한"]},
    {"id": 4, "name": "불국사", "keywords": ["전통적인", "역사탐방", "고즈넉한", "힐링", "자연친화적인"]},
    {"id": 5, "name": "석굴암", "keywords": ["전통적인", "고즈넉한", "힐링", "자연친화적인", "산책"]},
    {"id": 6, "name": "경주월드", "keywords": ["친구여행", "데이트", "체험형", "사진맛집", "가족여행"]},
    {"id": 7, "name": "보문호", "keywords": ["드라이브", "산책", "힐링", "자연친화적인", "야경", "커플여행"]},
    {"id": 8, "name": "교촌한옥마을", "keywords": ["전통적인", "한옥감성", "사진맛집", "감성적인", "데이트"]},
    {"id": 9, "name": "국립경주박물관", "keywords": ["역사탐방", "전통적인", "가족여행", "조용한", "문화유산"]},
    {"id": 10, "name": "월정교","keywords": ["야경", "로맨틱한", "사진맛집", "감성적인", "산책", "데이트"]},
]

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

# 모든 유니크 키워드 추출 및 Trie에 저장
all_keywords = set()
trie_store = Trie()
for place in places_data:
    for kw in place["keywords"]:
        all_keywords.add(kw)
        trie_store.insert(kw)

unique_keywords_list = sorted(list(all_keywords))
num_keywords = len(unique_keywords_list)

# [자료구조 2] HashMap (파이썬의 dict)
# 사용 목적: 키워드별 인덱스 매핑 및 최종 TF-IDF 가중치 벡터 관리를 위함
keyword_to_idx = {kw: i for i, kw in enumerate(unique_keywords_list)}

# [알고리즘 1] TF-IDF (Term Frequency-Inverse Document Frequency)
# 사용 목적: 각 장소에서 특정 키워드가 가지는 상대적 중요도(가중치)를 계산하여 벡터화
# 원래 리뷰에서 계산해야 하지만, 여기서는 장소별 키워드 리스트를 하나의 문서로 취급하여 계산
def calculate_tfidf(places, kw_to_idx, total_kws_count):
    N = len(places)
    # 1. DF (Document Frequency - 해당 키워드를 가진 장소의 수) 계산
    df = collections.defaultdict(int)
    for place in places:
        for kw in set(place["keywords"]):
            df[kw] += 1

    # 2. TF-IDF 벡터 생성
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
                idf = math.log(N / (1 + df[kw])) + 1  # idf 계산식(분모 0 방지)
                idx = kw_to_idx[kw]
                vector[idx] = tf * idf

        places_vectors.append(vector)

    return places_vectors


# TF-IDF 연산 수행해 장소별 1차원 가중치 벡터 획득
places_vectors = calculate_tfidf(places_data, keyword_to_idx, num_keywords)


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

# K=3으로 군집화 실행
k = 3
clusters, centroids = kmeans_clustering(places_vectors, k=k)

# 결과 출력 및 시각화용 데이터 매핑
print("=== 키워드 분석 및 장소 분류 결과 ===")
print(f"총 추출된 유니크 키워드 개수: {num_keywords}개")

for cluster_idx, p_indices in enumerate(clusters):
    print(f"[군집 {cluster_idx + 1}] 카테고리 분류 장소 목록")
    # 각 군집을 대표하는 상위 키워드들을 추출하기 위해 중심점 활용
    centroid_vec = centroids[cluster_idx]
    # (키워드 인덱스, 가중치) 쌍으로 묶어 가중치가 높은 순으로 정렬
    top_kw_indices = sorted(
        enumerate(centroid_vec), key=lambda x: x[1], reverse=True
    )[:3]
    representative_keywords = [
        unique_keywords_list[idx] for idx, val in top_kw_indices if val > 0
    ]

    print(f"   * 주요 특징 키워드: {representative_keywords}")

    # 해당 군집에 속한 실제 장소 출력
    for p_idx in p_indices:
        place = places_data[p_idx]
        print(f"   - {place['name']} (ID: {place['id']})")
    print("-" * 50)
