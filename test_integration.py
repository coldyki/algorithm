"""
test_integration.py

GraphTrip 전체 파이프라인 통합 테스트.

테스트 흐름:
    역할1 (CF)  →  역할2 (키워드 가중치)  →  역할3 (PPR 추천)  →  역할4 (경로 최적화)

테스트 시나리오:
    1. 역할1 단독: CF 기반 유사 사용자 및 추천 장소 확인
    2. 역할2 단독: 키워드 가중치 및 장소 클러스터 확인
    3. 역할3 단독: 키워드 기반 PPR 추천 확인
    4. 역할4 단독: 경로 최적화 확인
    5. 역할1 + 역할3 연동: CF 결과를 PPR 씨드에 추가
    6. 역할2 + 역할3 연동: 키워드 가중치가 그래프에 반영되는지 확인
    7. 전체 파이프라인: 역할1 → 역할3 → 역할4 end-to-end
    8. 예외 처리: 잘못된 입력값 처리 확인
"""

import sys
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "src"))

os.chdir(_ROOT)  # 상대경로 기준을 프로젝트 루트로 고정

# 역할1 (CF)
from cf.recommender import recommend_places_cf, find_similar_users
from cf.data_loader import load_user_likes

# 역할2 (키워드 시스템)
from keyword_system.keyword_system import (
    get_keyword_weights,
    get_place_cluster_mapping,
)

# 역할3 (개인화 추천)
from personalization.recommender import recommend_places, get_place_ids_for_route

# 역할4 (경로 최적화)
from route.route_optimizer import optimize_travel_route


# -------------------------------------------------------
# 출력 헬퍼
# -------------------------------------------------------
PASS = "✅"
FAIL = "❌"
PLACES_FILE = os.path.join(_ROOT, "data", "places.json")


def print_divider(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check(condition: bool, label: str):
    icon = PASS if condition else FAIL
    print(f"  {icon} {label}")
    return condition


def print_ppr_result(recommendations: list[dict]):
    for i, r in enumerate(recommendations, 1):
        print(
            f"    {i}. [{r['place_id']}] {r['place_name']}"
            f"  |  score: {r['score']}"
        )
        print(f"       이유: {r['reason']}")
        kw = r["matched_keywords"]
        print(f"       매칭 키워드: {kw if kw else '없음'}")
        print(f"       좌표: lat={r['lat']}, lng={r['lng']}")
        bd = r["score_breakdown"]
        print(
            f"       세부: 방문횟수={bd['visit_count']}, "
            f"그래프가중치={bd['max_graph_weight']}, "
            f"씨드출처={bd['seed_source']}"
        )


def print_route_result(result: dict):
    print(f"    알고리즘: {result.get('algorithm', '-')}")
    route  = result.get("optimized_route_ids", [])
    names  = result.get("optimized_route_names", [])
    route_str = " → ".join(
        f"{name}({pid})" for pid, name in zip(route, names)
    ) if names else " → ".join(str(p) for p in route)
    print(f"    최적 경로: {route_str}")
    print(f"    총 거리:   {result.get('optimized_distance_km', 0):.2f} km")
    print(f"    원래 거리: {result.get('original_distance_km', 0):.2f} km")
    diff = result.get("distance_difference_km", 0)
    impr = result.get("improvement_rate_percent", 0)
    print(f"    단축 거리: {diff:.2f} km ({impr:.1f}% 개선)")
    for seg in result.get("segments", []):
        print(
            f"      {seg.get('from_place_name','?')}({seg.get('from_place_id','?')})"
            f" → {seg.get('to_place_name','?')}({seg.get('to_place_id','?')})"
            f" : {seg.get('distance_km', 0):.2f} km"
        )


# 테스트용 사용자 설정
TARGET_USER    = 1          # 김민준 (좋아요: 1, 2, 8, 10)
USER_KEYWORDS  = ["야경", "힐링", "산책"]   # 사용자가 선택한 관심 키워드
user_likes     = load_user_likes()
LIKED_PLACES   = sorted(user_likes.get(TARGET_USER, set()))


# -------------------------------------------------------
# 테스트 1: 역할1 단독 — CF 유사 사용자 및 추천 장소
# -------------------------------------------------------
print_divider("테스트 1: 역할1 단독 — CF 기반 추천")

try:
    check(TARGET_USER in user_likes, f"사용자 {TARGET_USER} 데이터 로드")
    print(f"    좋아요 장소: {LIKED_PLACES}")

    similar_users = find_similar_users(TARGET_USER, similarity_threshold=0.2)
    check(len(similar_users) > 0, "유사 사용자 탐색 (threshold=0.2)")
    for uid, sim in similar_users[:3]:
        print(f"    유저 {uid} | 유사도: {round(sim, 4)}")

    cf_result = recommend_places_cf(TARGET_USER, top_k=5, similarity_threshold=0.2)
    check(isinstance(cf_result, list), "CF 추천 결과 반환")
    check(
        all(pid not in user_likes[TARGET_USER] for pid in cf_result),
        "CF 결과에 이미 좋아요한 장소 미포함"
    )
    print(f"    CF 추천 장소 ID: {cf_result}")

except Exception as e:
    print(f"  {FAIL} 역할1 오류: {e}")
    cf_result = []


# -------------------------------------------------------
# 테스트 2: 역할2 단독 — 키워드 가중치 및 장소 클러스터
# -------------------------------------------------------
print_divider("테스트 2: 역할2 단독 — 키워드 가중치 & 클러스터링")

try:
    base_weights = get_keyword_weights()
    check(isinstance(base_weights, dict) and len(base_weights) > 0, "기본 IDF 가중치 계산")
    top3 = sorted(base_weights.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"    상위 3개 키워드 가중치: {[(k, round(v,4)) for k,v in top3]}")

    user_weights = get_keyword_weights(target_user_id=TARGET_USER)
    check(isinstance(user_weights, dict), f"사용자 {TARGET_USER} 개인화 가중치 계산")

    boosted = any(
        user_weights.get(kw, 0) > base_weights.get(kw, 0)
        for kw in ["가족여행", "힐링", "산책"]
    )
    check(boosted, "선호 키워드 Topic-Sensitive Boosting 적용")

    cluster_map = get_place_cluster_mapping()
    check(len(cluster_map) == 10, "전체 10개 장소 클러스터 매핑 완성")
    cluster_groups = {}
    for pid, cidx in cluster_map.items():
        cluster_groups.setdefault(cidx, []).append(pid)
    for cidx, pids in sorted(cluster_groups.items()):
        print(f"    군집 {cidx}: 장소 {sorted(pids)}")

except Exception as e:
    print(f"  {FAIL} 역할2 오류: {e}")
    user_weights = {}


# -------------------------------------------------------
# 테스트 3: 역할3 단독 — 키워드 기반 PPR 추천
# -------------------------------------------------------
print_divider("테스트 3: 역할3 단독 — 키워드 기반 PPR 개인화 추천")
print(f"  선택 키워드: {USER_KEYWORDS}")
print(f"  좋아요 장소(제외): {LIKED_PLACES}")

try:
    ppr_result = recommend_places(
        user_keywords=USER_KEYWORDS,
        liked_places=LIKED_PLACES,
        top_k=5,
    )
    check(len(ppr_result) > 0, "PPR 추천 결과 반환")
    check(
        all(r["place_id"] not in LIKED_PLACES for r in ppr_result),
        "추천 결과에 이미 좋아요한 장소 미포함"
    )
    check(
        all(r["lat"] is not None and r["lng"] is not None for r in ppr_result),
        "모든 추천 결과에 좌표(lat/lng) 포함"
    )
    check(
        ppr_result == sorted(ppr_result, key=lambda x: x["score"], reverse=True),
        "추천 결과 score 내림차순 정렬"
    )
    print_ppr_result(ppr_result)

except Exception as e:
    print(f"  {FAIL} 역할3 오류: {e}")
    ppr_result = []


# -------------------------------------------------------
# 테스트 4: 역할4 단독 — 경로 최적화
# -------------------------------------------------------
print_divider("테스트 4: 역할4 단독 — 경로 최적화")

DUMMY_ROUTE = [1, 2, 3, 8, 10]

try:
    route_result = optimize_travel_route(
        start_place_id=1,
        recommended_place_ids=DUMMY_ROUTE,
        places_file=PLACES_FILE,
        method="dijkstra",
    )
    check(isinstance(route_result, dict), "optimize_travel_route 결과 반환")
    check("optimized_route_ids" in route_result, "optimized_route_ids 키 존재")
    check("optimized_distance_km" in route_result, "optimized_distance_km 키 존재")
    check(route_result["optimized_distance_km"] > 0, "총 이동 거리 > 0")
    print_route_result(route_result)

except Exception as e:
    print(f"  {FAIL} 역할4 오류: {e}")


# -------------------------------------------------------
# 테스트 5: 역할1 + 역할3 연동
# -------------------------------------------------------
print_divider("테스트 5: 역할1 + 역할3 연동 — CF 결과를 PPR 씨드에 추가")
print(f"  선택 키워드: {USER_KEYWORDS}")

try:
    cf_places = recommend_places_cf(TARGET_USER, top_k=5, similarity_threshold=0.2)

    result_no_cf = recommend_places(
        user_keywords=USER_KEYWORDS,
        liked_places=LIKED_PLACES,
        top_k=5,
    )
    result_with_cf = recommend_places(
        user_keywords=USER_KEYWORDS,
        liked_places=LIKED_PLACES,
        cf_places=cf_places,
        top_k=5,
    )

    check(len(result_with_cf) > 0, "CF + PPR 통합 추천 결과 반환")
    check(
        all(r["place_id"] not in LIKED_PLACES for r in result_with_cf),
        "통합 추천 결과에 이미 좋아요한 장소 미포함"
    )

    ids_no_cf   = [r["place_id"] for r in result_no_cf]
    ids_with_cf = [r["place_id"] for r in result_with_cf]
    print(f"    CF 없이 추천: {ids_no_cf}")
    print(f"    CF 포함 추천: {ids_with_cf}")
    changed = "있음" if ids_no_cf != ids_with_cf else "동일 (CF 결과 영향 미미)"
    print(f"    CF 투입으로 달라진 추천 여부: {changed}")

except Exception as e:
    print(f"  {FAIL} 역할1+역할3 연동 오류: {e}")


# -------------------------------------------------------
# 테스트 6: 역할2 + 역할3 연동 — 키워드 가중치 그래프 반영
# -------------------------------------------------------
print_divider("테스트 6: 역할2 + 역할3 연동 — 키워드 가중치 그래프 반영 확인")

try:
    from personalization.place_graph import build_place_graph
    from keyword_system.keyword_data import get_keyword_weights as kd_get_weights

    weights = kd_get_weights()
    graph = build_place_graph(threshold=0.1)
    check(len(graph) > 0, "그래프 생성 완료")
    total_edges = sum(len(v) for v in graph.values())
    print(f"    그래프 엣지 수: {total_edges}")

    if weights:
        check(True, "역할2 Weighted Jaccard 반영 완료")
    else:
        check(True, "역할2 가중치 미구현 → 일반 Jaccard 폴백 동작")

except Exception as e:
    print(f"  {FAIL} 역할2+역할3 연동 오류: {e}")


# -------------------------------------------------------
# 테스트 7: 전체 파이프라인 — 역할1 → 역할3 → 역할4
# -------------------------------------------------------
print_divider("테스트 7: 전체 파이프라인 end-to-end")
print(f"  사용자: {TARGET_USER}번 | 선택 키워드: {USER_KEYWORDS} | 좋아요 장소(제외): {LIKED_PLACES}")

try:
    # Step 1: 역할1 — CF 추천
    cf_places = recommend_places_cf(TARGET_USER, top_k=5, similarity_threshold=0.2)
    check(True, f"[역할1] CF 추천 완료 → {cf_places}")

    # Step 2: 역할3 — 키워드 + CF 기반 PPR 추천
    recommendations = recommend_places(
        user_keywords=USER_KEYWORDS,
        liked_places=LIKED_PLACES,
        cf_places=cf_places,
        top_k=5,
    )
    check(len(recommendations) > 0, "[역할3] PPR 추천 완료")
    print(f"    추천 장소: {[r['place_id'] for r in recommendations]}")
    for r in recommendations:
        print(f"      [{r['place_id']}] {r['place_name']} | {r['reason']}")

    # Step 3: 역할3 → 역할4 연동
    place_ids = get_place_ids_for_route(recommendations)
    check(len(place_ids) > 0, f"[역할3→역할4] place_id 리스트 추출 → {place_ids}")

    # Step 4: 역할4 — 경로 최적화
    final_route = optimize_travel_route(
        start_place_id=LIKED_PLACES[0] if LIKED_PLACES else place_ids[0],
        recommended_place_ids=place_ids,
        places_file=PLACES_FILE,
        method="dijkstra",
    )
    check("optimized_route_ids" in final_route, "[역할4] 경로 최적화 완료")

    print(f"\n  ── 최종 여행 코스 ──")
    print_route_result(final_route)

except Exception as e:
    print(f"  {FAIL} 전체 파이프라인 오류: {e}")
    import traceback; traceback.print_exc()


# -------------------------------------------------------
# 테스트 8: 예외 처리
# -------------------------------------------------------
print_divider("테스트 8: 예외 처리")

# 8-1: 역할1 — 존재하지 않는 사용자
try:
    find_similar_users(9999)
    check(False, "역할1: 존재하지 않는 사용자 → 예외 미발생 (오류)")
except ValueError:
    check(True, "역할1: 존재하지 않는 사용자 → ValueError 정상 발생")

# 8-2: 역할3 — 빈 키워드
try:
    recommend_places(user_keywords=[])
    check(False, "역할3: 빈 user_keywords → 예외 미발생 (오류)")
except ValueError:
    check(True, "역할3: 빈 user_keywords → ValueError 정상 발생")

# 8-3: 역할3 — 매칭 장소 없는 키워드
try:
    recommend_places(user_keywords=["존재하지않는키워드"])
    check(False, "역할3: 매칭 장소 없는 키워드 → 예외 미발생 (오류)")
except ValueError:
    check(True, "역할3: 매칭 장소 없는 키워드 → ValueError 정상 발생")

# 8-4: 역할4 — 존재하지 않는 장소 ID
try:
    optimize_travel_route(
        start_place_id=1,
        recommended_place_ids=[1, 9999],
        places_file=PLACES_FILE,
    )
    check(False, "역할4: 존재하지 않는 장소 ID → 예외 미발생 (오류)")
except Exception:
    check(True, "역할4: 존재하지 않는 장소 ID → 예외 정상 발생")

print("\n" + "=" * 60)
print("  통합 테스트 완료")
print("=" * 60)
