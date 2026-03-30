import pandas as pd
import numpy as np
import logging

choices = {
    "Перерасход": "red",
    "Риск (низкие продажи)": "yellow",
    "Норма": "lightgreen"
}



def bad_great_good_status(row):
    color = "background-color:" + choices[row["статус"]]
    return [""] * (len(row)-2) + [color] + [""]



async def get_report(uid):
    try:
        plan = pd.read_csv(f'user_data/{uid}/menu_plan.csv')
        fact = pd.read_csv(f'user_data/{uid}/sales_fact.csv')

        sum_table = plan.merge(fact, on=["дата", "день_недели", "id_блюда"], how="left")


        sum_table["выполнение_плана_%"] = round(
            sum_table["продано_порций"] / sum_table["план_порций"] * 100, 1
        )

        sum_table["выручка"] = sum_table["продано_порций"] * sum_table["цена"]

        conditions = [
            sum_table["продано_порций"] > sum_table["остаток_на_начало"],
            sum_table["выполнение_плана_%"] < 70,
            True]

        sum_table["статус"] = np.select(conditions, choices.keys(), default="Норма")

        sum_table['решение_проблемы'] = np.select(
            [sum_table["статус"] == "Перерасход",
                    sum_table["статус"] == "Риск (низкие продажи)",
                    sum_table["статус"] == "Норма"],
            ["Увеличить план по продажам / скорректировать закупки",
                "Увеличить рекламу или переместить блюдо в более заметное место / сменить на другое блюдо",
                "ОК"],

            default="ОК"
        )


        styled = sum_table.style.apply(bad_great_good_status, axis=1)

        return styled, sum_table
    except Exception as e:
        logging.error(e)
        return None, None

