#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, re, os
import yaml

def str_(val):
    if not type(val) is float:
        return str(val)
    return "{:.2f}".format(val)

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
                id_ = words[0]
                title = words[1]
                amount = words[2]
                unit = words[3]
                carbo = words[4]
    
                info = {}
                info['title'] = title
                info['amount'] = float(amount)
                info['unit'] = unit
                info['carbo'] = float(carbo)
    
                res[id_] = info
        return res

    def get_title(self, key):
        return self.map[key]['title'] if key in self.map else None

    def get_carbo(self, key, amount, unit):
        if not key in self.map:
            return None

        info = self.map[key]
        if unit and info["unit"] != unit:
            return None

        return amount / info["amount"] * info["carbo"]

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

    def bold_if(self, txt, cond, suffix=""):
        txt = str_(txt) + str_(suffix)
        if not cond:
            return txt
        return '<span style="background:red;color:white"> __' + txt + "__ </span>"

    def calc_using_ketto(self, ketto):
        before = ketto.get("before")
        after1 = ketto.get("1h_after")
        after2 = ketto.get("2h_after")

        if after1 or after2:
            after = max(after1 or 0, after2 or 0)
            diff = after - before
            tobun = diff / 1.4
            return diff, tobun
        return None, None

    def markdown_index(self):
        yield "## もくじ"
        yield ""

        for x in self.lst:
            date = str_(x["date"])
            yield '- <a href="#' + date + '"> ' + date + '</a>'

        yield ""

    def markdown_ketto(self, ketto, carbo_sum):
        before = ketto["before"]

        yield "- 血糖"
        yield "  - 食前: " + str_(before)

        after1 = ketto.get("1h_after")
        after2 = ketto.get("2h_after")

        if after1:
            yield "  - 食後１時間: " + str_(after1)
        if after2:
            yield "  - 食後２時間: " + str_(after2)

        diff, tobun = self.calc_using_ketto(ketto)
        if tobun:
            yield "  - 考察"
            yield "    - 差分: " + str_(diff)
            yield "    - 差分から想定される摂取糖分量: " + self.bold_if(tobun, 40 < tobun, "g")
 
    def markdown(self, carbo_map):
        yield "# めし"

        yield from self.markdown_index()

        for x in self.lst:
            date = x["date"]
            meals = x["meals"]

            yield "## " + str_(date)

            carbo_total = 0
            carbo_total_estimated = 0
            for meal_type in meals.keys():
                if meal_type == "kanso":
                    continue

                yield ""
                yield "### " + meal_type
                yield ""

                opt_img_path = str_(date) + meal_type

                meal = meals[meal_type]

                img_name = str_(date) + "_" + meal_type
                img_fname = img_name + ".jpg"
                if os.path.exists(img_fname):
                    yield '<img src="' + img_fname + '" alt="' + img_name +'" width="250"/>'
                    yield ""

                yield "- 食った時間：" + meal["time"]

                yield "- 内容"
                foods = meal["foods"]
                carbo_sum = 0
                for key, indicator in foods.items():
                    quantity, carbo = self.read_indicator(carbo_map, key, indicator)

                    if carbo is None:
                        raise Exception("Invalid food: " + key + ", " + indicator)

                    title = carbo_map.get_title(key) or key
                    display_quantity = " (" + str_(quantity) + ")" if quantity else ""
                    yield "  - " + title + display_quantity + ": " + str_(carbo) + "g"

                    carbo_sum += carbo

                yield "- 合計糖分: " + self.bold_if(carbo_sum, 40 < carbo_sum, "g")

                estimated_tobun = None
                if "ketto" in meal:
                    yield from self.markdown_ketto(meal["ketto"], carbo_sum)
                    _a, tobun = self.calc_using_ketto(meal["ketto"])
                    estimated_tobun = tobun

                carbo_total += carbo_sum
                carbo_total_estimated += estimated_tobun if estimated_tobun else carbo_sum

            yield ""
            yield "### まとめ"
            yield ""
            yield "- 総計糖分: " + self.bold_if(carbo_total, 120 < carbo_total, "g") + \
                    " ( 〜" + self.bold_if(carbo_total_estimated, 120 < carbo_total_estimated, "g") + " )"
            if "kanso" in meals:
                yield from ("- " + item for item in meals["kanso"])

def main():
    carbo_map = CarboMap("carbo.csv")
    meshi_map = MeshiMap("meshi.yaml")

    with open("out/meshi.md", "w") as f:
        for line in meshi_map.markdown(carbo_map):
            print(line, file=f)

if __name__== "__main__":
    main()
