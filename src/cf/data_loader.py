import pandas as pd


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

    set을 사용하는 이유:
    - 중복 장소 제거
    - 교집합/합집합 연산을 빠르게 수행하기 위함
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