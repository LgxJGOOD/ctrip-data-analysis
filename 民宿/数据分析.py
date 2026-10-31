import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
import os
import warnings
import numpy as np

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def load_data(filename='hotels.csv'):
    """加载CSV数据"""
    if not os.path.exists(filename):
        print(f"❌ 文件 {filename} 不存在！")
        return None

    df = pd.read_csv(filename, encoding='utf-8-sig')
    print(f"✅ 加载数据：{len(df)} 条记录")
    return df


def clean_data(df):
    """数据清洗和类型转换"""
    df_clean = df.copy()

    # 转换数值类型
    df_clean['评分'] = pd.to_numeric(df_clean['评分'], errors='coerce')
    df_clean['评论数'] = pd.to_numeric(df_clean['评论数'], errors='coerce')
    df_clean['现价'] = pd.to_numeric(df_clean['现价'], errors='coerce')
    df_clean['原价'] = pd.to_numeric(df_clean['原价'], errors='coerce')
    df_clean['星级'] = pd.to_numeric(df_clean['星级'], errors='coerce')

    # 计算折扣率
    df_clean['折扣率'] = (df_clean['现价'] / df_clean['原价'] * 100).round(1)

    # 删除空值
    df_clean = df_clean.dropna(subset=['酒店名称', '现价'])

    print(f"✅ 清洗后：{len(df_clean)} 条有效记录")
    return df_clean


def basic_stats(df):
    """基础统计分析"""
    print("\n" + "=" * 50)
    print("📊 基础统计分析")
    print("=" * 50)

    stats = {
        '酒店总数': len(df),
        '平均价格': f"¥{df['现价'].mean():.2f}",
        '最高价格': f"¥{df['现价'].max():.2f}",
        '最低价格': f"¥{df['现价'].min():.2f}",
        '平均评分': f"{df['评分'].mean():.2f}",
        '最高评分': f"{df['评分'].max():.2f}",
        '平均评论数': f"{df['评论数'].mean():.0f}条",
        '总评论数': f"{df['评论数'].sum():.0f}条",
    }

    for key, value in stats.items():
        print(f"{key}: {value}")

    return stats


def price_analysis(df):
    """价格分析图表"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. 价格分布直方图
    ax1 = axes[0, 0]
    df['现价'].hist(bins=30, edgecolor='black', ax=ax1, color='steelblue')
    ax1.set_title('酒店价格分布', fontsize=14, fontweight='bold')
    ax1.set_xlabel('价格 (¥)')
    ax1.set_ylabel('酒店数量')
    ax1.axvline(df['现价'].mean(), color='red', linestyle='--', label=f'均值: ¥{df["现价"].mean():.0f}')
    ax1.legend()

    # 2. 价格箱线图（按星级分组）
    ax2 = axes[0, 1]
    star_groups = df.groupby('星级')['现价'].apply(list).to_dict()
    star_labels = [f"{k}星" for k in sorted(star_groups.keys())]
    star_data = [star_groups[k] for k in sorted(star_groups.keys())]

    bp = ax2.boxplot(star_data, labels=star_labels, patch_artist=True)
    for box in bp['boxes']:
        box.set_facecolor('lightblue')
    ax2.set_title('各星级酒店价格分布', fontsize=14, fontweight='bold')
    ax2.set_xlabel('星级')
    ax2.set_ylabel('价格 (¥)')

    # 3. 价格-评分散点图
    ax3 = axes[1, 0]
    scatter = ax3.scatter(df['评分'], df['现价'],
                          c=df['星级'], cmap='viridis',
                          alpha=0.6, s=50)
    ax3.set_title('价格 vs 评分', fontsize=14, fontweight='bold')
    ax3.set_xlabel('评分')
    ax3.set_ylabel('价格 (¥)')
    plt.colorbar(scatter, ax=ax3, label='星级')

    # 4. 价格区间占比（饼图）
    ax4 = axes[1, 1]
    bins = [0, 100, 200, 300, 500, 1000, float('inf')]
    labels = ['<100', '100-200', '200-300', '300-500', '500-1000', '>1000']
    df['价格区间'] = pd.cut(df['现价'], bins=bins, labels=labels)
    price_counts = df['价格区间'].value_counts()
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(price_counts)))[::-1]
    ax4.pie(price_counts.values, labels=price_counts.index,
            autopct='%1.1f%%', colors=colors, startangle=90)
    ax4.set_title('价格区间占比', fontsize=14, fontweight='bold')

    plt.suptitle('酒店价格分析', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('price_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 价格分析图已保存: price_analysis.png")
    plt.show()


def rating_analysis(df):
    """评分分析图表"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 1. 评分分布
    ax1 = axes[0]
    rating_counts = df['评分'].value_counts().sort_index()
    ax1.bar(rating_counts.index, rating_counts.values, color='coral', edgecolor='black')
    ax1.set_title('评分分布', fontsize=14, fontweight='bold')
    ax1.set_xlabel('评分')
    ax1.set_ylabel('酒店数量')
    ax1.axvline(df['评分'].mean(), color='red', linestyle='--',
                label=f'均值: {df["评分"].mean():.2f}')
    ax1.legend()

    # 2. 评分-评论数关系
    ax2 = axes[1]
    ax2.scatter(df['评分'], df['评论数'], alpha=0.5, color='teal')
    ax2.set_title('评分 vs 评论数', fontsize=14, fontweight='bold')
    ax2.set_xlabel('评分')
    ax2.set_ylabel('评论数')

    # 3. 星级平均评分
    ax3 = axes[2]
    star_avg = df.groupby('星级')['评分'].mean().sort_index()
    ax3.bar(star_avg.index.astype(str) + '星', star_avg.values,
            color='gold', edgecolor='black')
    ax3.set_title('各星级平均评分', fontsize=14, fontweight='bold')
    ax3.set_xlabel('星级')
    ax3.set_ylabel('平均评分')
    for i, v in enumerate(star_avg.values):
        ax3.text(i, v + 0.05, f'{v:.2f}', ha='center', fontweight='bold')

    plt.suptitle('酒店评分分析', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('rating_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 评分分析图已保存: rating_analysis.png")
    plt.show()


def top_hotels(df):
    """TOP酒店排行"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 1. 价格最低的10家
    ax1 = axes[0]
    cheapest = df.nsmallest(10, '现价')[['酒店名称', '现价', '评分', '星级']]
    bars1 = ax1.barh(cheapest['酒店名称'].str[:12] + '...', cheapest['现价'],
                     color='lightgreen', edgecolor='black')
    ax1.set_title('最便宜的10家酒店', fontsize=14, fontweight='bold')
    ax1.set_xlabel('价格 (¥)')
    # 添加评分标签
    for i, (idx, row) in enumerate(cheapest.iterrows()):
        ax1.text(row['现价'] + 3, i, f"{row['评分']}星", va='center', fontsize=9)

    # 2. 评分最高的10家
    ax2 = axes[1]
    best = df.nlargest(10, '评分')[['酒店名称', '现价', '评分', '评论数']]
    bars2 = ax2.barh(best['酒店名称'].str[:12] + '...', best['评分'],
                     color='orange', edgecolor='black')
    ax2.set_title('评分最高的10家酒店', fontsize=14, fontweight='bold')
    ax2.set_xlabel('评分')
    # 添加价格标签
    for i, (idx, row) in enumerate(best.iterrows()):
        ax2.text(row['评分'] + 0.05, i, f"¥{row['现价']}", va='center', fontsize=9)

    plt.suptitle('酒店排行', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('top_hotels.png', dpi=300, bbox_inches='tight')
    print("✅ 排行图已保存: top_hotels.png")
    plt.show()


def correlation_analysis(df):
    """相关性热力图"""
    plt.figure(figsize=(10, 8))

    # 选择数值列
    numeric_cols = ['星级', '评分', '评论数', '现价', '原价', '折扣率']
    corr_data = df[numeric_cols].corr()

    # 绘制热力图
    mask = np.triu(np.ones_like(corr_data, dtype=bool))
    sns.heatmap(corr_data, annot=True, fmt='.2f', cmap='coolwarm',
                square=True, linewidths=0.5, mask=mask)

    plt.title('各指标相关性热力图', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('correlation.png', dpi=300, bbox_inches='tight')
    print("✅ 相关性热力图已保存: correlation.png")
    plt.show()


def export_summary(df):
    """导出统计摘要"""
    summary = {
        '指标': ['酒店总数', '平均价格', '最高价格', '最低价格',
                 '平均评分', '最高评分', '最低评分', '平均评论数'],
        '数值': [
            len(df),
            f"{df['现价'].mean():.2f}",
            f"{df['现价'].max():.2f}",
            f"{df['现价'].min():.2f}",
            f"{df['评分'].mean():.2f}",
            f"{df['评分'].max():.2f}",
            f"{df['评分'].min():.2f}",
            f"{df['评论数'].mean():.0f}"
        ]
    }
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv('hotels_summary.csv', index=False, encoding='utf-8-sig')
    print("✅ 统计摘要已保存: hotels_summary.csv")

    return summary_df


def print_top_recommendations(df):
    """打印推荐列表"""
    print("\n" + "=" * 50)
    print("🏆 性价比推荐 (评分>4.5 且 价格低于均值)")
    print("=" * 50)

    avg_price = df['现价'].mean()
    recommend = df[(df['评分'] > 4.5) & (df['现价'] < avg_price)]
    recommend = recommend.sort_values(['评分', '现价'], ascending=[False, True])

    if len(recommend) > 0:
        for i, row in recommend.head(10).iterrows():
            print(f"{row['酒店名称'][:20]:20} | 评分: {row['评分']} | ¥{row['现价']} | {row['星级']}星")
    else:
        print("没有符合条件的推荐")

    print("\n" + "=" * 50)
    print("💎 高分精选 (评分≥4.8)")
    print("=" * 50)
    high_score = df[df['评分'] >= 4.8].sort_values('评分', ascending=False)
    if len(high_score) > 0:
        for i, row in high_score.head(10).iterrows():
            print(f"{row['酒店名称'][:20]:20} | 评分: {row['评分']} | ¥{row['现价']} | {row['星级']}星")
    else:
        print("没有高分酒店")


def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("🏨 携程酒店数据分析系统")
    print("=" * 50)

    # 加载数据
    df = load_data('hotels.csv')
    if df is None or len(df) == 0:
        return

    # 清洗数据
    df_clean = clean_data(df)
    if len(df_clean) == 0:
        print("❌ 没有有效数据，请检查CSV文件")
        return

    # 基础统计
    stats = basic_stats(df_clean)

    # 导出统计摘要
    export_summary(df_clean)

    # 打印推荐
    print_top_recommendations(df_clean)

    # 可视化分析
    print("\n开始生成可视化图表...")
    price_analysis(df_clean)
    rating_analysis(df_clean)
    top_hotels(df_clean)
    correlation_analysis(df_clean)

    print("\n" + "=" * 50)
    print("✅ 分析完成！生成文件：")
    print("  - price_analysis.png (价格分析)")
    print("  - rating_analysis.png (评分分析)")
    print("  - top_hotels.png (酒店排行)")
    print("  - correlation.png (相关性热力图)")
    print("  - hotels_summary.csv (统计摘要)")
    print("=" * 50)


if __name__ == "__main__":
    main()