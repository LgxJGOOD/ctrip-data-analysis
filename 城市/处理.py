import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('beijing_scenic_spots.csv')


# 数据清洗（同之前）
def clean_data(df):
    before_count = len(df)
    df = df.drop_duplicates(subset=['景点名称'], keep='first')
    after_count = len(df)
    print(f"去重前: {before_count} 条, 去重后: {after_count} 条, 删除重复: {before_count - after_count} 条")

    df['星级'] = df['星级'].astype(str).str.extract(r'(\d+[A-Z]?)')[0]
    df['评分'] = pd.to_numeric(df['评分'], errors='coerce')
    df['热度'] = pd.to_numeric(df['热度'], errors='coerce')

    def parse_review_count(x):
        if pd.isna(x):
            return 0
        x = str(x)
        if '万' in x:
            return float(x.replace('万条点评', '').replace('万', '')) * 10000
        elif '条' in x:
            return float(x.replace('条点评', '').replace('条', ''))
        return 0

    df['点评数量_数值'] = df['点评数量'].apply(parse_review_count)

    def parse_price(x):
        if pd.isna(x):
            return 0
        x = str(x)
        import re
        match = re.search(r'(\d+)', x)
        return int(match.group(1)) if match else 0

    import re
    df['票价_数值'] = df['票价'].apply(parse_price)

    df['区域'] = df['地址'].str.split('·').str[0]
    return df


df = clean_data(df)

# 创建多个独立的图表（每个图表单独保存）
fig1 = plt.figure(figsize=(12, 8))
star_counts = df[df['星级'].notna() & (df['星级'] != '')]['星级'].value_counts()
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
wedges, texts, autotexts = plt.pie(star_counts.values, labels=star_counts.index, autopct='%1.1f%%',
                                   colors=colors[:len(star_counts)], startangle=90, textprops={'fontsize': 12})
for autotext in autotexts:
    autotext.set_fontsize(12)
plt.title('北京各星级景点数量占比', fontsize=18, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('1_星级占比.png', dpi=150, bbox_inches='tight')
plt.show()

# 2. 景区评分TOP15
fig2 = plt.figure(figsize=(14, 10))
top_score = df.nlargest(15, '评分')[['景点名称', '评分']]
colors_bar = plt.cm.RdYlGn(top_score['评分'] / 5)
plt.barh(range(len(top_score)), top_score['评分'].values, color=colors_bar)
plt.yticks(range(len(top_score)), top_score['景点名称'].values, fontsize=11)
plt.xlabel('评分', fontsize=13)
plt.title('景区评分TOP15 (满分5分)', fontsize=18, fontweight='bold', pad=20)
plt.gca().invert_yaxis()
for i, v in enumerate(top_score['评分'].values):
    plt.text(v + 0.02, i, f'{v:.1f}', va='center', fontsize=11)
plt.tight_layout()
plt.savefig('2_评分TOP15.png', dpi=150, bbox_inches='tight')
plt.show()

# 3. 景区热度TOP15
fig3 = plt.figure(figsize=(14, 10))
top_hot = df.nlargest(15, '热度')[['景点名称', '热度']]
colors_hot = plt.cm.plasma(top_hot['热度'] / 10)
plt.barh(range(len(top_hot)), top_hot['热度'].values, color=colors_hot)
plt.yticks(range(len(top_hot)), top_hot['景点名称'].values, fontsize=11)
plt.xlabel('热度', fontsize=13)
plt.title('景区热度TOP15 (满分10分)', fontsize=18, fontweight='bold', pad=20)
plt.gca().invert_yaxis()
for i, v in enumerate(top_hot['热度'].values):
    plt.text(v + 0.1, i, f'{v:.0f}', va='center', fontsize=11)
plt.tight_layout()
plt.savefig('3_热度TOP15.png', dpi=150, bbox_inches='tight')
plt.show()

# 4. 各景区评论数占比 TOP15（改为条形图，更清晰）
fig4 = plt.figure(figsize=(14, 10))
top_reviews = df.nlargest(15, '点评数量_数值')[['景点名称', '点评数量_数值']]
colors_reviews = plt.cm.Greens(np.linspace(0.3, 0.9, len(top_reviews)))
plt.barh(range(len(top_reviews)), top_reviews['点评数量_数值'].values, color=colors_reviews)
plt.yticks(range(len(top_reviews)), top_reviews['景点名称'].values, fontsize=11)
plt.xlabel('评论数量', fontsize=13)
plt.title('评论数量TOP15', fontsize=18, fontweight='bold', pad=20)
plt.gca().invert_yaxis()
for i, v in enumerate(top_reviews['点评数量_数值'].values):
    if v >= 10000:
        label = f'{v / 10000:.1f}万'
    else:
        label = f'{v:.0f}'
    plt.text(v + 200, i, label, va='center', fontsize=10)
plt.tight_layout()
plt.savefig('4_评论数TOP15.png', dpi=150, bbox_inches='tight')
plt.show()

# 5. 门票价格分布
fig5 = plt.figure(figsize=(12, 8))
price_data = df[df['票价_数值'] > 0]['票价_数值']
plt.hist(price_data, bins=25, color='#FF6B6B', edgecolor='black', alpha=0.7)
plt.axvline(price_data.median(), color='blue', linestyle='--', linewidth=2,
            label=f'中位数: {price_data.median():.0f}元')
plt.axvline(price_data.mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {price_data.mean():.0f}元')
plt.xlabel('门票价格 (元)', fontsize=13)
plt.ylabel('景点数量', fontsize=13)
plt.title('北京景区门票价格分布', fontsize=18, fontweight='bold', pad=20)
plt.legend(fontsize=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('5_门票价格分布.png', dpi=150, bbox_inches='tight')
plt.show()

# 6. 各区域景点数量分布
fig6 = plt.figure(figsize=(14, 10))
region_counts = df['区域'].value_counts().head(15)
colors_region = plt.cm.Set3(np.linspace(0, 1, len(region_counts)))
plt.barh(range(len(region_counts)), region_counts.values, color=colors_region)
plt.yticks(range(len(region_counts)), region_counts.index, fontsize=11)
plt.xlabel('景点数量', fontsize=13)
plt.title('各区域景点数量TOP15', fontsize=18, fontweight='bold', pad=20)
plt.gca().invert_yaxis()
for i, v in enumerate(region_counts.values):
    plt.text(v + 0.1, i, str(v), va='center', fontsize=11)
plt.tight_layout()
plt.savefig('6_区域景点数量.png', dpi=150, bbox_inches='tight')
plt.show()

# 7. 评分与热度散点图
fig7 = plt.figure(figsize=(12, 8))
scatter = plt.scatter(df['评分'], df['热度'], c=df['点评数量_数值'],
                      cmap='YlOrRd', s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
plt.xlabel('评分', fontsize=13)
plt.ylabel('热度', fontsize=13)
plt.title('评分 vs 热度 (点大小=评论数)', fontsize=18, fontweight='bold', pad=20)
cbar = plt.colorbar(scatter)
cbar.set_label('评论数量', fontsize=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('7_评分热度关系.png', dpi=150, bbox_inches='tight')
plt.show()

# 8. 各星级平均票价对比
fig8 = plt.figure(figsize=(10, 8))
star_price = df[df['星级'].notna() & (df['票价_数值'] > 0)].groupby('星级')['票价_数值'].mean().sort_index()
bars = plt.bar(star_price.index, star_price.values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
plt.xlabel('星级', fontsize=13)
plt.ylabel('平均票价 (元)', fontsize=13)
plt.title('各星级景区平均票价对比', fontsize=18, fontweight='bold', pad=20)
for i, v in enumerate(star_price.values):
    plt.text(i, v + 2, f'{v:.0f}元', ha='center', fontsize=12)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('8_星级均价对比.png', dpi=150, bbox_inches='tight')
plt.show()

# 9. 评分分布
fig9 = plt.figure(figsize=(12, 8))
score_data = df[df['评分'].notna()]['评分']
plt.hist(score_data, bins=20, color='#4ECDC4', edgecolor='black', alpha=0.7)
plt.axvline(score_data.mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {score_data.mean():.2f}')
plt.axvline(score_data.median(), color='blue', linestyle='--', linewidth=2, label=f'中位数: {score_data.median():.2f}')
plt.xlabel('评分', fontsize=13)
plt.ylabel('景点数量', fontsize=13)
plt.title('景区评分分布', fontsize=18, fontweight='bold', pad=20)
plt.legend(fontsize=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('9_评分分布.png', dpi=150, bbox_inches='tight')
plt.show()

# 统计信息输出
print("\n" + "=" * 60)
print("📊 数据统计摘要")
print("=" * 60)
print(f"总景点数: {len(df)}")
print(f"5A景区数: {len(df[df['星级'] == '5A'])}")
print(f"4A景区数: {len(df[df['星级'] == '4A'])}")
print(f"平均评分: {df['评分'].mean():.2f}/5.0")
print(f"平均热度: {df['热度'].mean():.1f}/10")
print(f"免费景点数: {len(df[df['票价_数值'] == 0])}")
if len(df[df['票价_数值'] > 0]) > 0:
    print(f"最贵门票: {df['票价_数值'].max()}元 ({df[df['票价_数值'] == df['票价_数值'].max()]['景点名称'].values[0]})")
print(f"评论最多: {df.loc[df['点评数量_数值'].idxmax(), '景点名称']} ({df['点评数量_数值'].max():.0f}条)")
print(f"评分最高: {df.loc[df['评分'].idxmax(), '景点名称']} ({df['评分'].max():.1f}分)")