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
    2. Jaccard Similarity 기반 유사도 확인
    3. Collaborative Filtering 추천 장소 ID 리스트 출력
    4. Heap 기반 Top-K 추천 결과 확인
    5. 추천 장소별 점수와 추천 이유 출력
    """

    user_id = 1
    top_k = 5
    similarity_threshold = 0.3

    print("=" * 60)
    print("Collaborative Filtering 테스트")
    print("=" * 60)

    print(f"대상 사용자: User{user_id}")
    print(f"추천 개수 top_k: {top_k}")
    print(f"유사도 threshold: {similarity_threshold}")

    print("\n[1] Jaccard Similarity 기반 유사 사용자 목록")
    similar_users = find_similar_users(
        user_id,
        similarity_threshold=similarity_threshold
    )

    if not similar_users:
        print("유사도 threshold 이상인 사용자가 없습니다.")
    else:
        for other_user, similarity in similar_users:
            print(f"- User{other_user}: 유사도 {similarity:.4f}")

    print("\n[2] Collaborative Filtering 추천 장소 ID")
    recommended_place_ids = recommend_places_cf(
        user_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )
    print(recommended_place_ids)

    print("\n[3] Heap 기반 Top-K 추천 상세 결과")
    recommendations = recommend_places_cf_with_scores(
        user_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )

    if not recommendations:
        print("추천 가능한 장소가 없습니다.")
    else:
        for rank, item in enumerate(recommendations, start=1):
            print(
                f"{rank}. 장소 ID: {item['place_id']}, "
                f"점수: {item['score']}, "
                f"추천 이유: {item['reason']}"
            )

    print("\n테스트 완료")


if __name__ == "__main__":
    main()