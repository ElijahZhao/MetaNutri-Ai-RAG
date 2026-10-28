"""Fetch nutrition details for selected foods from 疾控食物营养成分查询平台.

Input:  data/foods_selected_list.csv (food_id, name, category_id)
Output: data/foods_nutrition.csv  (wide table: food_id, name, category_id, <item>:<value>...)
        data/fetch_errors.log    (failed fetches)
"""
import csv
import re
import time
import urllib.request

BASE = "https://nlc.chinanutri.cn/fq/foodinfo/"
# value pattern: number + unit, or "—" for missing
VAL_RE = re.compile(r"^[0-9.]+\s*(?:%|g|mg|μg|µg|kJ|kcal|IU)?$|^—$|^-$")


def parse_cells(cells):
    """Rows are either 6-cell (type,item,value,...) or 5-cell (item,value,...)
    because the type column uses row-spanning cells."""
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
    if len(cells) < 2:
        return None
    if VAL_RE.match(cells[1] or ""):
        item, val = cells[0], cells[1]
    else:
        item, val = cells[1], cells[2] if len(cells) > 2 else ""
    return item, val


def fetch_detail(food_id: str) -> dict:
    url = BASE + food_id + ".html"
    for attempt in range(2):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                t = r.read().decode("utf-8", "ignore")
            rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", t)
            data = {}
            for r in rows:
                cells = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", r)
                parsed = parse_cells(cells)
                if parsed:
                    item, val = parsed
                    if item and item != "项目" and item not in ("类型", "含量"):
                        data[item] = val
            if data:
                return data
        except Exception:
            time.sleep(0.8)
    return {}


def main():
    foods = []
    with open("data/foods_selected_list.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            foods.append((row["food_id"], row["name"], row["category_id"]))

    results, failed = [], []
    for i, (fid, name, cat) in enumerate(foods):
        d = fetch_detail(fid)
        if d:
            results.append({"food_id": fid, "name": name, "category_id": cat, **d})
        else:
            failed.append((fid, name))
        if (i + 1) % 25 == 0:
            print(f"progress {i+1}/{len(foods)}", flush=True)
        time.sleep(0.15)

    # union of items for columns
    items = ["food_id", "name", "category_id"]
    seen = set(items)
    for r in results:
        for k in r:
            if k not in seen:
                seen.add(k)
                items.append(k)

    with open("data/foods_nutrition.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=items)
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k, "") for k in items})

    with open("data/fetch_errors.log", "w", encoding="utf-8") as f:
        for fid, name in failed:
            f.write(f"{fid}\t{name}\n")

    print(f"DONE: ok={len(results)} failed={len(failed)} columns={len(items)}")


if __name__ == "__main__":
    main()
