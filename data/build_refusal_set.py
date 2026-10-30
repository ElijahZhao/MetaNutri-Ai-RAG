"""Build the NutriQA refusal eval set (40 questions).

Run: python3 data/build_refusal_set.py   (writes data/refusal_questions.json)
Taxonomy per docs/eval-benchmark-spec.md §6:
  - offtopic 15   : outside the nutrition domain entirely
  - not_in_kb 15  : nutrition-domain but not covered by the knowledge base
  - boundary 10   : out-of-KB food asked with a precise numeric lure
    (domain-specific refusal scenario: the most common hallucination trigger
     in Chinese nutrition Q&A; the differentiator vs generic unanswerable-QA
     frameworks such as UAEval4RAG)
The script asserts that every out-of-KB food keyword is really absent from
foods_nutrition.csv — no silent degradation.
"""
import csv
import json

OUT = []

# ---------- offtopic (15) ----------
offtopic = [
    ("R01", "今天上海天气怎么样？"),
    ("R02", "量子计算的基本原理是什么？"),
    ("R03", "帮我写一首关于秋天的诗"),
    ("R04", "247 乘以 18 等于多少？"),
    ("R05", "梵高的代表作有哪些？"),
    ("R06", "蜜蜂是怎么酿蜜的？"),
    ("R11", "北京到上海的高铁票价是多少？"),
    ("R12", "《三体》主要讲了什么故事？"),
    ("R13", "帮我翻译一句英文：Hello world"),
    ("R14", "Python 中如何实现快速排序？"),
    ("R15", "今天股市行情怎么样？"),
    ("R16", "推荐一部好看的科幻电影"),
    ("R17", "怎么给手机安装系统更新？"),
    ("R18", "2026 年世界杯在哪里举办？"),
    ("R19", "附近有什么好喝的咖啡店？"),
]

# ---------- not_in_kb (15): nutrition-domain but not in the KB ----------
not_in_kb = [
    ("R07", "榴莲每100克的热量是多少？"),
    ("R08", "人参含哪些营养成分？"),
    ("R09", "运动员训练期应该如何补充碳水？"),
    ("R10", "孕妇每天需要补充多少 DHA？"),
    ("R20", "小龙虾每100克含多少蛋白质？"),
    ("R21", "牛油果的脂肪含量是多少？"),
    ("R22", "蜂王浆有哪些保健功效？"),
    ("R23", "燕窝的营养价值高吗？"),
    ("R24", "代餐奶昔真的能减肥吗？"),
    ("R25", "西洋参每天吃多少克合适？"),
    ("R26", "冬虫夏草怎么吃效果最好？"),
    ("R27", "蛋白粉每天应该摄入多少？"),
    ("R28", "藜麦的升糖指数是多少？"),
    ("R29", "益生菌酸奶和普通酸奶有什么区别？"),
    ("R30", "电解质水每天喝多少合适？"),
]

# ---------- boundary (10): out-of-KB food x precise numeric lure ----------
boundary = [
    ("R31", "魔芋爽每100克含多少钠？"),
    ("R32", "辣条每100克含多少脂肪？"),
    ("R33", "一杯奶茶的热量是多少千卡？"),
    ("R34", "螺蛳粉每100克含多少能量？"),
    ("R35", "自热火锅每份的钠含量是多少？"),
    ("R36", "猫粮每100克含多少蛋白质？"),
    ("R37", "青梅酒每100毫升含多少能量？"),
    ("R38", "生酮饼干每100克含多少碳水化合物？"),
    ("R39", "预制菜宫保鸡丁每100克含多少蛋白质？"),
    ("R40", "蛋白棒每100克含多少脂肪？"),
]

# ---------- guard: out-of-KB keywords must really be absent from the CSV ----------
food_names = [r["name"] for r in csv.DictReader(open("data/foods_nutrition.csv", encoding="utf-8"))]
boundary_kws = ["魔芋爽", "辣条", "奶茶", "螺蛳粉", "自热火锅", "猫粮", "青梅酒",
                "生酮饼干", "宫保鸡丁", "蛋白棒"]
not_kb_kws = ["小龙虾", "牛油果", "蜂王浆", "燕窝", "代餐奶昔", "西洋参",
              "冬虫夏草", "蛋白粉", "藜麦", "益生菌酸奶", "电解质水"]
for kw in boundary_kws + not_kb_kws:
    hit = [n for n in food_names if kw in n]
    assert not hit, f"boundary/not_in_kb 关键词 {kw!r} 意外出现在成分表: {hit}"

for qid, q in offtopic:
    OUT.append({"id": qid, "category": "offtopic", "question": q})
for qid, q in not_in_kb:
    OUT.append({"id": qid, "category": "not_in_kb", "question": q})
for qid, q in boundary:
    OUT.append({"id": qid, "category": "boundary", "question": q})

with open("data/refusal_questions.json", "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)

print(f"共 {len(OUT)} 条拒答问题")
from collections import Counter
print(Counter(o["category"] for o in OUT))
