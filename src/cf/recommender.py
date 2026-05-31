from src.cf.data_loader import load_user_likes
from src.cf.similarity import jaccard_similarity


def find_similar_users(target_user_id, similarity_threshold=0.3):
    """
    target_user_id와 취향이 비슷한 사용자를 찾는다.

    처리 과정:
    1. user_likes.csv에서 사용자별 좋아요 장소 데이터를 읽는다.
    2. target_user_id 사용자의 좋아요 장소와 다른 사용자들의 좋아요 장소를 비교한다.
    3. Jaccard Similarity를 계산한다.
    4. similarity_threshold 이상인 사용자만 유사 사용자로 사용한다.
    5. 유사도 높은 순서로 정렬한다.

    Args:
        target_user_id: 추천을 받을 사용자 ID
        similarity_threshold: 유사 사용자로 인정할 최소 유사도

    Returns:
        [(user_id, similarity), ...]
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


def recommend_places_cf(target_user_id, top_k=5, similarity_threshold=0.3):
    """
    Collaborative Filtering 기반으로 추천 장소 ID 리스트를 반환한다.

    추천 방식:
    1. target_user_id와 유사한 사용자들을 찾는다.
    2. 유사 사용자들이 좋아요한 장소 중 target_user_id가 아직 좋아요하지 않은 장소를 찾는다.
    3. 각 장소에 대해 유사도 점수를 누적한다.
    4. 점수가 높은 장소 순서대로 top_k개를 추천한다.

    점수 계산:
        place_score += similar_user_similarity

    예:
        User2와 유사도 0.5이고 User2가 장소 10을 좋아함
        → 장소 10 점수 += 0.5

        User3와 유사도 0.3이고 User3도 장소 10을 좋아함
        → 장소 10 점수 += 0.3

        최종 장소 10 점수 = 0.8

    Returns:
        [place_id, place_id, ...]
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

        # 유사 사용자가 좋아했지만, 현재 사용자는 아직 좋아하지 않은 장소만 추천 후보로 사용
        candidate_places = other_places - target_places

        for place_id in candidate_places:
            place_scores[place_id] = place_scores.get(place_id, 0) + similarity

    sorted_places = sorted(
        place_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [place_id for place_id, score in sorted_places[:top_k]]


def recommend_places_cf_with_scores(target_user_id, top_k=5, similarity_threshold=0.3):
    """
    Collaborative Filtering 추천 결과를 점수와 추천 이유까지 포함해 반환한다.

    이 함수는 발표, 디버깅, Streamlit 화면 출력용으로 사용한다.

    Returns:
        [
            {
                "place_id": 6,
                "score": 1.2333,
                "reason": "비슷한 취향의 사용자가 좋아요/저장한 장소입니다."
            }
        ]
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
        candidate_places = other_places - target_places

        for place_id in candidate_places:
            place_scores[place_id] = place_scores.get(place_id, 0) + similarity

    sorted_places = sorted(
        place_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    result = []

    for place_id, score in sorted_places[:top_k]:
        result.append({
            "place_id": place_id,
            "score": round(score, 4),
            "reason": "비슷한 취향의 사용자가 좋아요/저장한 장소입니다."
        })

    return result