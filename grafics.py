import matplotlib.pyplot as plt
import pandas as pd



async def get_graphs(uid):
    df = pd.read_csv(f'user_data/{uid}/report.csv')

    #1
    top_dishes = df.groupby('блюдо')[['план_порций', 'продано_порций']].sum().head(10)
    top_dishes.plot(kind='bar', figsize=(12, 6))
    plt.title('План vs Факт по топ-10 блюдам')
    plt.ylabel('Порции')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'user_data/{uid}/plan_vs_fact.png')
    plt.close()


    #2
    revenue_by_day = df.groupby('день_недели')['выручка'].sum()
    days_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    revenue_by_day = revenue_by_day.reindex(days_order, fill_value=0)
    revenue_by_day.plot(kind='line', marker='o', figsize=(10, 5), color='purple')
    plt.title('Выручка по дням недели')
    plt.ylabel('Выручка (руб.)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'user_data/{uid}/revenue_by_day.png')
    plt.close()



    #3
    status_count = df['статус'].value_counts()
    status_count.plot(kind='pie', autopct='%1.1f%%', figsize=(8, 8), colors=['lightgreen', 'yellow', 'red'])
    plt.title('Распределение статусов блюд')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(f'user_data/{uid}/status_pie.png')
    plt.close()