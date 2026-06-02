import sys
import os
import streamlit as st

# ─── 경로 설정 ────────────────────────────────────────────────
# cf/recommender.py 가 "from src.cf.xxx" 형식으로 import하므로
# ROOT(프로젝트 루트)를 sys.path 맨 앞에 추가해야 한다.
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src")
for p in [ROOT, SRC]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─── 알고리즘 모듈 import ──────────────────────────────────────
# cf/recommender.py: "from src.cf.xxx" → ROOT가 sys.path에 있어야 함
from src.cf.recommender import recommend_places_cf_with_scores
from src.cf.data_loader import load_user_likes
# keyword_system: SRC 기준 import
from keyword_system.keyword_data import get_place_dict, get_place_keywords
from keyword_system.keyword_system import get_keyword_weights
# route: SRC 기준 import
from route.route_optimizer import optimize_travel_route

# personalization: "from personalization.xxx" 형식
try:
    from personalization.recommender import recommend_places as rwr_recommend
    PERS_AVAILABLE = True
except Exception as _e:
    PERS_AVAILABLE = False
    _PERS_ERROR = str(_e)

# ─── 데이터 캐싱 ──────────────────────────────────────────────
@st.cache_data
def get_places():
    return get_place_dict()   # {id: {name, lat, lng, keywords}}

@st.cache_data
def get_kw():
    return get_place_keywords()  # {id: [kw, ...]}

@st.cache_data
def get_all_users():
    return load_user_likes()  # {user_id: set(place_id)}

# ─── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(page_title="경주 여행 추천", layout="centered", initial_sidebar_state="expanded")

PLACES     = get_places()
KW_MAP     = get_kw()
USER_LIKES = get_all_users()
USER_IDS   = sorted(USER_LIKES.keys())

# ─── session_state 초기화 ──────────────────────────────────────
def _init():
    defaults = {
        "page": "홈",
        "selected_place": None,
        "search_query": "",
        "current_user": USER_IDS[0] if USER_IDS else 1,
        "liked": list(USER_LIKES.get(USER_IDS[0] if USER_IDS else 1, set())),
        "saved_routes": {},   # {user_id: [{name, stops, names, distance, liked}]}
        "last_route": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ─── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.title("🏛️ 경주 여행")

    # 사용자 선택 (CF 테스트용)
    uid = st.selectbox("👤 사용자 선택", USER_IDS,
                       index=USER_IDS.index(st.session_state.current_user)
                       if st.session_state.current_user in USER_IDS else 0,
                       key="uid_select")
    if uid != st.session_state.current_user:
        st.session_state.current_user = uid
        st.session_state.liked = list(USER_LIKES.get(uid, set()))
        st.rerun()

    st.markdown("---")
    pages = ["홈", "장소 검색", "개인화 추천", "경로 추천", "좋아요한 장소", "저장한 경로"]
    icons  = ["🏠", "🔍", "✨", "🗺️", "❤️", "📍"]
    for icon, pg in zip(icons, pages):
        if st.button(f"{icon} {pg}", use_container_width=True, key=f"nav_{pg}"):
            st.session_state.page = pg
            st.session_state.selected_place = None

# ─── 공통 유틸 ────────────────────────────────────────────────
def go_place(pid):
    st.session_state.selected_place = pid
    st.session_state.page = "장소 상세"

def toggle_like(pid):
    if pid in st.session_state.liked:
        st.session_state.liked.remove(pid)
    else:
        st.session_state.liked.append(pid)

def place_name(pid):
    return PLACES.get(pid, {}).get("name", f"장소{pid}")

def place_keywords(pid):
    return KW_MAP.get(pid, [])


# ═══════════════════════════════════════════════════════════════
# 화면 함수들
# ═══════════════════════════════════════════════════════════════

# ─── 홈 ───────────────────────────────────────────────────────
def page_home():
    st.markdown("## 🏛️ 경주 여행 추천")
    st.markdown(f"현재 사용자: **User {st.session_state.current_user}**")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("검색어", placeholder="장소명 또는 키워드 입력", label_visibility="hidden")
    with col2:
        if st.button("검색", use_container_width=True):
            st.session_state.search_query = query
            st.session_state.page = "장소 검색"
            st.rerun()

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔍 장소 검색", use_container_width=True):
            st.session_state.page = "장소 검색"; st.rerun()
    with c2:
        if st.button("✨ 개인화 추천", use_container_width=True):
            st.session_state.page = "개인화 추천"; st.rerun()
    with c3:
        if st.button("🗺️ 경로 추천", use_container_width=True):
            st.session_state.page = "경로 추천"; st.rerun()

    st.markdown("---")
    st.markdown("### 🌟 전체 장소")
    cols = st.columns(2)
    for i, (pid, info) in enumerate(PLACES.items()):
        with cols[i % 2]:
            with st.container(border=True):
                liked = "❤️" if pid in st.session_state.liked else "🤍"
                st.markdown(f"**{liked} {info['name']}**")
                st.caption(" ".join(f"#{kw}" for kw in info["keywords"][:3]))
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("상세", key=f"h_d_{pid}", use_container_width=True):
                        go_place(pid); st.rerun()
                with bc2:
                    lbl = "취소" if pid in st.session_state.liked else "좋아요"
                    if st.button(lbl, key=f"h_l_{pid}", use_container_width=True):
                        toggle_like(pid); st.rerun()


# ─── 장소 검색 ────────────────────────────────────────────────
def page_search():
    st.markdown("## 🔍 장소 검색")
    q = st.text_input("검색어", value=st.session_state.search_query,
                      placeholder="장소명, 키워드 (예: 야경, 힐링)")
    st.session_state.search_query = q

    results = []
    for pid, info in PLACES.items():
        if (q.lower() in info["name"]) or any(q in kw for kw in info["keywords"]):
            results.append(pid)
    if not q:
        results = list(PLACES.keys())

    st.markdown(f"**검색 결과 {len(results)}건**")
    for pid in results:
        info = PLACES[pid]
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{info['name']}**")
                st.caption(" ".join(f"#{kw}" for kw in info["keywords"][:3]))
            with c2:
                if st.button("상세", key=f"s_d_{pid}", use_container_width=True):
                    go_place(pid); st.rerun()
            with c3:
                lbl = "❤️" if pid in st.session_state.liked else "🤍"
                if st.button(lbl, key=f"s_l_{pid}", use_container_width=True):
                    toggle_like(pid); st.rerun()


# ─── 장소 상세 ────────────────────────────────────────────────
def page_detail():
    pid = st.session_state.selected_place
    if pid is None or pid not in PLACES:
        st.warning("장소를 선택해 주세요.")
        return

    info = PLACES[pid]

    if st.button("← 뒤로"):
        st.session_state.selected_place = None
        st.session_state.page = "장소 검색"
        st.rerun()

    st.markdown(f"## 🏷️ {info['name']}")

    # 역할2: 키워드 시스템 → 키워드 가중치 표시
    try:
        kw_weights = get_keyword_weights()  # {kw: float}
    except Exception:
        kw_weights = {}

    kws = info["keywords"]
    kw_cols = st.columns(min(len(kws), 4))
    for i, kw in enumerate(kws):
        with kw_cols[i % len(kw_cols)]:
            w = kw_weights.get(kw)
            label = f"`#{kw}` ({w:.2f})" if w else f"`#{kw}`"
            st.markdown(label)

    col1, col2 = st.columns(2)
    with col1:
        lbl = "❤️ 좋아요 취소" if pid in st.session_state.liked else "🤍 좋아요"
        if st.button(lbl, use_container_width=True):
            toggle_like(pid); st.rerun()
    with col2:
        st.markdown(f"📍 위도 {info['lat']}, 경도 {info['lng']}")

    st.markdown("---")

    # 역할3: RWR 유사 장소 추천
    st.markdown("### 📍 비슷한 장소 (RWR 기반)")
    if PERS_AVAILABLE:
        try:
            recs = rwr_recommend(
                user_keywords=kws[:2],
                liked_places=[pid],
                top_k=3,
            )
            sim_cols = st.columns(len(recs)) if recs else []
            for i, r in enumerate(recs):
                with sim_cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{r['place_name']}**")
                        st.caption(r.get("reason", ""))
                        if st.button("보기", key=f"sim_{pid}_{r['place_id']}", use_container_width=True):
                            go_place(r["place_id"]); st.rerun()
        except Exception as e:
            st.caption(f"RWR 추천 오류: {e}")
    else:
        st.caption(f"personalization 모듈 로드 실패: {_PERS_ERROR}")


# ─── 개인화 추천 ──────────────────────────────────────────────
def page_personal():
    from collections import Counter

    st.markdown("## ✨ 당신을 위한 추천")
    uid = st.session_state.current_user
    liked = st.session_state.liked

    # ── 키워드 검색 입력 ──────────────────────────────────────
    all_kws_pool = sorted({kw for kws in KW_MAP.values() for kw in kws})

    # 좋아요한 장소에서 자동 추출한 키워드를 기본값으로
    auto_kws = []
    for pid in liked:
        auto_kws.extend(KW_MAP.get(pid, []))
    default_kws = [kw for kw, _ in Counter(auto_kws).most_common(3)]

    st.markdown("### 🔍 관심 키워드 선택")
    selected_kws = st.multiselect(
        "키워드를 선택하거나 직접 추가하세요 (좋아요 장소에서 자동 추출됨)",
        options=all_kws_pool,
        default=[kw for kw in default_kws if kw in all_kws_pool],
        label_visibility="collapsed",
    )

    if st.button("✨ 추천 받기", use_container_width=True, type="primary"):
        st.session_state["pers_kws"] = selected_kws
        st.session_state["pers_result"] = None  # 재계산 트리거

    # 추천 실행
    kws_to_use = st.session_state.get("pers_kws", default_kws)

    if not kws_to_use:
        st.info("키워드를 1개 이상 선택하고 '추천 받기'를 눌러주세요.")
        return

    # ── CF 실행 ───────────────────────────────────────────────
    cf_score_map = {}   # {place_id: cf_score}
    cf_reason_map = {}  # {place_id: reason}
    try:
        cf_results = recommend_places_cf_with_scores(uid, top_k=10)
        for r in cf_results:
            cf_score_map[r["place_id"]] = r["score"]
            cf_reason_map[r["place_id"]] = r["reason"]
    except Exception:
        pass

    # ── RWR 실행 ──────────────────────────────────────────────
    rwr_results = []
    rwr_error = None
    if PERS_AVAILABLE:
        try:
            rwr_results = rwr_recommend(
                user_keywords=kws_to_use,
                liked_places=liked,
                cf_places=list(cf_score_map.keys()),
                top_k=10,
            )
        except Exception as e:
            rwr_error = str(e)

    # ── 점수 합산 (CF + RWR 정규화 후 0.4:0.6 가중합) ─────────
    # RWR 점수 정규화
    rwr_score_map = {}
    if rwr_results:
        max_rwr = max(r["score"] for r in rwr_results) or 1
        for r in rwr_results:
            rwr_score_map[r["place_id"]] = r["score"] / max_rwr

    # CF 점수 정규화
    if cf_score_map:
        max_cf = max(cf_score_map.values()) or 1
        cf_score_map = {pid: s / max_cf for pid, s in cf_score_map.items()}

    all_pids = set(rwr_score_map) | set(cf_score_map)
    combined = []
    rwr_map = {r["place_id"]: r for r in rwr_results}

    for pid in all_pids:
        if pid in liked:
            continue
        rwr_s = rwr_score_map.get(pid, 0)
        cf_s  = cf_score_map.get(pid, 0)
        total = rwr_s * 0.6 + cf_s * 0.4

        # 추천 이유 조합
        reasons = []
        if pid in rwr_map:
            reasons.append(rwr_map[pid].get("reason", ""))
        if pid in cf_reason_map:
            reasons.append("비슷한 취향 사용자 선호")
        reason_str = " | ".join(r for r in reasons if r)

        # 출처 태그
        tags = []
        if pid in rwr_score_map: tags.append("RWR")
        if pid in cf_score_map:  tags.append("CF")

        combined.append({
            "place_id": pid,
            "place_name": PLACES.get(pid, {}).get("name", f"장소{pid}"),
            "score": total,
            "reason": reason_str,
            "tags": tags,
            "matched_keywords": rwr_map.get(pid, {}).get("matched_keywords", []),
        })

    combined.sort(key=lambda x: x["score"], reverse=True)
    combined = combined[:8]

    # ── 추천 이유 요약 ────────────────────────────────────────
    st.markdown("---")
    with st.expander("📖 추천 근거 보기"):
        st.markdown(f"**선택 키워드:** {' · '.join(kws_to_use)}")
        if liked:
            st.markdown(f"**좋아요한 장소:** {', '.join(place_name(p) for p in liked)}")
        st.markdown("**알고리즘:** CF(협업 필터링) 0.4 + RWR(키워드 그래프) 0.6 가중합")

    # ── 오류 표시 ─────────────────────────────────────────────
    if rwr_error:
        st.warning(f"RWR 오류 (CF 결과만 표시): {rwr_error}")

    # ── 결과 출력 ─────────────────────────────────────────────
    st.markdown(f"### 추천 장소 ({len(combined)}개)")

    if not combined:
        st.info("추천 결과가 없습니다. 키워드를 바꾸거나 좋아요를 더 눌러보세요.")
        return

    for i, r in enumerate(combined, 1):
        pid = r["place_id"]
        info = PLACES.get(pid, {})
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                tag_str = " ".join(f"`{t}`" for t in r["tags"])
                st.markdown(f"**{i}. {r['place_name']}** {tag_str}")
                kws = r.get("matched_keywords")
                if kws:
                    st.caption(f"매칭 키워드: {', '.join(kws)}")
                if r["reason"]:
                    st.caption(r["reason"])
                st.progress(min(r["score"], 1.0), text=f"점수 {r['score']:.3f}")
            with c2:
                if st.button("상세", key=f"ps_d_{i}_{pid}", use_container_width=True):
                    go_place(pid); st.rerun()
            with c3:
                lbl = "❤️" if pid in st.session_state.liked else "🤍"
                if st.button(lbl, key=f"ps_l_{i}_{pid}", use_container_width=True):
                    toggle_like(pid); st.rerun()


# ─── 경로 추천 ────────────────────────────────────────────────
def page_route():
    st.markdown("## 🗺️ 경로 추천 (역할4 Dijkstra)")
    place_ids   = list(PLACES.keys())
    place_names = [PLACES[p]["name"] for p in place_ids]

    col1, col2 = st.columns(2)
    with col1:
        start_name = st.selectbox("🚩 출발지", place_names)
        start_id   = place_ids[place_names.index(start_name)]
    with col2:
        method = st.selectbox("알고리즘", ["dijkstra", "floyd"])

    # 경유지: 개인화 추천 결과 or 좋아요한 장소
    liked = st.session_state.liked
    default_stops = [p for p in liked if p != start_id][:4]

    all_names = [PLACES[p]["name"] for p in place_ids]
    selected_stops_names = st.multiselect(
        "📍 방문할 장소 선택 (경유지)",
        options=all_names,
        default=[PLACES[p]["name"] for p in default_stops if p in PLACES],
    )
    selected_stops = [place_ids[place_names.index(n)] for n in selected_stops_names if n in place_names]

    if st.button("🔍 경로 최적화", use_container_width=True):
        if not selected_stops:
            st.warning("경유지를 1개 이상 선택하세요.")
        else:
            with st.spinner("Dijkstra/Floyd로 최적 경로 계산 중..."):
                try:
                    result = optimize_travel_route(
                        start_place_id=start_id,
                        recommended_place_ids=selected_stops,
                        places_file=os.path.join(ROOT, "data", "places.json"),
                        method=method,
                    )
                    st.session_state.last_route = result
                except Exception as e:
                    st.error(f"경로 최적화 오류: {e}")

    if st.session_state.last_route:
        result = st.session_state.last_route
        st.markdown("---")
        st.markdown(f"### 📍 최적화된 여행 코스 ({result['algorithm']})")

        route_ids   = result["optimized_route_ids"]
        route_names = result["optimized_route_names"]

        # ── 지도 표시 ─────────────────────────────────────────
        try:
            import folium
            from streamlit_folium import st_folium

            coords = [(PLACES[pid]["lat"], PLACES[pid]["lng"]) for pid in route_ids if pid in PLACES]

            if coords:
                center_lat = sum(c[0] for c in coords) / len(coords)
                center_lng = sum(c[1] for c in coords) / len(coords)
                m = folium.Map(location=[center_lat, center_lng], zoom_start=13, tiles="CartoDB positron")

                # 경로 선
                folium.PolyLine(coords, color="#E74C3C", weight=4, opacity=0.8).add_to(m)

                # 마커
                for i, (pid, name, (lat, lng)) in enumerate(zip(route_ids, route_names, coords)):
                    icon_color = "red" if i == 0 else ("darkblue" if i == len(coords)-1 else "blue")
                    label = f"{'🚩 출발: ' if i==0 else ('🏁 도착: ' if i==len(coords)-1 else f'{i}. ')}{name}"
                    folium.Marker(
                        location=[lat, lng],
                        popup=folium.Popup(label, max_width=200),
                        tooltip=label,
                        icon=folium.Icon(color=icon_color, icon="map-marker"),
                    ).add_to(m)

                    # 순서 번호 원형 표시
                    folium.Marker(
                        location=[lat, lng],
                        icon=folium.DivIcon(
                            html=f'''<div style="
                                background:#E74C3C;color:white;border-radius:50%;
                                width:24px;height:24px;line-height:24px;
                                text-align:center;font-weight:bold;font-size:13px;
                                border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.4);
                                margin-top:-30px;margin-left:8px;">
                                {i+1}</div>''',
                            icon_size=(24, 24),
                        ),
                    ).add_to(m)

                st_folium(m, use_container_width=True, height=420, returned_objects=[])
        except ImportError:
            st.info("지도 표시를 위해 `pip install folium streamlit-folium` 을 실행해 주세요.")
        except Exception as e:
            st.warning(f"지도 로딩 오류: {e}")

        # ── 경로 텍스트 ───────────────────────────────────────
        st.markdown("　→　".join(f"**{n}**" for n in route_names))

        col1, col2, col3 = st.columns(3)
        col1.metric("최적 거리", f"{result['optimized_distance_km']}km")
        col2.metric("기존 순서 거리", f"{result['original_distance_km']}km")
        col3.metric("개선율", f"{result['improvement_rate_percent']}%")

        st.markdown("**구간별 이동 거리**")
        for seg in result["segments"]:
            st.caption(f"{seg['from_place_name']} → {seg['to_place_name']}: {seg['distance_km']}km")

        st.markdown(f"**코스 유형:** {result['course_type']}")

        if st.button("💾 경로 저장"):
            uid = st.session_state.current_user
            user_routes = st.session_state.saved_routes.setdefault(uid, [])
            user_routes.append({
                "name": f"경로{len(user_routes)+1}",
                "stops": result["optimized_route_ids"],
                "names": route_names,
                "distance": result["optimized_distance_km"],
                "liked": False,
            })
            st.success("저장되었습니다!")


# ─── 좋아요한 장소 ────────────────────────────────────────────
def page_liked():
    st.markdown("## ❤️ 내가 좋아요한 장소")
    liked = st.session_state.liked

    if not liked:
        st.info("아직 좋아요한 장소가 없습니다.")
        return

    st.caption(f"총 {len(liked)}곳 | CF·RWR 추천에 활용됩니다.")
    for pid in list(liked):
        info = PLACES.get(pid, {})
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{info.get('name', pid)}**")
                st.caption(" ".join(f"#{kw}" for kw in KW_MAP.get(pid, [])[:3]))
            with c2:
                if st.button("상세", key=f"lk_d_{pid}", use_container_width=True):
                    go_place(pid); st.rerun()
            with c3:
                if st.button("❌", key=f"lk_r_{pid}", use_container_width=True):
                    toggle_like(pid); st.rerun()


# ─── 저장한 경로 ──────────────────────────────────────────────
def page_saved():
    st.markdown("## 📍 저장한 경로")
    uid = st.session_state.current_user
    routes = st.session_state.saved_routes.setdefault(uid, [])

    if not routes:
        st.info("저장된 경로가 없습니다. 경로 추천에서 경로를 저장해 보세요!")
        return

    liked_count = sum(1 for r in routes if r.get("liked"))
    st.caption(f"총 {len(routes)}개 저장 | ❤️ {liked_count}개 좋아요")

    # 탭: 전체 / 좋아요만
    tab1, tab2 = st.tabs(["전체 경로", "❤️ 좋아요한 경로"])

    def render_routes(route_list, prefix):
        for i, route in enumerate(route_list):
            idx = routes.index(route)
            names = route.get("names") or [place_name(p) for p in route["stops"]]
            is_liked = route.get("liked", False)
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{route['name']}**")
                    st.markdown(" → ".join(names))
                    if "distance" in route:
                        st.caption(f"총 거리: {route['distance']}km")
                with c2:
                    lbl = "❤️" if is_liked else "🤍"
                    if st.button(lbl, key=f"{prefix}_like_{idx}", use_container_width=True):
                        routes[idx]["liked"] = not is_liked
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"{prefix}_del_{idx}", use_container_width=True):
                        routes.pop(idx)
                        st.rerun()

    with tab1:
        render_routes(routes, "all")

    with tab2:
        liked_routes = [r for r in routes if r.get("liked")]
        if not liked_routes:
            st.info("좋아요한 경로가 없습니다. 🤍 버튼을 눌러 경로를 저장해 보세요.")
        else:
            render_routes(liked_routes, "fav")


# ─── 라우팅 ───────────────────────────────────────────────────
pg = st.session_state.page
if pg == "홈":               page_home()
elif pg == "장소 검색":      page_search()
elif pg == "장소 상세":      page_detail()
elif pg == "개인화 추천":    page_personal()
elif pg == "경로 추천":      page_route()
elif pg == "좋아요한 장소":  page_liked()
elif pg == "저장한 경로":    page_saved()
