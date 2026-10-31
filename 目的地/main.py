from playwright.sync_api import sync_playwright
import re
import csv
import time


def extract_comments_from_page(page):
    """提取当前页面的所有评论数据"""
    # 等待评论出现
    page.wait_for_selector(".commentItem", timeout=10000)

    comment_items = page.query_selector_all(".commentItem")
    page_comments = []

    for item in comment_items:
        # 用户名
        user_name_el = item.query_selector(".userName")
        user_name = user_name_el.inner_text() if user_name_el else ""

        # 评分
        score_el = item.query_selector(".averageScore")
        score_text = score_el.inner_text() if score_el else ""
        score_match = re.search(r"(\d+)", score_text)
        score = score_match.group(1) if score_match else ""

        # 评论内容
        detail_el = item.query_selector(".commentDetail")
        content = detail_el.inner_text() if detail_el else ""

        # IP属地
        ip_el = item.query_selector(".ipContent")
        ip_full = ip_el.inner_text() if ip_el else ""
        ip_match = re.search(r"IP属地[：:]\s*(.+)", ip_full)
        ip_location = ip_match.group(1) if ip_match else ""

        page_comments.append({
            "user_name": user_name,
            "score": score,
            "content": content,
            "ip_location": ip_location
        })

    return page_comments


def go_to_next_page(page):
    """点击下一页，如果存在且可用，返回True；否则返回False"""
    try:
        # 定位下一页按钮（class包含 ant-pagination-next 且没有 disabled 状态）
        next_button = page.query_selector(".ant-pagination-next:not(.ant-pagination-disabled)")

        if next_button:
            # 滚动到按钮位置确保可见
            next_button.scroll_into_view_if_needed()
            time.sleep(0.5)  # 短暂等待，防止点击过快
            next_button.click()

            # 等待页面加载完成（等待新的评论出现）
            page.wait_for_selector(".commentItem", timeout=10000)
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # 额外等待，确保数据加载完成

            return True
        else:
            return False
    except Exception as e:
        print(f"翻页失败: {e}")
        return False


# 主程序
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # 打开网页
    url = "https://you.ctrip.com/sight/jingdezhen405/110018.html"
    page.goto(url, wait_until="networkidle")
    time.sleep(2)  # 等待初始加载

    all_comments = []
    current_page = 1

    print(f"开始抓取第 {current_page} 页...")

    while True:
        # 提取当前页评论
        comments = extract_comments_from_page(page)
        all_comments.extend(comments)
        print(f"第 {current_page} 页: 抓取到 {len(comments)} 条评论 (累计: {len(all_comments)} 条)")

        # 尝试翻到下一页
        if go_to_next_page(page):
            current_page += 1
            print(f"正在翻到第 {current_page} 页...")
        else:
            print("已是最后一页，抓取完成！")
            break

    # 保存为CSV文件
    csv_filename = "jingdezhen_all_comments.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["user_name", "score", "content", "ip_location"])
        writer.writeheader()
        writer.writerows(all_comments)

    # 打印统计信息
    print("\n" + "=" * 50)
    print(f"抓取完成！")
    print(f"总页数: {current_page}")
    print(f"总评论数: {len(all_comments)}")
    print(f"数据已保存到: {csv_filename}")

    # 打印前3条样例
    print("\n前3条评论样例:")
    for idx, comment in enumerate(all_comments[:3], 1):
        print(f"\n{idx}. {comment['user_name']} | {comment['score']}分 | {comment['ip_location']}")
        print(f"   内容: {comment['content'][:80]}..." if len(
            comment['content']) > 80 else f"   内容: {comment['content']}")

    input("\n按回车关闭浏览器...")
    browser.close()