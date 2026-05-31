from src.cf.recommender import (
    find_similar_users,
    recommend_places_cf,
    recommend_places_cf_with_scores
)


def main():
    """
    CF 추천 모듈 테스트 실행 파일.

    실행 명령어:
        python -m src.cf.test_cf

    테스트 내용:
    1. 특정 사용자와 유사한 사용자 목록 출력
    2. CF 추천 장소 ID 리스트 출력
    3. 추천 장소별 점수와 추천 이유 출력
    """

    user_id = 1
    similarity_threshold = 0.3

    print("=== Collaborative Filtering 테스트 ===")
    print(f"대상 사용자: User{user_id}")
    print(f"유사도 threshold: {similarity_threshold}")

    print("\n=== 유사 사용자 목록 ===")
    similar_users = find_similar_users(
        user_id,
        similarity_threshold=similarity_threshold
    )

    for other_user, similarity in similar_users:
        print(f"User{other_user}: 유사도 {similarity:.4f}")

    print("\n=== CF 추천 장소 ID ===")
    recommended_place_ids = recommend_places_cf(
        user_id,
        top_k=5,
        similarity_threshold=similarity_threshold
    )
    print(recommended_place_ids)

    print("\n=== CF 추천 상세 결과 ===")
    recommendations = recommend_places_cf_with_scores(
        user_id,
        top_k=5,
        similarity_threshold=similarity_threshold
    )

    for item in recommendations:
        print(
            f"장소 ID: {item['place_id']}, "
            f"점수: {item['score']}, "
            f"추천 이유: {item['reason']}"
        )


if __name__ == "__main__":
    main()