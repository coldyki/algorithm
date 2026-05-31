# CF Recommendation

## 담당

이수광

---

## 기능 설명

사용자 행동 기반 Collaborative Filtering 추천 시스템입니다.

사용자의 장소 좋아요/저장 데이터를 기반으로 비슷한 취향의 사용자를 찾고, 유사 사용자가 좋아했지만 현재 사용자가 아직 좋아하지 않은 장소를 추천합니다.

---

## 사용 데이터

### user_likes.csv

사용자의 장소 좋아요/저장 데이터를 저장합니다.

예시

user_id | place_id
--- | ---
1 | 1
1 | 2
1 | 8

위 예시는 User1이 장소 1, 2, 8을 좋아요한 상태를 의미합니다.

---

## 사용 자료구조

### Set

사용자별 좋아요 장소 목록을 집합(Set)으로 저장합니다.

사용 이유

- 중복 제거
- 교집합 계산
- 합집합 계산
- 추천 후보 장소 계산

예시

```python
{1, 2, 8, 10}
```

---

### Dictionary

사용자별 좋아요 데이터와 장소별 추천 점수를 저장합니다.

사용 이유

- 사용자 ID 기준 빠른 조회
- 장소 ID 기준 점수 누적

예시

```python
{
    1: {1, 2, 8, 10},
    2: {1, 2, 10}
}
```

---

## 사용 알고리즘

### Collaborative Filtering

비슷한 취향을 가진 사용자가 좋아한 장소를 추천하는 방식입니다.

추천 흐름

```text
사용자 선택
↓
유사 사용자 탐색
↓
유사 사용자가 좋아한 장소 수집
↓
추천 점수 계산
↓
상위 장소 추천
```

---

### Jaccard Similarity

두 사용자의 좋아요 장소 집합이 얼마나 비슷한지 계산합니다.

공식

```text
J(A,B) = |A∩B| / |A∪B|
```

예시

```text
User1 = {1, 2, 8}
User2 = {1, 2, 10}

교집합 = {1, 2}
합집합 = {1, 2, 8, 10}

유사도 = 2 / 4 = 0.5
```

유사도가 높을수록 취향이 비슷하다고 판단합니다.

---

## 추천 점수 계산 방식

유사 사용자가 좋아한 장소 중 현재 사용자가 아직 좋아하지 않은 장소를 추천 후보로 사용합니다.

예시

```text
User2 유사도 = 0.5
User2가 장소 10 좋아요

→ 장소 10 점수 +0.5

User3 유사도 = 0.3
User3도 장소 10 좋아요

→ 장소 10 점수 +0.3
```

최종

```text
장소 10 점수 = 0.8
```

점수가 높은 장소를 우선 추천합니다.

---

## 유사도 Threshold

너무 낮은 유사도를 가진 사용자는 추천에 반영하지 않습니다.

현재 설정

```python
similarity_threshold = 0.3
```

즉,

```text
유사도 0.3 이상
→ 추천 반영

유사도 0.3 미만
→ 제외
```

---

## 주요 함수

### find_similar_users()

특정 사용자와 유사한 사용자를 찾습니다.

```python
find_similar_users(
    target_user_id=1,
    similarity_threshold=0.3
)
```

---

### recommend_places_cf()

추천 장소 ID만 반환합니다.

```python
recommend_places_cf(
    target_user_id=1,
    top_k=5
)
```

예시 반환값

```python
[6, 7, 3, 9, 4]
```

---

### recommend_places_cf_with_scores()

추천 장소 ID, 점수, 추천 이유를 함께 반환합니다.

```python
recommend_places_cf_with_scores(
    target_user_id=1,
    top_k=5
)
```

예시 반환값

```python
[
    {
        "place_id": 6,
        "score": 1.2333,
        "reason": "비슷한 취향의 사용자가 좋아요한 장소입니다."
    }
]
```

---

## 실행 방법

프로젝트 루트 디렉토리에서 실행

```bash
python -m src.cf.test_cf
```

---

## 다른 모듈과의 연동

CF 추천 결과는 Personalized PageRank 모듈의 입력값으로 전달됩니다.

```python
cf_places = recommend_places_cf(
    target_user_id=1
)
```

예시

```python
recommend_places(
    liked_places=[1, 2, 8],
    cf_places=cf_places
)
```

이후 Personalized PageRank가 최종 추천 장소를 계산하고, 최종 추천 결과는 Route Optimizer 모듈로 전달됩니다.

## 향후 확장 계획

현재는 test_cf.py에서 테스트 사용자 ID를 직접 지정하여 추천을 수행합니다.

```python
user_id = 1