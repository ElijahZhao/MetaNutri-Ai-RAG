"""Select common foods from the full list (keyword whitelist per category, with caps).

Input:  data/foods_all_list.csv (food_id, name, category_id)
Output: data/foods_selected_list.csv (food_id, name, category_id)
"""
import csv
from collections import defaultdict

CAT_KEYWORDS = {
    1:  ["小麦粉", "挂面", "面条", "通心粉", "大米", "糯米", "糙米", "玉米面", "小米", "燕麦", "荞麦", "馒头", "花卷", "烙饼", "油条", "面包"],
    10: ["马铃薯", "甘薯", "木薯", "魔芋", "粉丝", "藕粉"],
    11: ["黄豆", "黑豆", "青豆", "绿豆", "赤豆", "红豆", "芸豆", "蚕豆", "豆腐", "豆浆", "腐竹", "豆芽"],
    12: ["白萝卜", "红萝卜", "胡萝卜", "番茄", "黄瓜", "茄子", "青椒", "洋葱", "大蒜", "白菜", "菠菜", "油菜", "芹菜", "生菜", "西兰花", "菜花", "冬瓜", "南瓜", "莲藕", "山药", "韭菜", "豆角", "空心菜", "莴笋", "竹笋", "芦笋", "苦瓜", "丝瓜", "西葫芦", "豇豆", "香菜", "蒜苗", "葱", "姜", "香椿"],
    13: ["香菇", "蘑菇", "金针菇", "平菇", "木耳", "银耳", "海带", "紫菜", "草菇", "口蘑", "猴头菇", "茶树菇", "竹荪"],
    14: ["苹果", "香蕉", "橙", "橘", "梨", "葡萄", "桃", "草莓", "西瓜", "猕猴桃", "柚子", "樱桃", "蓝莓", "菠萝", "芒果", "荔枝", "哈密瓜", "火龙果", "柠檬", "椰子", "石榴", "柿子", "枣", "杏", "桂圆", "枇杷", "木瓜", "山楂"],
    15: ["核桃", "板栗", "栗子", "花生", "瓜子", "芝麻", "杏仁", "开心果", "腰果", "松子", "白果", "榛子"],
    16: ["猪肉", "牛肉", "羊肉", "猪肝", "猪心", "猪蹄", "牛肝", "牛肚", "羊肝", "火腿", "香肠", "腊肉"],
    17: ["鸡胸", "鸡腿", "鸡翅", "鸡肝", "鸡爪", "鸭掌", "鸭肝", "鸭肉", "鹅"],
    18: ["牛乳", "牛奶", "酸奶", "奶粉", "奶酪", "奶油", "炼乳"],
    19: ["鸡蛋", "鸭蛋", "鹅蛋", "鹌鹑蛋", "鸽蛋", "松花蛋", "咸鸭蛋", "皮蛋"],
    20: ["草鱼", "鲤鱼", "鲫鱼", "鲈鱼", "带鱼", "黄花鱼", "鲳鱼", "鳕鱼", "三文鱼", "鲑鱼", "金枪鱼", "罗非鱼", "鳗鱼", "虾", "蟹", "蛤", "牡蛎", "扇贝", "鱿鱼", "墨鱼", "海参", "泥鳅", "鳝鱼", "田螺"],
    22: ["煎饼", "豆腐脑", "凉粉", "元宵", "汤圆", "粽子", "月饼", "年糕"],
    23: ["方便面", "薯条", "汉堡", "比萨", "披萨", "炸鸡", "雪糕", "爆米花"],
    24: ["可乐", "橙汁", "苹果汁", "葡萄汁", "茶", "奶茶", "咖啡", "椰子汁", "杏仁露", "果汁"],
    25: ["啤酒", "葡萄酒", "白酒", "黄酒", "米酒"],
    26: ["白砂糖", "绵白糖", "冰糖", "红糖", "巧克力", "蜂蜜"],
    27: ["花生油", "大豆油", "豆油", "菜籽油", "玉米油", "橄榄油", "葵花籽油", "芝麻油", "香油", "猪油", "牛油", "黄油"],
    28: ["酱油", "生抽", "老抽", "醋", "豆瓣酱", "花生酱", "甜面酱", "芝麻酱", "味精", "鸡精", "蚝油", "咖喱", "辣椒酱", "番茄酱", "沙拉酱"],
    29: ["枸杞", "菊花"],
}
CAPS = {1: 26, 10: 9, 11: 18, 12: 52, 13: 14, 14: 34, 15: 13, 16: 20, 17: 9, 18: 9, 19: 9, 20: 26, 22: 8, 23: 8, 24: 11, 25: 6, 26: 7, 27: 12, 28: 16, 29: 2}


def rank(name: str) -> tuple:
    """Prefer generic/mean entries over brand/variant ones."""
    has_brand = any(k in name for k in ["牌", "肯德基", "麦当劳", "惠氏", "雀巢", "美赞臣", "三元", "伊利", "蒙牛", "光明", "汇源", "青岛", "燕京", "长城", "张裕", "王朝"])
    has_mean = "均值" in name
    return (has_brand, not has_mean, len(name))


def main():
    foods = defaultdict(list)
    for row in csv.DictReader(open("data/foods_all_list.csv", encoding="utf-8")):
        foods[int(row["category_id"])].append((row["food_id"], row["name"]))

    selected, matched_kw = [], defaultdict(set)
    for cat, kws in CAT_KEYWORDS.items():
        pool = []
        for food_id, name in foods.get(cat, []):
            for kw in kws:
                if kw in name:
                    pool.append((food_id, name, kw))
        # dedup: one food may match multiple keywords; keep first keyword match
        seen_food = {}
        for food_id, name, kw in pool:
            if food_id not in seen_food:
                seen_food[food_id] = kw
        items = [(fid, nm, seen_food[fid]) for fid, nm, kw in pool]
        # per-keyword cap: prefer generic entries, max 3 per keyword
        by_kw = defaultdict(list)
        for food_id, name, kw in items:
            by_kw[kw].append((food_id, name))
        for kw, arr in by_kw.items():
            arr.sort(key=lambda x: rank(x[1]))
            for food_id, name in arr[:4]:
                matched_kw[cat].add(kw)
                if len(selected) < 0:  # no-op guard
                    pass
        # global cap per category
        cat_pool = []
        for kw, arr in by_kw.items():
            arr.sort(key=lambda x: rank(x[1]))
            cat_pool.extend(arr[:4])
        # dedup food_id across keywords
        seen = set()
        for food_id, name in sorted(cat_pool, key=lambda x: rank(x[1])):
            if food_id in seen:
                continue
            seen.add(food_id)
            selected.append((food_id, name, cat))
        # apply cap: keep generic-first
        sel = [x for x in selected if x[2] == cat]
        if len(sel) > CAPS.get(cat, 99):
            sel.sort(key=lambda x: rank(x[1]))
            keep = set()
            for fid, nm, c in sel[: CAPS[cat]]:
                keep.add(fid)
            selected = [x for x in selected if x[2] != cat or x[0] in keep]

    selected.sort(key=lambda x: (x[2], x[1]))
    with open("data/foods_selected_list.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["food_id", "name", "category_id"])
        w.writerows(selected)
    print("SELECTED total:", len(selected))
    from collections import Counter
    for c, n in sorted(Counter(x[2] for x in selected).items()):
        print(f"  cat {c}: {n}")
    print("Sample:", [x[1] for x in selected[:10]])


if __name__ == "__main__":
    main()
