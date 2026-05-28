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

## Collaboration

* GitHub

---

# 프로젝트 구조

```text
algorithm/
├─ data/
│  ├─ users.csv
│  ├─ places.csv
│  ├─ user_likes.csv
│  └─ distances.csv
│
├─ src/
│  ├─ recommendation.py
│  ├─ keyword_recommend.py
│  ├─ personalized.py
│  ├─ route_optimizer.py
│  └─ data_loader.py
│
├─ app.py
├─ requirements.txt
├─ .gitignore
└─ README.md
```

---

# 팀 역할

## 1. 이수광

* 사용자 행동 기반 추천 시스템 구현
* Collaborative Filtering
* Jaccard Similarity

## 2. 심찬기

* 키워드 분석 시스템 구현
* Inverted Index
* Topic-Sensitive Ranking

## 3. 최정현

* Personalized 추천 시스템 구현
* Personalized PageRank

## 4. 박종빈

* 여행 코스 최적화 구현
* Dijkstra Algorithm
* Greedy Algorithm

---

# Git 협업 규칙

## 브랜치 전략

main 브랜치는 최종 통합 브랜치로 사용합니다.

각 팀원은 기능별 브랜치를 생성하여 작업합니다.

예시:

```bash
feature/recommendation
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
