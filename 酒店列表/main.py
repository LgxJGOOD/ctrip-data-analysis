from playwright.sync_api import sync_playwright
import csv
import re
import time
import os


def load_cookies_from_txt(file_path):
    """读取 cookie.txt 中的标准 HTTP Cookie 字符串"""
    with open(file_path, 'r', encoding='utf-8') as f:
        cookie_str = f.read().strip()

    cookies = []
    for item in cookie_str.split(';'):
        item = item.strip()
        if not item or '=' not in item:
            continue
        equal_index = item.find('=')
        name = item[:equal_index]
        value = item[equal_index + 1:]
        cookies.append({
            'name': name,
            'value': value,
            'domain': '.ctrip.com',
            'path': '/',
        })
    return cookies


def extract_hotels(page):
    """提取当前页面所有酒店信息"""
    hotels = page.query_selector_all('.hotel-card')
    hotels_data = []

    for hotel in hotels:
        data = {}

        # 酒店名称
        name_el = hotel.query_selector('.hotelName')
        data['酒店名称'] = name_el.inner_text().strip() if name_el else ''

        # 星级（钻石图标数量）
        star_icons = hotel.query_selector_all('.star-icon')
        data['星级'] = len(star_icons) if star_icons else ''

        # 评分
        score_el = hotel.query_selector('.comment-score .score')
        data['评分'] = score_el.inner_text().strip() if score_el else ''

        # 点评数量
        comment_num_el = hotel.query_selector('.comment-num')
        if comment_num_el:
            comment_text = comment_num_el.inner_text().strip()
            num_match = re.search(r'(\d+)', comment_text)
            data['点评数量'] = num_match.group(1) if num_match else ''
        else:
            data['点评数量'] = ''

        # 一句话评价
        one_sentence_el = hotel.query_selector('.one-sentence-tag')
        data['一句话评价'] = one_sentence_el.inner_text().strip().strip('"') if one_sentence_el else ''

        # 位置区域
        position_el = hotel.query_selector('.position-desc')
        data['位置区域'] = position_el.inner_text().strip() if position_el else ''

        # 房型
        room_name_el = hotel.query_selector('.room-name')
        data['房型'] = room_name_el.inner_text().strip() if room_name_el else ''

        # 价格
        price_el = hotel.query_selector('.sale')
        if price_el:
            price_text = price_el.inner_text().strip()
            price_match = re.search(r'¥(\d+)', price_text)
            data['价格'] = price_match.group(1) if price_match else ''
        else:
            data['价格'] = ''

        # 标签（促销信息）
        tags = []
        tag_els = hotel.query_selector_all('.hotel-tag-content')
        for tag in tag_els:
            tag_text = tag.inner_text().strip()
            if tag_text:
                tags.append(tag_text)
        data['标签'] = ' | '.join(tags)

        if data['酒店名称']:
            hotels_data.append(data)

    return hotels_data


def scroll_and_load(page, max_scrolls=30):
    """
    滚动加载更多酒店
    返回: 是否还有更多内容
    """
    # 获取当前酒店数量
    before_count = len(page.query_selector_all('.hotel-card'))

    # 滚动到底部
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)  # 等待加载

    # 等待新内容出现
    try:
        page.wait_for_function(
            f"document.querySelectorAll('.hotel-card').length > {before_count}",
            timeout=5000
        )
        after_count = len(page.query_selector_all('.hotel-card'))
        print(f"  📍 滚动后: {before_count} → {after_count} (+{after_count - before_count})")
        return True
    except:
        # 超时说明没有新内容加载
        print("  📍 已滚动到底部，无更多酒店")
        return False


def save_to_csv(data, filename, is_first_page):
    """追加保存到CSV"""
    with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
        fieldnames = ['酒店名称', '星级', '评分', '点评数量', '一句话评价', '位置区域', '房型', '价格', '标签']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_first_page:
            writer.writeheader()
        writer.writerows(data)


def get_hotel_ids(page):
    """获取当前页面所有酒店ID（用于去重）"""
    hotel_cards = page.query_selector_all('.hotel-card')
    ids = []
    for card in hotel_cards:
        hotel_id = card.get_attribute('id')
        if hotel_id:
            ids.append(hotel_id)
    return set(ids)


def main():
    filename = 'beijing_hotels.csv'

    # 删除旧文件
    if os.path.exists(filename):
        os.remove(filename)

    url = "https://hotels.ctrip.com/hotels/list?countryId=1&city=1&provinceId=0&checkin=2026/06/13&checkout=2026/06/14&optionId=1&optionType=City&directSearch=0&display=%E5%8C%97%E4%BA%AC&crn=1&adult=1&children=0&searchBoxArg=t&travelPurpose=0&ctm_ref=ix_sb_dl&domestic=1"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # 加载 cookie
        try:
            cookies = load_cookies_from_txt('cookie.txt')
            if cookies:
                context.add_cookies(cookies)
                print(f"✅ 已加载 {len(cookies)} 个 Cookie")
        except Exception as e:
            print(f"⚠️ 加载 Cookie 失败: {e}")

        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        print(f"\n正在访问酒店列表页...")
        page.goto(url, wait_until="networkidle")
        time.sleep(3)

        # 等待酒店列表加载
        page.wait_for_selector('.hotel-card', timeout=15000)

        # 用于去重的酒店ID集合
        seen_hotel_ids = set()
        scroll_count = 0
        max_scrolls = 50  # 最大滚动次数
        no_new_count = 0  # 连续无新数据的次数

        print("\n开始滚动加载酒店数据...\n")

        while scroll_count < max_scrolls and no_new_count < 3:
            scroll_count += 1

            # 获取滚动前的酒店ID
            before_ids = get_hotel_ids(page)

            # 提取当前所有酒店
            hotels = extract_hotels(page)

            # 过滤新酒店（去重）
            new_hotels = []
            for hotel in hotels:
                # 用酒店名称作为去重依据（也可用其他字段）
                if hotel['酒店名称'] not in [h['酒店名称'] for h in new_hotels]:
                    new_hotels.append(hotel)

            # 保存新酒店
            if new_hotels:
                is_first = scroll_count == 1 and len(seen_hotel_ids) == 0
                save_to_csv(new_hotels, filename, is_first)
                seen_hotel_ids.update([h['酒店名称'] for h in new_hotels])

                # 进度条显示
                total = len(seen_hotel_ids)
                bar_len = 30
                progress = min(1.0, total / 200)  # 假设最多200家
                filled = int(bar_len * progress)
                bar = '█' * filled + '░' * (bar_len - filled)
                print(f"\r进度: [{bar}] 已加载 {total} 家酒店 (滚动 {scroll_count} 次)", end='', flush=True)
            else:
                print(f"\r⚠️ 滚动 {scroll_count} 次，无新酒店", end='', flush=True)

            # 滚动加载更多
            if not scroll_and_load(page):
                no_new_count += 1
            else:
                no_new_count = 0

            # 检查是否还有"加载更多"按钮（某些页面有）
            load_more_btn = page.query_selector('button:has-text("加载更多")')
            if load_more_btn and load_more_btn.is_visible():
                load_more_btn.click()
                time.sleep(2)

        total_hotels = len(seen_hotel_ids)
        print(f"\n\n✅ 抓取完成！共滚动 {scroll_count} 次，{total_hotels} 家酒店")
        print(f"📁 数据已保存到: {filename}")

        input("\n按回车关闭浏览器...")
        browser.close()


if __name__ == "__main__":
    main()