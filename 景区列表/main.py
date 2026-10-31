from playwright.sync_api import sync_playwright
import csv
import re
import os


def extract_scenic_spots(page):
    """提取当前页面所有景点卡片的信息"""
    spots_data = []
    cards = page.query_selector_all(".sightItemCard_box__2FUEj")

    for card in cards:
        spot = {}

        # 1. 景点名称
        name_el = card.query_selector(".titleModule_name__Li4Tv a")
        spot["景点名称"] = name_el.inner_text().strip() if name_el else ""

        # 2. 景点链接
        spot["景点链接"] = name_el.get_attribute("href") if name_el else ""
        if spot["景点链接"] and not spot["景点链接"].startswith("http"):
            spot["景点链接"] = "https://you.ctrip.com" + spot["景点链接"]

        # 3. 星级
        level_el = card.query_selector(".titleModule_level-text__lxAaP")
        spot["星级"] = level_el.inner_text().strip() if level_el else ""

        # 4. 图片链接
        img_el = card.query_selector(".coverModule_img__hdwzO")
        spot["图片链接"] = img_el.get_attribute("src") if img_el else ""

        # 5. 排行榜信息
        rank_el = card.query_selector(".rankInfoModule_rank_desc_text__QY4cm")
        spot["排行榜"] = rank_el.inner_text().strip() if rank_el else ""

        # 6. 特色标签（多个用|分隔）
        tag_els = card.query_selector_all(".rankInfoModule_tag_text__FCSHe")
        spot["特色标签"] = " | ".join([tag.inner_text().strip() for tag in tag_els]) if tag_els else ""

        # 7. 地址
        distance_els = card.query_selector_all(".distanceView_desc-text__jb8H9")
        spot["地址"] = distance_els[0].inner_text().strip() if distance_els else ""

        # 8. 距离信息
        spot["距离信息"] = distance_els[2].inner_text().strip() if len(distance_els) > 2 else ""

        # 9. 热度
        hot_el = card.query_selector(".style_score_text__BGUSa")
        spot["热度"] = hot_el.inner_text().strip() if hot_el else ""

        # 10. 评分
        score_el = card.query_selector(".XReviewScoreV2_scoreText__l7KJA")
        if score_el:
            score_text = score_el.inner_text().strip()
            score_match = re.search(r"(\d+\.?\d*)", score_text)
            spot["评分"] = score_match.group(1) if score_match else score_text
        else:
            spot["评分"] = ""

        # 11. 点评数量
        review_el = card.query_selector(".XReviewScoreV2_countText__uumpj")
        spot["点评数量"] = review_el.inner_text().strip() if review_el else ""

        # 12. 其他标签（如：随买随用、可订今日等）
        other_tag_els = card.query_selector_all(".otherTagsModule_tag-text__VB8kU")
        spot["其他标签"] = " | ".join([tag.inner_text().strip() for tag in other_tag_els]) if other_tag_els else ""

        # 13. 市场价（原价）
        market_price_el = card.query_selector(".priceView_market-price-text__Sn9Na")
        spot["市场价"] = market_price_el.inner_text().strip() if market_price_el else ""

        # 14. 票价
        price_el = card.query_selector(".priceView_real-price-text__xmmuA")
        if price_el:
            price_text = price_el.inner_text().strip()
            price_match = re.search(r"¥(\d+)", price_text)
            spot["票价"] = price_match.group(1) if price_match else price_text
        else:
            spot["票价"] = ""

        # 15. 门票类型
        price_desc_el = card.query_selector(".priceView_price-desc-text__wDT0Q")
        spot["门票类型"] = price_desc_el.inner_text().strip() if price_desc_el else ""

        # 16. 价格后缀（如"起"）
        price_ext_el = card.query_selector(".priceView_price-ext-text__05aUo")
        spot["价格后缀"] = price_ext_el.inner_text().strip() if price_ext_el else ""

        if spot["景点名称"]:
            spots_data.append(spot)

    return spots_data


def save_to_csv(data, filename, is_first_page):
    """保存数据到CSV（每页追加）"""
    # 只保留10个核心字段
    fieldnames = [
        "景点名称", "景点链接", "星级", "图片链接", "排行榜",
        "特色标签", "地址", "距离信息", "热度", "评分"
    ]

    # 过滤数据，只保留这10个字段
    filtered_data = []
    for row in data:
        filtered_row = {field: row.get(field, "") for field in fieldnames}
        filtered_data.append(filtered_row)

    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_first_page:
            writer.writeheader()
        writer.writerows(filtered_data)


def go_to_next_page(page):
    """点击下一页"""
    try:
        next_button = page.query_selector(".ant-pagination-next:not(.ant-pagination-disabled)")
        if next_button:
            next_button.scroll_into_view_if_needed()
            next_button.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_selector(".sightItemCard_box__2FUEj", timeout=10000)
            return True
    except:
        pass
    return False


def get_total_pages(page):
    """获取总页数"""
    try:
        info_el = page.query_selector(".paginationBox_base-info-text__h5CSU")
        if info_el:
            info_text = info_el.inner_text().strip()
            match = re.search(r"/(\d+)条", info_text)
            if match:
                total_items = int(match.group(1))
                items_per_page = 300
                return (total_items + items_per_page - 1) // items_per_page
    except:
        pass
    return None


# 主程序
def main():
    filename = "beijing_scenic_spots.csv"

    # 如果是新运行，删除旧文件
    if os.path.exists(filename):
        os.remove(filename)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        url = "https://you.ctrip.com/sight/beijing1.html"
        page.goto(url, wait_until="networkidle")

        # 获取总页数
        total_pages = get_total_pages(page)
        if not total_pages:
            total_pages = 300

        current_page = 1
        is_first_page = True

        while True:
            # 抓取当前页
            spots = extract_scenic_spots(page)

            # 立即保存
            if spots:
                save_to_csv(spots, filename, is_first_page)
                is_first_page = False

            # 进度条
            progress = int(current_page / total_pages * 50)
            bar = "█" * progress + "░" * (50 - progress)
            print(f"\r进度: [{bar}] {current_page}/{total_pages}页 | 已保存{len(spots)}条", end="", flush=True)

            # 翻页
            if current_page >= total_pages or not go_to_next_page(page):
                break

            current_page += 1

        print(f"\n完成！数据已保存到 {filename}")
        browser.close()


if __name__ == "__main__":
    main()