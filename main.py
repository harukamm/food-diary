#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, re, os
import yaml

def str_(val):
    if not type(val) is float:
        return str(val)
    return "{0:.2f}".format(val).rstrip('0').rstrip('.')

class CarboMap:
    def __init__(self, fname):
        self.map = self.read_carbo(fname)

    @staticmethod
    def read_carbo(fname):
        res = {}
        with open(fname) as f:
            next(f)
            for line in f.readlines():
                words = line.split(',')
                if len(words) < 2:
                    continue
                if words[0][0] == '#':
                    continue
                if len(words) < 5:
                    raise Exception("Invalid carbo line: " + line)

                id_ = words[0]
                title = words[1]
                amount = words[2]
                unit = words[3]
                carbo = words[4]
                is_kome = words[5].strip() == 'x' if 5 < len(words) else False

                tup = (float(amount), unit, float(carbo))
                if id_ in res:
                    res[id_]['amount_unit_carbo'].append(tup)
                else:
                    info = {}
                    info['title'] = title
                    info['amount_unit_carbo'] = [tup]
                    info['is_kome'] = is_kome
                    res[id_] = info

        return res

    def get_title(self, key):
        return self.map[key]['title'] if key in self.map else None

    def get_carbo(self, key, amount, unit):
        if not key in self.map:
            return None

        info = self.map[key]
        for amount_, unit_, carbo_ in info['amount_unit_carbo']:
            if not unit or unit_ == unit:
                return amount / amount_ * carbo_

        return None
        
    def get_carbo_rate_string(self, key):
        if not key in self.map:
            return None

        info = self.map[key]
        rate_string = []
        for amount_, unit_, carbo_ in info['amount_unit_carbo']:
            rate_string.append(str_(carbo_) + "g / " + \
                    str_(amount_) + unit_)

        return ', '.join(rate_string)

    def is_kome(self, key):
        if not key in self.map:
            return False

        info = self.map[key]
        return info["is_kome"]

    def knows(self, key):
        return key in self.map

class MeshiMap:
    def __init__(self, fname):
        self.lst = self.read_meshi(fname)

    @staticmethod
    def read_meshi(fname):
        res = []
        with open(fname) as f:
            obj = yaml.safe_load(f)
            dates = list(obj.keys())
            dates.sort()
            for date in dates:
                meals = obj[date]
                res.append({"date": date, "meals": meals})
        return res

    def read_indicator(self, carbo_map, key, indicator):
        # starts with #
        indicator = str_(indicator)
        m = re.match(r'^\s*#([^g]+)g$', indicator)
        if m:
            return None, float(m.group(1))

        # consists of amount and unit
        m = re.match(r'^([\d\.]+)([^\d]+)?$', indicator)
        if m:
            amount = float(m.group(1))
            unit = m.group(2) or ""
            return str_(amount) + unit, carbo_map.get_carbo(key, amount, unit)

        return None

    def parse_date(self, date):
        m = re.match(r'(\d{4})(\d{2})(\d{2})', str_(date))
        return (m.group(1), m.group(2), m.group(3))

    def format_date(self, date):
        return "/".join(self.parse_date(date))

    def bold_if(self, txt, cond, suffix=""):
        txt = str_(txt) + str_(suffix)
        if not cond:
            return txt
        return '<span style="background:red;color:white"> __' + txt + "__ </span>"

    def parse_ketto(self, val):
        if type(val) is str and val[-1] is '?':
            return int(val[:-1]), True
        return val, False

    def calc_using_ketto(self, ketto):
        before, before_guessed = self.parse_ketto(ketto.get("before"))
        after1, after1_guessed = self.parse_ketto(ketto.get("1h_after"))
        after2, after2_guessed = self.parse_ketto(ketto.get("2h_after"))

        if after1 or after2:
            after = max(after1 or 0, after2 or 0)
            hour_diff = 1 if after1 == after else 2
            after_guessed = after1_guessed if after1 == after else after2_guessed
            diff = after - before
            return diff, hour_diff, before, after, before_guessed, after_guessed
        return None

    def format_remark(self, items):
        res = []
        for item in items:
            if item == 'kome':
                res.append('米')
            elif item == 'sanpo':
                res.append('歩')
            elif item == 'zesshoku':
                res.append('絶食')
            else:
                raise Exception("Invalid remark item: " + item)
        return ",".join(res)

    def describe_remark(self, items):
        res = []
        for item in items:
            if item == 'kome':
                res.append('米系あり')
            elif item == 'sanpo':
                res.append('食後に散歩')
            elif item == 'zesshoku':
                res.append('前食抜き')
            else:
                raise Exception("Invalid remark item: " + item)
        return ",".join(res)

    def exceed_recommended_ketto_after_meal(self, ketto, diff):
        if diff == 2:
            return 120 <= ketto
        elif diff == 1:
            return 140 <= ketto
        else:
            raise Exception("Unknown hour diff: " + str(diff))

    def markdown_index(self):
        yield "## もくじ"
        yield ""

        item_per_month = {}
        for x in self.lst:
            date = str_(x["date"])
            y, m, d = self.parse_date(date)
            key = y + "/" + m

            links = []
            if key in item_per_month:
                links = item_per_month[key]
            else:
                item_per_month[key] = links

            links.append('<a href="#' + date + '">' + d + '</a>')

        for key, links in item_per_month.items():
            yield '- ' + key + ' ' + ' | '.join(links)

        yield '- <a href="#テーブル"> テーブル </a>'

        yield ""

    def markdown_ketto(self, ketto, carbo_sum):
        diff, hour_diff, before, after, before_guessed, after_guessed = self.calc_using_ketto(ketto)

        yield "- 血糖"
        yield "  - 食前: " + str_(before) + (" (推定)" if before_guessed else "")
        yield "  - 食後 " + str_(hour_diff) + " 時間: " + str_(after) + (" (推定)" if after_guessed else "")
        yield "  - 差分: " + str_(diff)
 
    def markdown(self, carbo_map):
        yield "# めし"

        yield from self.markdown_index()

        ketto_history = {}
        carbo_history = {}
        for x in self.lst:
            date = x["date"]
            date_ = str_(date)
            meals = x["meals"]

            yield ""
            yield "## " + self.format_date(date_)
            yield ""

            carbo_total = 0
            for meal_type in meals.keys():
                if meal_type == "kanso":
                    continue

                id_ = date_ + "_" + meal_type
                yield ""
                yield "### <div id='" + id_ + "'>" + meal_type + "</div>"
                yield ""

                meal = meals[meal_type]

                img_name = date_ + "_" + meal_type
                img_fname = "img/" + img_name + ".jpg"
                if os.path.exists(img_fname):
                    yield '<img src="' + img_fname + '" alt="' + img_name +'" width="300"/>'
                    yield ""

                yield "- 食った時間：" + meal["time"]

                yield "- 申告糖分"
                foods = meal["foods"]
                carbo_sum = 0
                has_kome = False
                remarks = []
                for key, indicator in foods.items():
                    quantity, carbo = self.read_indicator(carbo_map, key, indicator)

                    if carbo is None:
                        raise Exception("Invalid food: " + key + ", " + indicator)

                    title = carbo_map.get_title(key) or key
                    display_quantity = " (" + str_(quantity) + ")" if quantity else ""
                    yield "  - " + title + display_quantity + ": " + str_(carbo) + "g"

                    carbo_sum += carbo
                    has_kome = has_kome or carbo_map.is_kome(key)

                yield "- 合計糖分: " + self.bold_if(carbo_sum, 40 < carbo_sum, "g")
                carbo_history[date_ + "_" + meal_type] = carbo_sum

                if "remark" in meal:
                    remark = meal["remark"]
                    remarks = remarks + remark.split(',')
                    yield "- 注釈: " + self.describe_remark(remarks)

                if "ketto" in meal:
                    yield from self.markdown_ketto(meal["ketto"], carbo_sum)
                    diff, hour_diff, ketto1, ketto2, ketto1_guessed, ketto2_guessed = self.calc_using_ketto(meal["ketto"])
                    ketto_history[date_ + "_" + meal_type] = { \
                            "ketto_before": ketto1, "ketto_after": ketto2, \
                            "ketto_before_guessed": ketto1_guessed, "ketto_after_guessed": ketto2_guessed, \
                            "ketto_diff": diff, "carbo_sum": carbo_sum, "hour_diff": hour_diff, \
                            "remark_items": ['kome'] + remarks if has_kome else remarks \
                            }

                carbo_total += carbo_sum

            yield ""
            yield "### 感想"
            yield ""
            yield "- 総計糖分: " + self.bold_if(carbo_total, 120 < carbo_total, "g")
            if "kanso" in meals:
                yield from ("- " + item for item in meals["kanso"])

            yield "---"

        yield ""
        yield "## テーブル"
        yield ""

        #yield "### 合計糖質"

        #yield   "| 日付 | 合計糖分 (g) |"
        #yield   "| ---- | ---- |"
        #x = 0
        #for key in carbo_history.keys():
        #    v = carbo_history[key]
        #    x += v
        #    yield "| " + key + " | " + str_(v) + " | "

        yield "### 上昇血糖割合"

        keys = list(ketto_history.keys())
        keys.sort()
        yield   "|  | 時 | 糖質量 | 食前 | 食後 | 差 | 上昇率 | 間隔 | 注釈 |"
        yield   "| ---- | ---- | ---- | ---- | --- | ---- | ---- | ---- | ---- |"

        for key in keys:
            info = ketto_history[key]
            date, meal_type = key.split('_')
            a = info["ketto_diff"]
            b = info["carbo_sum"]
            c = a / b
            d = info["hour_diff"]
            e = info["ketto_before"]
            f = info["ketto_after"]
            ketto_before = self.bold_if(e, 90 <= e)
            ketto_after = self.bold_if(f, self.exceed_recommended_ketto_after_meal(f, d))
            ketto_before_guessed = info["ketto_before_guessed"]
            ketto_after_guessed = info["ketto_after_guessed"]

            remark = self.format_remark(info["remark_items"])
            link = "<a href='#" + key + "'>#</a>"
            display_meal_type = { "breakfast": "朝", "lunch": "昼", "dinner": "夕" }

            yield "| " + link + " | " + display_meal_type.get(meal_type, meal_type) + " | " + str_(b) + "g | " + \
                    ketto_before + ("?" if ketto_before_guessed else "") + " | " + \
                    ketto_after + ("?" if ketto_after_guessed else "") + " | +" + str_(a) + " | " + str_(c) + " | " + str_(d) + " | " + remark + " | "


class KaimonoMap:
    def __init__(self, fname):
        self.map = self.read(fname)

    @staticmethod
    def read(fname):
        res = {}
        with open(fname) as f:
            obj = yaml.safe_load(f)
            genres = list(obj.keys())
            i = 0
            for genre in genres:
                items = obj[genre]
                res[genre] = { "items": items, "id": str_(i) }
                i += 1
        return res

    def parse_modifiers(self, modifiers):
        size = len(modifiers)
        is_important = False
        is_weakly_recommended = False

        i = 0
        while i < size:
            c = modifiers[i]
            next_c = modifiers[i + 1] if i + 1 < size else None

            if c == '!':
                is_important = True
                i += 1
            elif c == '(' and next_c == ')':
                is_weakly_recommended = True
                i += 2
            else:
                i += 1

        return is_important, is_weakly_recommended

    def format_item(self, item, carbo_map):
        m = re.match(r'^(#)?([\w-]+)(.*)$', item)
        if not m:
            raise Exception("Invalid item: " + item)

        has_hash = bool(m.group(1))
        item_key = m.group(2)
        modifiers = m.group(3)

        if has_hash:
            carbo_rate_str = ""
            title = item_key
        else:
            carbo_rate_str = carbo_map.get_carbo_rate_string(item_key)
            title = carbo_map.get_title(item_key)
            if not carbo_rate_str or not title:
                raise Exception("Unknown key: " + item_key)

        return self.item_html(title, carbo_rate_str, modifiers)

    def item_html(self, title, carbo_rate_str, modifiers):
        is_important, is_weakly_recommended = \
                self.parse_modifiers(modifiers)

        result = '<span class="title">' + title + '</span>'
        carbo_color = 'gray'
        if is_important:
            result = "__" + result + "__"
        if is_weakly_recommended:
            color = '#ccc'
            carbo_color = color
            result = '<span style="color:' + color + ';">' + result + '</span>'

        return result + ' <span style="color:' + carbo_color + ';">' + carbo_rate_str + '</span>'

    def markdown(self, carbo_map):
        yield "# かいものリスト"

        for genre, info in self.map.items():
            yield ""
            yield "## " + genre

            id_ = info["id"]
            items = info["items"]
            item_index = 0

            for item in items:
                check_box_name = 'chk_' + str_(id_) + '_' + str_(item_index)
                checkbox = '<input type="checkbox" name="' + check_box_name + '"> '
                yield "- " + checkbox + self.format_item(item, carbo_map)
                item_index += 1

    # <input type="checkbox" name="chk_sample" value="apple">

def exec_meshi_mode():
    carbo_map = CarboMap("carbo.csv")
    meshi_map = MeshiMap("meshi.yaml")

    with open("out/meshi.md", "w") as f:
        for line in meshi_map.markdown(carbo_map):
            print(line, file=f)

def exec_kaimono_mode():
    carbo_map = CarboMap("carbo.csv")
    kaimono_map = KaimonoMap("kaimono_lst.yaml")

    with open("out/kaimono.md", "w") as f:
        for line in kaimono_map.markdown(carbo_map):
            print(line, file=f)

def exec_mode(mode):
    if mode == "meshi":
        exec_meshi_mode()
    elif mode == "kaimono":
        exec_kaimono_mode()
    else:
        raise Exception("Unknown mode: " + mode)

def main():
    if len(sys.argv) < 2:
        print("python3 main.py <meshi>+")
        sys.exit(1)

    for mode in sys.argv[1:]:
        exec_mode(mode)

if __name__== "__main__":
    main()
