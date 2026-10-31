import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('beijing_hotels.csv')


# 数据清洗和去重
def clean_data(df):
    before_count = len(df)

    # 1. 按酒店名称去重
    df = df.drop_duplicates(subset=['酒店名称'], keep='first')
    after_count = len(df)
    print(f"去重前: {before_count} 条, 去重后: {after_count} 条, 删除重复: {before_count - after_count} 条")

    # 2. 清洗星级（转换为数字）
    df['星级_数值'] = df['星级'].astype(str).str.extract(r'(\d+)')[0]
    df['星级_数值'] = pd.to_numeric(df['星级_数值'], errors='coerce')

    # 3. 清洗评分（转换为浮点数）
    df['评分_数值'] = pd.to_numeric(df['评分'], errors='coerce')

    # 4. 清洗点评数量
    def parse_review_count(x):
        if pd.isna(x):
            return 0
        x = str(x)
        num_match = re.search(r'(\d+)', x)
        return int(num_match.group(1)) if num_match else 0

    df['点评数量_数值'] = df['点评数量'].apply(parse_review_count)

    # 5. 清洗价格
    def parse_price(x):
        if pd.isna(x):
            return 0
        x = str(x)
        num_match = re.search(r'(\d+)', x)
        return int(num_match.group(1)) if num_match else 0

    df['价格_数值'] = df['价格'].apply(parse_price)

    # 6. 提取主要区域（位置区域的第一部分）
    df['主要区域'] = df['位置区域'].str.split('·').str[0].str.strip()

    # 7. 评分等级分类
    def score_level(score):
        if pd.isna(score):
            return '未知'
        if score >= 4.8:
            return '极好(4.8+)'
        elif score >= 4.5:
            return '优秀(4.5-4.8)'
        elif score >= 4.0:
            return '良好(4.0-4.5)'
        else:
            return '一般(<4.0)'

    df['评分等级'] = df['评分_数值'].apply(score_level)

    # 8. 价格区间分类
    def price_range(price):
        if price == 0:
            return '面议'
        elif price < 200:
            return '经济型(<200)'
        elif price < 400:
            return '舒适型(200-400)'
        elif price < 600:
            return '中档型(400-600)'
        else:
            return '高档型(600+)'

    df['价格区间'] = df['价格_数值'].apply(price_range)

    return df


df = clean_data(df)

# 创建可视化图表（每个图表独立，避免拥挤）
print("\n正在生成可视化图表...")

# 1. 酒店星级分布（饼图）
fig1 = plt.figure(figsize=(10, 8))
star_counts = df[df['星级_数值'].notna()]['星级_数值'].value_counts().sort_index()
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
plt.pie(star_counts.values, labels=[f'{i}星' for i in star_counts.index], autopct='%1.1f%%',
        colors=colors[:len(star_counts)], startangle=90, textprops={'fontsize': 12})
plt.title('北京酒店星级分布', fontsize=18, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('hotel_1_星级分布.png', dpi=150, bbox_inches='tight')
plt.show()

# 2. 酒店评分分布（直方图）
fig2 = plt.figure(figsize=(12, 8))
score_data = df[df['评分_数值'].notna()]['评分_数值']
plt.hist(score_data, bins=20, color='#4ECDC4', edgecolor='black', alpha=0.7)
plt.axvline(score_data.mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {score_data.mean():.2f}')
plt.axvline(score_data.median(), color='blue', linestyle='--', linewidth=2, label=f'中位数: {score_data.median():.2f}')
plt.xlabel('评分', fontsize=13)
plt.ylabel('酒店数量', fontsize=13)
plt.title('北京酒店评分分布', fontsize=18, fontweight='bold', pad=20)
plt.legend(fontsize=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('hotel_2_评分分布.png', dpi=150, bbox_inches='tight')
plt.show()

# 3. 评分TOP15酒店（水平条形图）
fig3 = plt.figure(figsize=(14, 10))
top_score = df[df['评分_数值'].notna()].nlargest(15, '评分_数值')[['酒店名称', '评分_数值', '点评数量_数值']]
colors_bar = plt.cm.RdYlGn(top_score['评分_数值'] / 5)
plt.barh(range(len(top_score)), top_score['评分_数值'].values, color=colors_bar)
plt.yticks(range(len(top_score)), top_score['酒店名称'].values, fontsize=10)
plt.xlabel('评分', fontsize=13)
plt.title('北京酒店评分TOP15', fontsize=18, fontweight='bold', pad=20)
plt.gca().invert_yaxis()
for i, (v, reviews) in enumerate(zip(top_score['评分_数值'].values, top_score['点评数量_数值'].values)):
    plt.text(v + 0.03, i, f'{v:.1f}分 ({reviews}条)', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('hotel_3_评分TOP15.png', dpi=150, bbox_inches='tight')
plt.show()

# 4. 价格分布（直方图）
fig4 = plt.figure(figsize=(12, 8))
price_data = df[df['价格_数值'] > 0]['价格_数值']
plt.hist(price_data, bins=25, color='#FF6B6B', edgecolor='black', alpha=0.7)
plt.axvline(price_data.median(), color='blue', linestyle='--', linewidth=2,
            label=f'中位数: {price_data.median():.0f}元')
plt.axvline(price_data.mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {price_data.mean():.0f}元')
plt.xlabel('价格 (元/晚)', fontsize=13)
plt.ylabel('酒店数量', fontsize=13)
plt.title('北京酒店价格分布', fontsize=18, fontweight='bold', pad=20)
plt.legend(fontsize=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('hotel_4_价格分布.png', dpi=150, bbox_inches='tight')
plt.show()

# 5. 各区域酒店数量TOP15（水平条形图）
fig5 = plt.figure(figsize=(14, 10))
region_counts = df['主要区域'].value_counts().head(15)
colors_region = plt.cm.Set3(np.linspace(0, 1, len(region_counts)))
plt.barh(range(len(region_counts)), region_counts.values, color=colors_region)
plt.yticks(range(len(region_counts)), region_counts.index, fontsize=10)
plt.xlabel('酒店数量', fontsize=13)
plt.title('北京各区域酒店数量TOP15', fontsize=18, fontweight='bold', pad=20)
plt.gca().invert_yaxis()
for i, v in enumerate(region_counts.values):
    plt.text(v + 0.3, i, str(v), va='center', fontsize=11)
plt.tight_layout()
plt.savefig('hotel_5_区域酒店数量.png', dpi=150, bbox_inches='tight')
plt.show()

# 6. 价格区间占比（饼图）
fig6 = plt.figure(figsize=(10, 8))
price_range_counts = df[df['价格区间'] != '面议']['价格区间'].value_counts()
colors_price = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
plt.pie(price_range_counts.values, labels=price_range_counts.index, autopct='%1.1f%%',
        colors=colors_price[:len(price_range_counts)], startangle=90, textprops={'fontsize': 12})
plt.title('北京酒店价格区间占比', fontsize=18, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('hotel_6_价格区间占比.png', dpi=150, bbox_inches='tight')
plt.show()

# 7. 评分与价格散点图
fig7 = plt.figure(figsize=(12, 8))
scatter = plt.scatter(df['评分_数值'], df['价格_数值'], c=df['点评数量_数值'],
                      cmap='YlOrRd', s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
plt.xlabel('评分', fontsize=13)
plt.ylabel('价格 (元/晚)', fontsize=13)
plt.title('酒店评分 vs 价格 (点大小=点评数量)', fontsize=18, fontweight='bold', pad=20)
cbar = plt.colorbar(scatter)
cbar.set_label('点评数量', fontsize=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('hotel_7_评分价格关系.png', dpi=150, bbox_inches='tight')
plt.show()

# 8. 各星级平均价格对比（柱状图）
fig8 = plt.figure(figsize=(10, 8))
star_price = df[df['星级_数值'].notna() & (df['价格_数值'] > 0)].groupby('星级_数值')['价格_数值'].mean().sort_index()
bars = plt.bar(star_price.index, star_price.values,
               color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'][:len(star_price)])
plt.xlabel('星级', fontsize=13)
plt.ylabel('平均价格 (元/晚)', fontsize=13)
plt.title('各星级酒店平均价格对比', fontsize=18, fontweight='bold', pad=20)
for i, v in enumerate(star_price.values):
    plt.text(i + 0.8, v + 5, f'{v:.0f}元', ha='center', fontsize=11)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('hotel_8_星级均价对比.png', dpi=150, bbox_inches='tight')
plt.show()

# 9. 评分等级分布（饼图）
fig9 = plt.figure(figsize=(10, 8))
score_level_counts = df['评分等级'].value_counts()
colors_level = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
plt.pie(score_level_counts.values, labels=score_level_counts.index, autopct='%1.1f%%',
        colors=colors_level[:len(score_level_counts)], startangle=90, textprops={'fontsize': 12})
plt.title('酒店评分等级分布', fontsize=18, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('hotel_9_评分等级分布.png', dpi=150, bbox_inches='tight')
plt.show()

# 输出统计信息
print("\n" + "=" * 60)
print("📊 北京酒店数据统计摘要")
print("=" * 60)
print(f"总酒店数: {len(df)}")
print(f"平均星级: {df['星级_数值'].mean():.2f}星")
print(f"平均评分: {df['评分_数值'].mean():.2f}/5.0")
print(f"平均价格: {df[df['价格_数值'] > 0]['价格_数值'].mean():.0f}元/晚")
print(f"中位数价格: {df[df['价格_数值'] > 0]['价格_数值'].median():.0f}元/晚")
print(f"最贵酒店: {df.loc[df['价格_数值'].idxmax(), '酒店名称']} ({df['价格_数值'].max()}元)")
print(f"评分最高: {df.loc[df['评分_数值'].idxmax(), '酒店名称']} ({df['评分_数值'].max():.1f}分)")
print(f"点评最多: {df.loc[df['点评数量_数值'].idxmax(), '酒店名称']} ({df['点评数量_数值'].max():.0f}条)")
print(f"酒店最多的区域: {region_counts.index[0]} ({region_counts.values[0]}家)")

print("\n✅ 所有图表已保存:")
print("   hotel_1_星级分布.png")
print("   hotel_2_评分分布.png")
print("   hotel_3_评分TOP15.png")
print("   hotel_4_价格分布.png")
print("   hotel_5_区域酒店数量.png")
print("   hotel_6_价格区间占比.png")
print("   hotel_7_评分价格关系.png")
print("   hotel_8_星级均价对比.png")
print("   hotel_9_评分等级分布.png")