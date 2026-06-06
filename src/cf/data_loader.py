import pandas as pd


# 자료구조: Dictionary(HashMap), Set
# 목적:
# - user_id를 key로 사용하여 사용자별 좋아요 장소를 빠르게 조회한다.
# - 각 사용자의 좋아요 장소 목록은 Set으로 저장하여 중복 제거와 집합 연산을 쉽게 한다.
def load_user_likes(path="data/user_likes.csv"):
    """
    user_likes.csv 파일을 읽어서 사용자별 좋아요 장소 집합을 반환한다.

    CSV 형식:
        user_id,place_id
        1,1
        1,2

    반환 형식:
        {
            1: {1, 2, 8, 10},
            2: {1, 2, 10}
        }

    사용 자료구조:
    - Dictionary(HashMap): user_id -> liked_place_set 매핑
    - Set: 각 사용자가 좋아요한 place_id 저장

    Set을 사용하는 이유:
    - 중복 장소 제거
    - 교집합 계산
    - 합집합 계산
    - 차집합 계산
    """

    df = pd.read_csv(path)

    user_likes = {}

    for _, row in df.iterrows():
        user_id = int(row["user_id"])
        place_id = int(row["place_id"])

        if user_id not in user_likes:
            user_likes[user_id] = set()

        user_likes[user_id].add(place_id)

    return user_likes