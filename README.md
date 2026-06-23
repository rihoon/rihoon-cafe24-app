# 리훈 카페24 배너 관리 (Streamlit Cloud)

자사몰(skin41) **카테고리 / 라이브 페이지 상단 배너**를 직원이 어디서나 업로드·게시하는 웹앱.

## 동작 원리
- 앱이 **GitHub API로만** 동작 (cafe24 토큰 불필요).
- 업로드한 배너 이미지 → `rihoon-sov/docs/banners/{분류번호}.jpg` 커밋 → **GitHub Pages**가 호스팅.
- `docs/category-banners.json` 갱신 → 자사몰 레이아웃/라이브 페이지가 이 JSON을 fetch해서 표시.
- 즉 **재붙여넣기·카페24 로그인 없이** 배너가 자동 반영됨.

## 배포 (한 번만)
1. 이 repo를 GitHub에 푸시.
2. https://share.streamlit.io → **New app** → 이 repo / `streamlit_app.py` 선택 → Deploy.
3. 앱 **Settings → Secrets** 에 아래 한 줄 등록:
   ```
   GITHUB_TOKEN = "github_pat_..."
   ```
   - 토큰: GitHub → Settings → Developer settings → **Fine-grained tokens** →
     Repository access = `rihoon/rihoon-sov`, Permissions = **Contents: Read and write**.
4. 끝. 생성된 `https://....streamlit.app` 주소를 직원에게 공유.

## 카테고리 목록 갱신
카테고리가 늘면 로컬에서 `refresh_categories.py` 실행 → `docs/categories.json` 푸시.
