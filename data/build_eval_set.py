"""Build the 50-question evaluation set with gold answers extracted from real data.

Output: data/eval_questions.json
  [{id, category: composition|guideline|special, question, gold, source_keyword}]
source_keyword is used by evaluation to check retrieval hit (top-k must include a chunk
containing this keyword). Gold answers come from foods_nutrition.csv (real values) or
the official dietary-guideline texts (verbatim sentences) — no fabricated numbers.
"""
import csv
import json
import re

FOODS = list(csv.DictReader(open("data/foods_nutrition.csv", encoding="utf-8")))
GUIDE = open("data/dietary_guidelines_2022.md", encoding="utf-8").read()
G6 = open("data/dietary_guidelines_rule6_detail.md", encoding="utf-8").read()


def food_value(name_kw: str, col: str) -> str:
    for r in FOODS:
        if name_kw in r["name"]:
            v = (r.get(col) or "").strip()
            if v and v not in ("—", "-"):
                return v
    raise ValueError(f"food {name_kw} / {col} not found or empty")


def guide_snippet(kw: str, pool: str = GUIDE, limit: int = 150) -> str:
    pool_n = re.sub(r"\s+", " ", pool)  # normalize all unicode spaces
    kw_n = re.sub(r"\s+", " ", kw)
    m = re.search(r".{0,20}%s.{0,%d}" % (re.escape(kw_n), limit), pool_n)
    if not m:
        raise ValueError(f"guide kw {kw} not found in pool")
    return m.group(0).strip()


# ---------- composition (20): gold = real value from CSV ----------
composition = [
    ("C01", "小米每100克含有多少能量？", "小米", "能量(Energy)"),
    ("C02", "每100克鸡蛋含有多少蛋白质？", "蛋（鸡蛋，均值)", "蛋白质(Protein)"),
    ("C03", "每100克苹果的碳水化合物含量是多少？", "苹果(均值)", "碳水化合物(CHO)"),
    ("C04", "杏仁每100克含多少脂肪？", "杏仁(炒)", "脂肪(Fat)"),
    ("C05", "每100克牛奶的钙含量是多少？", "乳品（牛乳，均值)", "钙(Ca)"),
    ("C06", "菠菜每100克含多少铁？", "菠菜", "铁(Fe)"),
    ("C07", "香蕉每100克含多少钾？", "香蕉[甘蕉]", "钾(K)"),
    ("C08", "橙子每100克含多少维生素C？", "橙", "维生素C(Vitamin C)"),
    ("C09", "猪里脊每100克含多少蛋白质？", "猪肉(里脊)", "蛋白质(Protein)"),
    ("C10", "核桃每100克含多少脂肪？", "核桃(干)", "脂肪(Fat)"),
    ("C11", "豆腐每100克含多少蛋白质？", "豆腐(均值)", "蛋白质(Protein)"),
    ("C12", "鸡肉每100克含多少能量？", "鸡(均值)", "能量(Energy)"),
    ("C13", "带鱼每100克含多少蛋白质？", "带鱼", "蛋白质(Protein)"),
    ("C14", "秋黄瓜每100克含多少水分？", "秋黄瓜", "水分(Water)"),
    ("C15", "红薯每100克含多少能量？", "甘薯(红心)", "能量(Energy)"),
    ("C16", "燕麦片每100克含多少膳食纤维？", "燕麦片", "总膳食纤维(Dietary fiber)"),
    ("C17", "黄豆每100克含多少铁？", "黄豆", "铁(Fe)"),
    ("C18", "西兰花每100克含多少维生素C？", "西兰花", "维生素C(Vitamin C)"),
    ("C19", "豆浆每100克含多少蛋白质？", "豆浆", "蛋白质(Protein)"),
    ("C20", "羊肉每100克含多少能量？", "羊肉(肥瘦)(均值)", "能量(Energy)"),
]

# ---------- guideline (15): gold = verbatim sentence from official text ----------
guideline = [
    ("G01", "成年人每天摄入食盐不超过多少克？", "食盐", GUIDE),
    ("G02", "每天烹调油摄入量建议是多少？", "烹调油", GUIDE),
    ("G03", "添加糖每天摄入量建议控制在多少？", "添加糖", GUIDE),
    ("G04", "每天应摄入多少新鲜蔬菜？", "新鲜蔬菜", GUIDE),
    ("G05", "每天应摄入多少新鲜水果？", "新鲜水果", GUIDE),
    ("G06", "每天谷类食物摄入量建议是多少？", "谷类食物", GUIDE),
    ("G07", "平均每天应摄入多少种食物？", "12种以上", GUIDE),
    ("G08", "奶制品摄入量相当于每天多少毫升液态奶？", "液态奶", GUIDE),
    ("G09", "每周蛋类摄入量建议是多少？", "蛋类300", GUIDE),
    ("G10", "每周最好吃鱼几次或多少克？", "吃鱼2次", GUIDE),
    ("G11", "成年人如饮酒，一天饮用的酒精量不超过多少？", "酒精量", GUIDE),
    ("G12", "成年男性每天喝水多少毫升？", "1700ml", G6),
    ("G13", "成年女性每天喝水多少毫升？", "1500ml", G6),
    ("G14", "每周应进行多少中等强度身体活动？", "中等强度", GUIDE),
    ("G15", "每天主动身体活动最好达到多少步？", "6 000步", GUIDE),
]

# ---------- special / taboo (15): gold = verbatim from official text ----------
special = [
    ("S01", "高血压人群在饮食上应该注意什么？", "食盐不超过5g", GUIDE, "食盐不超过5g"),
    ("S02", "糖尿病患者应该控制什么摄入？", "添加糖", GUIDE, "添加糖"),
    ("S03", "儿童青少年可以饮酒吗？", "儿童青少年", GUIDE, "不应饮酒"),
    ("S04", "孕妇和乳母能饮酒吗？", "孕妇", GUIDE, "不应饮酒"),
    ("S05", "想控制体重的人应该怎么做？", "食不过量", GUIDE, "食不过量"),
    ("S06", "胆固醇偏高的人吃鸡蛋要丢掉蛋黄吗？", "不弃蛋黄", GUIDE, "不弃蛋黄"),
    ("S07", "含糖饮料喝多了有什么健康风险？", "龋齿", G6, "龋齿"),
    ("S08", "如何判断身体是否缺水？", "尿液颜色", G6, "尿液颜色"),
    ("S09", "减重期间晚餐应该怎么安排？", "睡觉前2小时", G6, "睡觉前"),
    ("S10", "在外就餐应该注意什么？", "在外就餐", G6, "在外就餐"),
    ("S11", "吃零食应该注意什么？", "零食", G6, "零食"),
    ("S12", "暴饮暴食会增加什么健康风险？", "暴饮暴食", G6, "超重肥胖"),
    ("S13", "营养充足的早餐应包括哪几类食物？", "早餐的食物应", G6, "谷薯类"),
    ("S14", "反式脂肪酸每天摄入量上限是多少？", "反式脂肪酸", GUIDE, "反式脂肪酸不超过2g"),
    ("S15", "蛋白质摄入不足的人应多吃哪几类食物？", "大豆制品", GUIDE, "大豆制品"),
]

OUT = []

for qid, q, fk, col in composition:
    val = food_value(fk, col)
    OUT.append({"id": qid, "category": "composition", "question": q,
                "gold": f"每100克可食部含{val}", "source_keyword": fk.split("[")[0]})

for qid, q, kw, pool in guideline:
    OUT.append({"id": qid, "category": "guideline", "question": q,
                "gold": guide_snippet(kw, pool), "source_keyword": kw})

for qid, q, kw, pool, gk in special:
    OUT.append({"id": qid, "category": "special", "question": q,
                "gold": guide_snippet(kw, pool), "source_keyword": kw, "gold_key": gk})

with open("data/eval_questions.json", "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)

print(f"共 {len(OUT)} 条评测问题")
from collections import Counter
print(Counter(o["category"] for o in OUT))
for o in OUT:
    print(f"{o['id']} [{o['category']}] {o['question']}\n    gold: {o['gold'][:80]}")
