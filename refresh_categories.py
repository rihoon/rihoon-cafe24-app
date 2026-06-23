# -*- coding: utf-8 -*-
"""카테고리 목록을 cafe24에서 추출해 rihoon-sov/docs/categories.json 으로 저장.
로컬에서만 실행(카테고리가 늘었을 때). 실행 후 rihoon-sov 에서 commit/push.
"""
import sys, os, json
sys.path.insert(0, r"C:/Users/rihoo/projects/rihoon-keywords")
import cafe24

OUT = r"C:/Users/rihoo/projects/rihoon-keywords/docs/categories.json"

r = cafe24.api("GET", "/admin/categories?limit=100", "")
cats = [{"no": int(c["category_no"]), "name": c["category_name"],
         "depth": int(c.get("category_depth", 1))} for c in r.get("categories", [])]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(cats, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(cats)}개 카테고리 → {OUT}")
