# 알고리즘: Jaccard Similarity
# 자료구조: Set
# 목적:
# - 두 사용자의 좋아요 장소 집합이 얼마나 비슷한지 계산한다.
# - Collaborative Filtering에서 유사 사용자를 찾는 기준으로 사용한다.
def jaccard_similarity(set1, set2):
    """
    두 사용자의 좋아요 장소 집합을 비교하여 Jaccard Similarity를 계산한다.

    공식:
        J(A, B) = |A ∩ B| / |A ∪ B|

    의미:
    - 1에 가까울수록 두 사용자의 취향이 비슷함
    - 0에 가까울수록 두 사용자의 취향이 다름

    예:
        User1 = {1, 2, 8}
        User2 = {1, 2, 10}

        교집합 = {1, 2}
        합집합 = {1, 2, 8, 10}

        유사도 = 2 / 4 = 0.5

    사용 자료구조:
    - Set
        set1 & set2 : 교집합
        set1 | set2 : 합집합
    """

    union = set1 | set2

    if len(union) == 0:
        return 0

    return len(set1 & set2) / len(union)