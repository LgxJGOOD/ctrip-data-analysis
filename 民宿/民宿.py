from playwright.sync_api import sync_playwright
import csv
import time
import re
import os


def load_cookies_from_file(file_path='cookies.txt'):
    """从cookies.txt读取cookie字符串并解析"""
    with open(file_path, 'r', encoding='utf-8') as f:
        cookie_str = f.read().strip()

    cookies = []
    for item in cookie_str.split('; '):
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.ctrip.com',
                'path': '/'
            })
    return cookies


def parse_hotel_card(card):
    """解析单个酒店卡片HTML"""
    try:
        # 酒店ID
        hotel_id = card.get_attribute('id') or ''

        # 酒店名称
        name_elem = card.query_selector('.hotelName')
        name = name_elem.inner_text().strip() if name_elem else ''

        # 星级
        star = ''
        star_elems = card.query_selector_all('.star-icon')
        if star_elems:
            star = str(len(star_elems))

        # 评分
        score_elem = card.query_selector('.score')
        score = score_elem.inner_text().strip() if score_elem else ''

        # 评论数
        comment_elem = card.query_selector('.comment-num')
        comment = comment_elem.inner_text().strip() if comment_elem else ''
        comment = re.sub(r'[^0-9]', '', comment)

        # 评价标签
        tag_elem = card.query_selector('.one-sentence-tag')
        tag = tag_elem.inner_text().strip() if tag_elem else ''

        # 地址
        pos_elem = card.query_selector('.position-desc')
        address = pos_elem.inner_text().strip() if pos_elem else ''

        # 房型
        room_elem = card.query_selector('.room-name')
        room_name = room_elem.inner_text().strip() if room_elem else ''

        # 原价
        delete_elem = card.query_selector('.delete')
        original_price = delete_elem.inner_text().strip().replace('¥', '') if delete_elem else ''

        # 现价
        sale_elem = card.query_selector('.sale')
        current_price = sale_elem.inner_text().strip().replace('¥', '') if sale_elem else ''

        # 优惠标签
        discount_tags = []
        tag_elems = card.query_selector_all('.promotion-tag')
        for t in tag_elems:
            discount_tags.append(t.inner_text().strip())
        discount = ';'.join(discount_tags)

        # 特色标签
        feature_tags = []
        feature_elems = card.query_selector_all('.hotel-tag-content')
        for t in feature_elems:
            text = t.inner_text().strip()
            if text and text not in discount_tags:
                feature_tags.append(text)
        features = ';'.join(feature_tags)

        # 图片
        img_elem = card.query_selector('.m-lazyImg__img')
        img_url = img_elem.get_attribute('src') if img_elem else ''

        return {
            '酒店ID': hotel_id,
            '酒店名称': name,
            '星级': star,
            '评分': score,
            '评论数': comment,
            '评价标签': tag,
            '地址': address,
            '房型': room_name,
            '原价': original_price,
            '现价': current_price,
            '优惠': discount,
            '特色': features,
            '图片': img_url
        }
    except Exception as e:
        return None


def save_hotel_to_csv(hotel_data, filename='hotels.csv', fieldnames=None):
    """实时保存单条数据到CSV（追加模式）"""
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(hotel_data)


def load_existing_ids(filename='hotels.csv'):
    """加载已保存的酒店ID，用于去重"""
    existing_ids = set()
    if os.path.isfile(filename):
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('酒店ID'):
                    existing_ids.add(row['酒店ID'])
    return existing_ids


def scroll_and_collect():
    filename = 'hotels.csv'

    # 加载已存在的ID（断点续爬）
    existing_ids = load_existing_ids(filename)
    print(f"已存在 {len(existing_ids)} 条数据")

    all_hotels = []
    hotel_ids = existing_ids.copy()
    new_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 加载cookie
        cookies = load_cookies_from_file('cookies.txt')
        print(f"加载了 {len(cookies)} 个cookie")
        context.add_cookies(cookies)

        page = context.new_page()

        # 注入反检测
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

        # 访问页面
        url = "https://hotels.ctrip.com/hotels/list?flexType=1&fixedDate=0&cityId=213&provinceId=15&countryId=1&cityName=%E5%B8%B8%E5%B7%9E&destName=%E5%B8%B8%E5%B7%9E&searchType=CT&checkin=2026-06-22&checkout=2026-06-23&crn=1&listFilters=29~1*29*1~2*2%2C17~1*17*1%2C75~TAG_510*75*510%2C80~2*80*2&curr=CNY&locale=zh-CN&old=1"

        print("正在打开页面...")
        page.goto(url, wait_until='networkidle')

        # 等待卡片加载
        print("等待酒店卡片加载...")
        try:
            page.wait_for_selector('.hotel-card', timeout=15000)
        except:
            print("等待超时，尝试继续...")

        time.sleep(3)

        # 滚动收集
        print("开始滚动收集...")
        last_count = len(all_hotels)
        no_new_count = 0

        while no_new_count < 20:
            # 滚动到底部
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(2)

            # 获取当前所有卡片
            cards = page.query_selector_all('.hotel-card')

            # 解析新卡片
            for card in cards:
                hotel_id = card.get_attribute('id') or ''
                if hotel_id and hotel_id not in hotel_ids:
                    hotel_ids.add(hotel_id)
                    data = parse_hotel_card(card)
                    if data:
                        all_hotels.append(data)
                        new_count += 1
                        # 实时保存到CSV
                        fieldnames = data.keys()
                        save_hotel_to_csv(data, filename, fieldnames)
                        print(f"  [{new_count}] {data['酒店名称']} ¥{data['现价']} {data['评分']}分 ✅ 已保存")

            current_count = len(all_hotels)
            if current_count > last_count:
                print(f"当前共 {current_count} 个酒店 (新增 {current_count - last_count})")
                last_count = current_count
                no_new_count = 0
            else:
                no_new_count += 1
                print(f"没有新数据，尝试 {no_new_count}/20")

            # 尝试点击加载更多按钮
            try:
                load_btn = page.query_selector('text=加载更多, text=查看更多, button:has-text("加载")')
                if load_btn and load_btn.is_visible():
                    load_btn.click()
                    print("点击了加载更多按钮")
                    time.sleep(1)
            except:
                pass

        print(f"\n✅ 完成！总共获取 {len(all_hotels)} 个新酒店")
        print(f"✅ 已保存到 {filename}")

        input("按回车键关闭浏览器...")
        browser.close()


if __name__ == "__main__":
    scroll_and_collect()