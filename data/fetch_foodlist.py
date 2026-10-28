"""Fetch full food list from 中国疾病预防控制中心营养与健康所 食物营养成分查询平台.

Source: https://nlc.chinanutri.cn/fq/ (official)
Endpoint: POST /fq/FoodInfoQueryAction!queryFoodInfoList.do
Output: data/foods_all_list.csv (food_id, name, category_id)

Reproducible script; record source in SOURCES.md.
"""
import csv
import json
import time
import urllib.request
import urllib.parse

BASE = "https://nlc.chinanutri.cn/fq/"
LIST_URL = BASE + "FoodInfoQueryAction!queryFoodInfoList.do"
CATEGORIES = list(range(1, 30))  # probe 1..29; empty ones are skipped


def fetch_page(category: int, page_num: int) -> dict:
    data = urllib.parse.urlencode({
        "categoryOne": category, "categoryTwo": "0", "foodName": "",
        "pageNum": page_num, "field": "0", "flag": "0",
    }).encode()
    req = urllib.request.Request(LIST_URL, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    })
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception:
            time.sleep(1.0)
    return {}


def main():
    rows = []
    for cat in CATEGORIES:
        page = 1
        got = 0
        while True:
            d = fetch_page(cat, page)
            items = d.get("list") or []
            if not items:
                break
            for it in items:
                rows.append([it[0], it[2], cat])
            got += len(items)
            total = int(d.get("totalPages") or 0)
            if page >= total:
                break
            page += 1
            time.sleep(0.2)
        if got:
            print(f"category={cat}: {got} items")
        time.sleep(0.3)

    # dedup by food_id (some foods may appear under multiple categories)
    seen, out = set(), []
    for food_id, name, cat in rows:
        if food_id in seen:
            continue
        seen.add(food_id)
        out.append([food_id, name, cat])

    with open("data/foods_all_list.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["food_id", "name", "category_id"])
        w.writerows(out)
    print(f"TOTAL unique foods: {len(out)}")


if __name__ == "__main__":
    main()
