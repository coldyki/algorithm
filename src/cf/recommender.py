import heapq

from src.cf.data_loader import load_user_likes
from src.cf.similarity import jaccard_similarity


def find_similar_users(target_user_id, similarity_threshold=0.3):
    """
    [알고리즘] Jaccard Similarity
    [자료구조] Set, Dictionary

    target_user_id와 취향이 비슷한 사용자를 찾는다.

    user_likes.csv에서 사용자별 좋아요 장소 데이터를 읽고,
    각 사용자의 좋아요 장소 집합을 비교하여 Jaccard Similarity를 계산한다.

    similarity_threshold 이상인 사용자만 유사 사용자로 사용한다.
    """

    user_likes = load_user_likes()

    if target_user_id not in user_likes:
        raise ValueError(f"사용자 ID {target_user_id}가 user_likes.csv에 없습니다.")

    target_places = user_likes[target_user_id]
    similarities = []

    for other_user, places in user_likes.items():
        if other_user == target_user_id:
            continue

        similarity = jaccard_similarity(target_places, places)

        if similarity >= similarity_threshold:
            similarities.append((other_user, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)

    return similarities


def _calculate_cf_scores(target_user_id, similarity_threshold=0.3):
    """
    [알고리즘] Collaborative Filtering
    [자료구조] Dictionary / HashMap

    CF 추천 후보별 점수를 계산한다.

    점수 계산 방식:
    - 유사 사용자가 좋아한 장소 중 현재 사용자가 아직 좋아하지 않은 장소를 후보로 선정
    - 후보 장소의 점수에 유사 사용자의 Jaccard Similarity 값을 누적

    반환:
        {
            place_id: score
        }
    """

    user_likes = load_user_likes()

    if target_user_id not in user_likes:
        raise ValueError(f"사용자 ID {target_user_id}가 user_likes.csv에 없습니다.")

    target_places = user_likes[target_user_id]

    similar_users = find_similar_users(
        target_user_id,
        similarity_threshold=similarity_threshold
    )

    place_scores = {}

    for other_user, similarity in similar_users:
        other_places = user_likes[other_user]

        # Set 차집합:
        # 유사 사용자가 좋아했지만 현재 사용자는 아직 좋아하지 않은 장소만 추천 후보로 사용
        candidate_places = other_places - target_places

        for place_id in candidate_places:
            place_scores[place_id] = place_scores.get(place_id, 0) + similarity

    return place_scores


def _get_top_k_places_by_heap(place_scores, top_k=5):
    """
    [자료구조] Heap / Priority Queue

    추천 후보 장소 중 점수가 높은 상위 top_k개 장소를 추출한다.

    Python의 heapq는 기본적으로 min heap이지만,
    heapq.nlargest()를 사용하면 내부적으로 heap 기반으로 상위 K개를 선택할 수 있다.
    """

    top_items = heapq.nlargest(
        top_k,
        place_scores.items(),
        key=lambda item: item[1]
    )

    return top_items


def recommend_places_cf(target_user_id, top_k=5, similarity_threshold=0.3):
    """
    [알고리즘] Collaborative Filtering
    [자료구조] Dictionary, Heap

    Collaborative Filtering 기반으로 추천 장소 ID 리스트를 반환한다.

    반환 예시:
        [6, 7, 3, 9, 4]
    """

    place_scores = _calculate_cf_scores(
        target_user_id,
        similarity_threshold=similarity_threshold
    )

    top_items = _get_top_k_places_by_heap(place_scores, top_k=top_k)

    return [place_id for place_id, score in top_items]


def recommend_places_cf_with_scores(target_user_id, top_k=5, similarity_threshold=0.3):
    """
    [알고리즘] Collaborative Filtering
    [자료구조] Dictionary, Heap

    추천 장소 ID, 추천 점수, 추천 이유를 함께 반환한다.

    발표, 디버깅, Streamlit 화면 출력용으로 사용한다.
    """

    place_scores = _calculate_cf_scores(
        target_user_id,
        similarity_threshold=similarity_threshold
    )

    top_items = _get_top_k_places_by_heap(place_scores, top_k=top_k)

    result = []

    for place_id, score in top_items:
        result.append({
            "place_id": place_id,
            "score": round(score, 4),
            "reason": "비슷한 취향의 사용자가 좋아요/저장한 장소입니다."
        })

    return result