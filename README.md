# algorithm

# GraphTrip

사용자 행동 및 키워드 기반 개인화 여행 코스 추천 서비스

## Team

Graph Navigators

---

# 프로젝트 소개

GraphTrip은 사용자의 장소 저장/좋아요 데이터와 리뷰 키워드를 기반으로 여행 장소 및 여행 코스를 추천하는 서비스입니다.

초기 단계에서는 사용자 행동 데이터를 기반으로 비슷한 취향의 사용자가 함께 저장한 장소를 추천합니다.

이후에는 리뷰 키워드(감성적인, 조용한, 사진맛집 등)를 활용하여 사용자 취향 기반 개인화 추천으로 확장할 수 있습니다.

또한 추천 장소들을 이동 거리 기준으로 최적화하여 하나의 여행 코스로 제공합니다.

---

# 주요 기능

* 사용자 행동 기반 장소 추천
* 키워드 기반 장소 분류
* Personalized 추천
* 최적 여행 코스 생성
* 추천 이유 출력

---

# 기술 스택

## Language

* Python

## Library

* pandas
* networkx
* streamlit

## Data

* CSV 기반 더미 데이터

### 더미 사용자 데이터

본 프로젝트는 프로토타입 단계이므로 실제 서비스 데이터 대신 더미 사용자 데이터를 사용합니다.

#### users.csv

사용자 정보를 저장합니다.

```csv
user_id,user_name
1,User1
2,User2
...
```

#### user_likes.csv

사용자의 장소 저장/좋아요 데이터를 저장합니다.

```csv
user_id,place_id
1,1
1,2
1,8
```

위 예시는 User1이 황리단길(id=1), 동궁과 월지(id=2), 교촌한옥마을(id=8)을 좋아요한 상태를 의미합니다.

Collaborative Filtering 추천 시스템은 해당 데이터를 기반으로 사용자 간 유사도를 계산합니다.

현재는 약 30명의 더미 사용자 데이터를 사용하여 추천 알고리즘을 검증합니다.

추후 실제 서비스로 확장할 경우 좋아요/저장 이벤트를 데이터베이스에 저장하여 실시간으로 추천 결과에 반영할 수 있습니다.

## Collaboration

* GitHub

---

# 프로젝트 구조

```text
algorithm/
├─ data/
│  ├─ places.json
│  ├─ users.csv
│  └─ user_likes.csv
│
├─ src/
│  ├─ cf/
│  ├─ keyword_system/
│  ├─ personalization/
│  └─ route/
│
├─ app.py
├─ requirements.txt
└─ README.md
```

---

# 팀 역할

## 1. 이수광

* 사용자 행동 기반 추천 시스템 구현
* Collaborative Filtering
* Jaccard Similarity

## 2. 박종빈

* 키워드 분석 시스템 구현
* Inverted Index
* Topic-Sensitive Ranking

## 3. 심찬기

* Personalized 추천 시스템 구현
* Personalized PageRank

## 4. 최정현

* 여행 코스 최적화 구현
* Dijkstra Algorithm
* Greedy Algorithm

---

# Git 협업 규칙

## 브랜치 전략

main 브랜치는 최종 통합 브랜치로 사용합니다.

각 팀원은 기능별 브랜치를 생성하여 작업합니다.


```bash
feature/cf
feature/keyword
feature/pagerank
feature/route
```

---

## 작업 순서

### main 최신화

```bash
git checkout main
git pull origin main
```

### 브랜치 생성

```bash
git checkout -b feature/브랜치이름
```

### 작업 후 업로드

```bash
git add .
git commit -m "feat: 기능 설명"
git push -u origin 브랜치이름
```

---

# 개발 컨벤션

## 함수 구조

* 기능 단위로 함수 분리
* 입력/출력 형식 통일
* CSV 데이터 형식 유지

## 추천 시스템 출력 형식 예시

```python
recommended_place_ids = [1, 2, 3]

recommend_reason = {
    1: "비슷한 취향의 사용자가 저장한 장소입니다."
}
```

---

# 실행 방법

## 라이브러리 설치

```bash
pip install -r requirements.txt
```

## Streamlit 실행

```bash
streamlit run app.py
```

---

# 최종 목표

## 최소 목표

* 추천 기능 정상 동작
* 여행 코스 생성 기능 구현

## 추가 목표

* 키워드 기반 개인화 추천
* 지도 API 연동
* 로그인 기능
* 인기 장소 랭킹
