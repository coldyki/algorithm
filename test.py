"""
test.py

GraphTrip 개인화 추천 시스템 통합 테스트.

테스트 시나리오:
  1. 기본 추천 (liked_places만 사용)
  2. CF 연동 추천 (역할1 CF 결과를 cf_places로 전달)
  3. 역할4 연동 확인 (get_place_ids_for_route 반환값 확인)
  4. 예외 처리 테스트
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from personalization.recommender import recommend_places, get_place_ids_for_route


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
    cf_places=[2, 8],
    top_k=5,
)
print_result(result_cf)


# -------------------------------------------------------
# 테스트 3: 역할4 연동 — get_place_ids_for_route
# 테스트 2의 recommend_places() 결과를 그대로 넘겨
# 추천 상세 정보는 유지하면서 ID 리스트만 추출한다.
# -------------------------------------------------------
print_divider("테스트 3: 역할4 연동 — get_place_ids_for_route")

place_ids = get_place_ids_for_route(result_cf)

if all(isinstance(pid, int) for pid in place_ids):
    print(f"  ✅ place_id 리스트 정상 반환: {place_ids}")
    print(f"  → 역할4 호출 예시: optimize_travel_route(start_place_id=1, recommended_place_ids={place_ids})")
else:
    print(f"  ❌ 반환값 오류: {place_ids}")


# -------------------------------------------------------
# 테스트 4: 예외 처리 — 빈 liked_places
# -------------------------------------------------------
print_divider("테스트 4: 예외 처리 — liked_places 빈 리스트")

try:
    recommend_places(liked_places=[])
    print("  ❌ 예외가 발생하지 않음 (오류)")
except ValueError as e:
    print(f"  ✅ ValueError 정상 발생: {e}")
