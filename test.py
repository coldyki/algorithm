"""
test.py

GraphTrip 개인화 추천 시스템 통합 테스트.

테스트 시나리오:
  1. 기본 추천 (liked_places만 사용)
  2. CF 연동 추천 (역할1 CF 결과를 cf_places로 전달)
  3. 재현성 테스트 (walk_seed 고정)
  4. 역할4 연동 확인 (반환값에 lat/lng 포함 여부)
  5. 예외 처리 테스트
"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가 (어느 위치에서 실행해도 동작)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from personalization.recommender import recommend_places


# -------------------------------------------------------
# 출력 헬퍼
# -------------------------------------------------------
def print_divider(title: str):
    print("\n" + "=" * 55)
    print(f"  {title}")
    print("=" * 55)


def print_result(recommendations: list[dict]):
    for i, place in enumerate(recommendations, 1):
        print(
            f"  {i}. [{place['place_id']}] {place['place_name']}"
            f"  |  score: {place['score']}"
        )
        print(f"      이유: {place['reason']}")
        print(
            f"      매칭 키워드: "
            f"{place['matched_keywords'] if place['matched_keywords'] else '없음'}"
        )
        print(
            f"      좌표(역할4용): lat={place['lat']}, lng={place['lng']}"
        )
        bd = place["score_breakdown"]
        print(
            f"      세부점수: 방문횟수={bd['visit_count']}, "
            f"그래프가중치={bd['max_graph_weight']}"
        )
        print()


# -------------------------------------------------------
# 테스트 1: 기본 추천 (liked_places만)
# -------------------------------------------------------
print_divider("테스트 1: 기본 추천 (CF 없음)")
print("  사용자 좋아요 장소: 황리단길(1), 월정교(10)")

result_basic = recommend_places(
    liked_places=[1, 10],
    top_k=5,
    walk_seed=42,    # 재현성을 위해 시드 고정
)
print_result(result_basic)


# -------------------------------------------------------
# 테스트 2: CF 연동 추천 (역할1 결과 통합)
# -------------------------------------------------------
print_divider("테스트 2: CF 연동 추천 (역할1 결과 포함)")
print("  사용자 좋아요 장소: 황리단길(1), 월정교(10)")
print("  역할1 CF 결과 (유사 사용자 선호 장소): 동궁과 월지(2), 교촌한옥마을(8)")

result_cf = recommend_places(
    liked_places=[1, 10],
    cf_places=[2, 8],   # 역할1이 계산한 CF 추천 결과
    top_k=5,
    walk_seed=42,
)
print_result(result_cf)


# -------------------------------------------------------
# 테스트 3: 재현성 확인 (동일 seed → 동일 결과)
# -------------------------------------------------------
print_divider("테스트 3: 재현성 확인 (seed=42 두 번 실행)")

result_a = recommend_places(liked_places=[3, 4], top_k=3, walk_seed=42)
result_b = recommend_places(liked_places=[3, 4], top_k=3, walk_seed=42)

ids_a = [r["place_id"] for r in result_a]
ids_b = [r["place_id"] for r in result_b]

if ids_a == ids_b:
    print(f"  ✅ 재현성 확인: 두 결과 동일 → {ids_a}")
else:
    print(f"  ❌ 재현성 실패: {ids_a} vs {ids_b}")


# -------------------------------------------------------
# 테스트 4: 역할4 연동 — 좌표 포함 여부 확인
# -------------------------------------------------------
print_divider("테스트 4: 역할4(Dijkstra) 연동 — 좌표 확인")

result_coord = recommend_places(liked_places=[7], top_k=3, walk_seed=42)
all_have_coords = all(
    r["lat"] is not None and r["lng"] is not None for r in result_coord
)

if all_have_coords:
    print("  ✅ 모든 추천 결과에 lat/lng 포함 — 역할4에서 바로 사용 가능")
    for r in result_coord:
        print(
            f"     [{r['place_id']}] {r['place_name']} "
            f"→ ({r['lat']}, {r['lng']})"
        )
else:
    print("  ❌ 좌표 누락 — places.json 확인 필요")


# -------------------------------------------------------
# 테스트 5: 예외 처리 — 빈 liked_places
# -------------------------------------------------------
print_divider("테스트 5: 예외 처리 — liked_places 빈 리스트")

try:
    recommend_places(liked_places=[])
    print("  ❌ 예외가 발생하지 않음 (오류)")
except ValueError as e:
    print(f"  ✅ ValueError 정상 발생: {e}")
