"""Build knowledge-base texts: one chunk per food + one chunk per guideline rule.

Input:  data/foods_nutrition.csv, data/dietary_guidelines_2022.md, data/dietary_guidelines_rule6_detail.md
Output: data/kb_foods.txt, data/kb_guidelines.txt, data/SOURCES.md
"""
import csv
import re
from collections import OrderedDict

CAT_NAMES = {1:"谷类",10:"薯类",11:"干豆",12:"蔬菜",13:"菌藻",14:"水果",15:"坚果",16:"畜肉",17:"禽肉",18:"乳类",19:"蛋类",20:"鱼虾蟹贝",21:"婴幼儿食品",22:"小吃甜饼",23:"速食",24:"饮料",25:"含酒精饮料",26:"糖果蜜饯蜂蜜",27:"油脂",28:"调味品",29:"其它"}

# official column -> readable Chinese label (order matters for display)
LABELS = OrderedDict([
    ("能量(Energy)", "能量"), ("蛋白质(Protein)", "蛋白质"), ("脂肪(Fat)", "脂肪"),
    ("碳水化合物(CHO)", "碳水化合物"), ("总膳食纤维(Dietary fiber)", "膳食纤维"),
    ("胆固醇(Cholesterol)", "胆固醇"), ("灰分(Ash)", "灰分"), ("水分(Water)", "水分"),
    ("胡萝卜素(Carotene)", "胡萝卜素"), ("维生素A(Vitamin)", "维生素A"),
    ("α-TE", "维生素E(α-TE)"), ("硫胺素(Thiamin)", "硫胺素(维生素B1)"),
    ("核黄素(Riboflavin)", "核黄素(维生素B2)"), ("烟酸(Niacin)", "烟酸"),
    ("维生素C(Vitamin C)", "维生素C"), ("钙(Ca)", "钙"), ("磷(P)", "磷"),
    ("钾(K)", "钾"), ("钠(Na)", "钠"), ("镁(Mg)", "镁"), ("铁(Fe)", "铁"),
    ("锌(Zn)", "锌"), ("硒(Se)", "硒"), ("铜(Cu)", "铜"), ("锰(Mn)", "锰"),
    ("碘(I)", "碘"), ("饱和脂肪酸(SFA)", "饱和脂肪酸"),
    ("单不饱和脂肪酸(MUFA)", "单不饱和脂肪酸"), ("多不饱和脂肪酸(PUFA)", "多不饱和脂肪酸"),
])


def fmt_food(row):
    parts = []
    for col, label in LABELS.items():
        v = (row.get(col) or "").strip()
        if v and v not in ("—", "-"):
            parts.append(f"{label}{v}")
    cat = CAT_NAMES.get(int(row["category_id"]), "其它")
    return (f"【食物：{row['name']}｜分类：{cat}】\n"
            f"每100克可食部：{'，'.join(parts) if parts else '（该条目各营养成分均未收录）'}。\n"
            "（数据来源：中国疾病预防控制中心营养与健康所·食物营养成分查询平台）\n")


def chunk_guidelines():
    chunks = []
    md = open("data/dietary_guidelines_2022.md", encoding="utf-8").read()
    # split per 准则N
    segs = re.split(r"(准则[一二三四五六七八]\s*[^ \n]+)", md)
    for i in range(1, len(segs), 2):
        title = segs[i].strip()
        body = segs[i + 1].strip() if i + 1 < len(segs) else ""
        if not body:
            continue
        chunks.append(f"【膳食指南·{title}】\n{body}\n（来源：中国营养学会《中国居民膳食指南（2022）》平衡膳食八准则）\n")
    # rule-6 detail: one chunk per topical section (（一）-（八）)
    d6 = open("data/dietary_guidelines_rule6_detail.md", encoding="utf-8").read()
    d6 = re.sub(r"^#.*$", "", d6, flags=re.M).strip()
    marks = list(re.finditer(r"（[一二三四五六七八]）", d6))
    intro = d6[:marks[0].start()].strip()
    for i, m in enumerate(marks):
        start = m.start()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(d6)
        sec = d6[start:end].strip()
        title = re.match(r"（[一二三四五六七八]）[^\n]{0,42}", sec).group(0).rstrip()
        chunks.append(f"【膳食指南·准则六 详细实践：{title}】\n{sec}\n（来源：中国营养学会《中国居民膳食指南（2022）》，官网实践应用部分）\n")
    if intro:
        chunks.append(f"【膳食指南·准则六 详细实践（概述）】\n{intro}\n（来源：中国营养学会《中国居民膳食指南（2022）》，官网实践应用部分）\n")
    return chunks


def main():
    foods = []
    with open("data/foods_nutrition.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            foods.append(row)

    with open("data/kb_foods.txt", "w", encoding="utf-8") as f:
        for row in foods:
            f.write(fmt_food(row) + "\n")

    g = chunk_guidelines()
    with open("data/kb_guidelines.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(g))

    n_food_items = 0
    for row in foods:
        parts = [c for c, l in LABELS.items() if (row.get(c) or "").strip() not in ("", "—", "-")]
        n_food_items += len(parts)

    with open("data/SOURCES.md", "w", encoding="utf-8") as f:
        f.write("""# 数据来源登记（nutri-rag）

## 1. 食物营养成分数据
- 来源：中国疾病预防控制中心营养与健康所「食物营养成分查询平台」
- 网址：https://nlc.chinanutri.cn/fq/
- 数据版本：平台现行版（2026-10-28 抓取）
- 内容：307 条常见食物，每食物 32 项营养成分（能量/蛋白质/脂肪/碳水/维生素/矿物质/脂肪酸等），单位 g/mg/μg/kJ
- 抓取方式：`data/fetch_foodlist.py`（全量清单 1356 条）→ `data/fetch_foods_selected.py`（精选 307 条）→ `data/fetch_food_details.py`（详情）
- 缺失说明：部分营养项平台本身未收录（如膳食纤维 282/307 缺失、维生素E 287/307 缺失、碘 281/307 缺失），切片中该字段不列出；问答时对缺失项按"数据源未收录"处理，不估算

## 2. 膳食指南
- 来源：中国营养学会·中国居民膳食指南官网
- 网址：http://dg.cnsoc.org/
- 内容：《中国居民膳食指南（2022）》平衡膳食八准则核心推荐（data/dietary_guidelines_2022.md）+ 准则六详细实践（data/dietary_guidelines_rule6_detail.md）
- 抓取日期：2026-10-28

## 3. 切片产物
- data/kb_foods.txt：307 条食物，每食物一段（按知识点切片）
- data/kb_guidelines.txt：8 准则 + 准则六详细版，每准则一段
""")

    print(f"kb_foods: {len(foods)} 条食物切片")
    print(f"kb_guidelines: {len(g)} 段指南切片")
    print(f"食物营养项合计非空条目: {n_food_items}")


if __name__ == "__main__":
    main()
