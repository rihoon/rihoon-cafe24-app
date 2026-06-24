# -*- coding: utf-8 -*-
"""리훈 카페24 배너 관리 — Streamlit Cloud 배포판.

GitHub API로만 동작한다. 배너 이미지는 GitHub Pages(rihoon-sov/docs/banners/)에 호스팅하고,
JSON(main-banners.json / category-banners.json)을 갱신하면 자사몰(skin41)이 그 JSON을 fetch해서
표시한다. → 클라우드에 cafe24 토큰이 전혀 필요 없다.

필요한 secret: GITHUB_TOKEN (rihoon-sov repo Contents 읽기/쓰기 권한).
"""
import io
import json
import base64
import requests
import streamlit as st
from PIL import Image

REPO = "rihoon/rihoon-sov"
BRANCH = "master"
PAGES = "https://rihoon.github.io/rihoon-sov"
GH = "https://api.github.com"

st.set_page_config(page_title="리훈 카페24 관리", page_icon="🛍️", layout="centered")

# ──────────────────────── 디자인 (리훈 무채색 라이트) ────────────────────────
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
html, body, .stApp, [class*="css"]{font-family:'Pretendard',-apple-system,BlinkMacSystemFont,sans-serif;}
.stApp{background:#faf9f7;}
header[data-testid="stHeader"]{display:none;}
footer{display:none;}
#MainMenu{display:none;}
.block-container{max-width:780px;padding-top:1.4rem;padding-bottom:5rem;}
section[data-testid="stSidebar"]{background:#f2f1ee;border-right:1px solid #e7e5e1;}

.rh-head{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid #e7e5e1;padding:6px 2px 18px;margin-bottom:22px;}
.rh-logo{font-size:26px;font-weight:800;letter-spacing:-.02em;color:#1a1a1a;}
.rh-sub{font-size:14px;color:#8a8783;font-weight:500;}
.rh-desc{font-size:13.5px;color:#8a8783;line-height:1.6;margin:-10px 2px 22px;}

[data-testid="stExpander"]{border:1px solid #e7e5e1;border-radius:14px;background:#fff;
  margin-bottom:9px;box-shadow:0 1px 2px rgba(0,0,0,.03);overflow:hidden;}
[data-testid="stExpander"] summary{padding:13px 18px;font-size:14.5px;font-weight:600;color:#1a1a1a;}
[data-testid="stExpander"] summary:hover{background:#f4f3f0;}
[data-testid="stImage"] img{border-radius:10px;}
[data-testid="stFileUploader"] section{border:1.5px dashed #d6d3cd;border-radius:10px;background:#faf9f7;}
.stTextInput input,.stTextArea textarea{border-radius:9px;border:1px solid #e7e5e1;}
.stButton button[kind="primary"]{background:#1a1a1a;color:#fff;border:none;border-radius:11px;
  padding:.75rem 1.2rem;font-weight:700;font-size:15px;transition:.15s;}
.stButton button[kind="primary"]:hover{background:#333;transform:translateY(-1px);}
[data-testid="stAlert"]{border-radius:11px;}
hr{margin:1.2rem 0;border-color:#e7e5e1;}
</style>
""", unsafe_allow_html=True)


# ──────────────────────── GitHub API ────────────────────────
def _token():
    t = st.secrets.get("GITHUB_TOKEN", "")
    if not t:
        st.error("GITHUB_TOKEN secret이 없습니다. 우측 하단 Manage app → Settings → Secrets 에 등록하세요.")
        st.stop()
    return t


def _h():
    return {"Authorization": f"token {_token()}", "Accept": "application/vnd.github+json"}


def gh_get(path):
    r = requests.get(f"{GH}/repos/{REPO}/contents/{path}", headers=_h(),
                     params={"ref": BRANCH}, timeout=30)
    return r.json() if r.status_code == 200 else None


def gh_get_json(path, default):
    j = gh_get(path)
    if not j:
        return default, None
    try:
        return json.loads(base64.b64decode(j["content"])), j.get("sha")
    except Exception:
        return default, j.get("sha")


def gh_put(path, content_bytes, message, sha=None):
    data = {"message": message, "branch": BRANCH,
            "content": base64.b64encode(content_bytes).decode()}
    if sha:
        data["sha"] = sha
    r = requests.put(f"{GH}/repos/{REPO}/contents/{path}", headers=_h(), json=data, timeout=60)
    return r.status_code in (200, 201), r.json()


def commit_image(raw, path, msg):
    """이미지 bytes를 jpg로 변환해 커밋, GitHub Pages URL(캐시버스터 포함) 반환."""
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    ex = gh_get(path)
    ok, resp = gh_put(path, buf.getvalue(), msg, ex["sha"] if ex else None)
    if not ok:
        raise RuntimeError(resp.get("message", "업로드 실패"))
    v = resp["content"]["sha"][:8]
    return f"{PAGES}/{path.replace('docs/', '')}?v={v}"


@st.cache_data(ttl=60)
def load_categories():
    cats, _ = gh_get_json("docs/categories.json", [])
    return cats


# ════════════════════════ 메인 배너 페이지 ════════════════════════
def page_main():
    st.markdown('<div class="rh-head"><span class="rh-logo">rihoon</span>'
                '<span class="rh-sub">메인 배너 (홈 히어로)</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="rh-desc">홈 첫 화면의 큰 슬라이드 배너입니다. 이미지·문구·링크·글자색을 바꾸고 '
                '<b>저장 & 반영</b>을 누르면 1~2분 뒤 홈에 자동 반영됩니다. (가로로 넓은 이미지 권장)</div>',
                unsafe_allow_html=True)

    banners, _ = gh_get_json("docs/main-banners.json", [])
    if "mb_n" not in st.session_state:
        st.session_state.mb_n = max(1, len(banners))

    n = st.session_state.mb_n
    for i in range(n):
        b = banners[i] if i < len(banners) else {}
        title_show = b.get("title", f"새 배너")
        with st.expander(f"배너 {i + 1} — {title_show}", expanded=(i == 0)):
            if b.get("image"):
                st.image(b["image"], use_container_width=True)
            st.file_uploader("이미지 교체", type=["jpg", "jpeg", "png"], key=f"mb_img_{i}")
            st.text_input("큰 글씨 1줄", value=b.get("head", ""), key=f"mb_head_{i}")
            st.text_input("큰 글씨 2줄", value=b.get("title", ""), key=f"mb_title_{i}")
            st.text_input("작은 글씨", value=b.get("sub", ""), key=f"mb_sub_{i}")
            st.text_input("클릭 시 이동 링크", value=b.get("link", ""), key=f"mb_link_{i}")
            c1, c2 = st.columns(2)
            c1.radio("글자색", ["검정", "흰색"], index=(1 if b.get("light") else 0),
                     key=f"mb_color_{i}", horizontal=True)
            c2.slider("배경 어둡게(%)", 0, 70, int(b.get("dim", 0)), key=f"mb_dim_{i}")

    cc1, cc2 = st.columns(2)
    if cc1.button("➕ 배너 추가", use_container_width=True):
        st.session_state.mb_n += 1
        st.rerun()
    if cc2.button("➖ 마지막 배너 삭제", use_container_width=True) and st.session_state.mb_n > 1:
        st.session_state.mb_n -= 1
        st.rerun()

    st.markdown("---")
    if st.button("💾  저장 & 반영", type="primary", use_container_width=True):
        try:
            with st.spinner("게시 중…"):
                out = []
                for i in range(st.session_state.mb_n):
                    b = banners[i] if i < len(banners) else {}
                    up = st.session_state.get(f"mb_img_{i}")
                    img_url = b.get("image", "")
                    if up is not None:
                        img_url = commit_image(up.getvalue(), f"docs/banners/main-{i}.jpg", f"메인배너 이미지 {i}")
                    slide = {
                        "image": img_url,
                        "head": st.session_state.get(f"mb_head_{i}", ""),
                        "title": st.session_state.get(f"mb_title_{i}", ""),
                        "sub": st.session_state.get(f"mb_sub_{i}", ""),
                        "link": st.session_state.get(f"mb_link_{i}", ""),
                        "light": st.session_state.get(f"mb_color_{i}") == "흰색",
                        "dim": st.session_state.get(f"mb_dim_{i}", 0),
                    }
                    out.append(slide)
                _, sha = gh_get_json("docs/main-banners.json", [])
                ok, resp = gh_put("docs/main-banners.json",
                                  (json.dumps(out, ensure_ascii=False, indent=1) + "\n").encode(),
                                  "메인 배너 갱신", sha)
            if ok:
                st.success("✅ 게시 완료! 1~2분 뒤 홈에 자동 반영됩니다.")
                st.balloons()
            else:
                st.error(f"실패: {resp.get('message')}")
        except Exception as e:
            st.error(f"오류: {e}")


# ════════════════════════ 카테고리·라이브 배너 페이지 ════════════════════════
def page_category():
    st.markdown('<div class="rh-head"><span class="rh-logo">rihoon</span>'
                '<span class="rh-sub">카테고리 · 라이브 배너</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="rh-desc">카테고리·라이브 페이지 상단 배너입니다. 이미지를 올리고 <b>저장 & 반영</b>을 '
                '누르면 1~2분 뒤 자사몰에 자동 반영됩니다. (가로로 넓은 이미지 권장)</div>',
                unsafe_allow_html=True)

    cats = load_categories()
    banners, _ = gh_get_json("docs/category-banners.json", {})

    rows = [{"key": "live", "name": "🔴 라이브 방송 페이지"}]
    for c in cats:
        rows.append({"key": str(c["no"]), "name": "　" * (int(c.get("depth", 1)) - 1) + c["name"]})

    if "pending" not in st.session_state:
        st.session_state.pending = {}

    done = sum(1 for r in rows if banners.get(r["key"], {}).get("image"))
    st.caption(f"배너 등록됨 {done} · 전체 {len(rows)}")

    for row in rows:
        k, name = row["key"], row["name"]
        cur = banners.get(k, {})
        mark = "🟢" if cur.get("image") else "⚪"
        with st.expander(f"{mark}　{name}"):
            if cur.get("image"):
                st.image(cur["image"], use_container_width=True)
            else:
                st.caption("아직 배너가 없습니다.")
            up = st.file_uploader("배너 이미지 올리기", type=["jpg", "jpeg", "png"], key=f"u_{k}")
            link = st.text_input("클릭 시 이동할 링크 (선택)", value=cur.get("link", ""), key=f"l_{k}")
            if up is not None:
                st.session_state.pending[k] = (up.getvalue(), name, link)
                st.image(up, use_container_width=True, caption="새 이미지 미리보기 — 저장하면 적용")

    st.markdown("---")
    if st.button("💾  저장 & 반영", type="primary", use_container_width=True):
        pend = st.session_state.pending
        if not pend:
            st.warning("새로 올린 이미지가 없습니다.")
        else:
            prog = st.progress(0.0, text="게시 중…")
            banners2, sha2 = gh_get_json("docs/category-banners.json", {})
            items = list(pend.items())
            fail = []
            for i, (k, (raw, name, link)) in enumerate(items):
                try:
                    url = commit_image(raw, f"docs/banners/{k}.jpg", f"배너 이미지 {k}")
                    banners2[k] = {"image": url}
                    if link.strip():
                        banners2[k]["link"] = link.strip()
                except Exception as e:
                    fail.append(f"{name} ({e})")
                prog.progress((i + 1) / len(items), text=f"게시 중… {i + 1}/{len(items)}")
            ok, resp = gh_put("docs/category-banners.json",
                              (json.dumps(banners2, ensure_ascii=False, indent=1) + "\n").encode(),
                              "배너 목록 갱신", sha2)
            if ok and not fail:
                st.success("✅ 게시 완료! 1~2분 뒤 자사몰에 자동 반영됩니다.")
                st.balloons()
                st.session_state.pending = {}
            elif ok:
                st.warning("일부 실패: " + ", ".join(fail))
            else:
                st.error(f"목록 갱신 실패: {resp.get('message')}")


# ──────────────────────── 라우팅 ────────────────────────
st.sidebar.markdown("### 🛍️ 리훈 카페24 관리")
page = st.sidebar.radio("메뉴", ["🖼️ 메인 배너", "🏷️ 카테고리·라이브 배너"])
st.sidebar.caption("배너 업로드 → 저장하면 자동 게시.\n카페24 로그인 필요 없음.")

if page.startswith("🖼️"):
    page_main()
else:
    page_category()
