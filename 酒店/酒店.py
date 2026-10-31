from playwright.sync_api import sync_playwright
import json
import csv
import re

def clean_text(text):
    """清理零宽连接符等特殊字符"""
    if not text:
        return text
    # 零宽连接符、零宽空格等
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u2064]', '', text)
    return text.strip()
import time
import random

def scrape_ctrip_reviews():
    all_reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
            ]
        )
        page = browser.new_page()

        # 隐藏自动化特征
        page.add_init_script('''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        ''')

        page.set_extra_http_headers({
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        })

        # 打开酒店页面
        page.goto('https://hotels.ctrip.com/hotels/detail/?&hotelId=128444132', wait_until='domcontentloaded')
        page.wait_for_timeout(3000)

        # 滚动到评论区并点击"展开更多"
        page.evaluate('window.scrollBy(0, 1500)')
        page.wait_for_timeout(1000)

        # 点击展开更多按钮
        more_button = page.locator('#review-swiper-show-more-button')
        if more_button.is_visible():
            more_button.click()
            print("已点击「展开更多」按钮")
            page.wait_for_timeout(2000)

        # 获取总页数
        pagination_info = page.evaluate('''() => {
            const pagination = document.querySelector('[class*="E7ufy5rNpuXnxgcwkjPa"]');
            if (!pagination) return null;
            const totalPages = pagination.querySelectorAll('[class*="Gntq2ON8Z1hf4AG2HMEB"]');
            const lastPage = totalPages.length > 0 ? totalPages[totalPages.length - 1].textContent.trim() : '1';
            return { totalPages: lastPage };
        }''')

        total_pages = int(pagination_info.get('totalPages', 1)) if pagination_info else 1
        print(f"共 {total_pages} 页评论")

        # 逐页提取
        for page_num in range(1, total_pages + 1):
            print(f"正在提取第 {page_num}/{total_pages} 页...")

            # 滚动加载当前页评论
            for _ in range(3):
                page.evaluate('window.scrollBy(0, 500)')
                page.wait_for_timeout(300)

            # 提取当前页评论
            reviews = page.evaluate('''() => {
                const results = [];
                const reviewCards = document.querySelectorAll('[class*="yRvZgc0SICPUbmdb2L2a"]');

                reviewCards.forEach((card) => {
                    const exposureData = card.getAttribute('data-exposure');
                    let parsedData = {};
                    try {
                        parsedData = JSON.parse(exposureData);
                    } catch (e) {}

                    const nicknameEl = card.querySelector('[class*="yCIHzFRsP6Tzk7Kia6Qo"]');
                    const nickname = nicknameEl ? nicknameEl.textContent.trim() : '';

                    const profilePicEl = card.querySelector('[class*="SVyrUbD88WrRWQkJHPWy"]');
                    const profilePicture = profilePicEl ? profilePicEl.src : '';

                    const infoItems = card.querySelectorAll('[class*="wl5HTVzzG2JXWejYiabW"] [class*="j_xXWYpWQ4P7mGIuGZEB"]');
                    let roomType = '', checkInDate = '', tripType = '', reviewCount = '';

                    infoItems.forEach((item) => {
                        const text = item.textContent.trim();
                        if (text.includes('房')) roomType = text;
                        else if (text.includes('入住')) checkInDate = text;
                        else if (text.includes('商务') || text.includes('朋友') || text.includes('家庭') || text.includes('独自') || text.includes('其他')) tripType = text;
                        else if (text.includes('点评')) reviewCount = text;
                    });

                    const scoreEl = card.querySelector('[class*="xt_R_A70sdDRsOgExJWw"]');
                    const rating = scoreEl ? scoreEl.textContent.trim() : '';

                    const labelEl = card.querySelector('[class*="xfkD5CyQbxDVVuKdQx6j"]');
                    const ratingLabel = labelEl ? labelEl.textContent.trim() : '';

                    const reviewTextEl = card.querySelector('[class*="tpHRPkB7n9UV_c7A5t6h"]');
                    let reviewText = '';
                    if (reviewTextEl) {
                        const expandBtn = reviewTextEl.querySelector('[class*="HZpWkZ8gHOiS0x9ZZ6cw"]');
                        if (expandBtn) {
                            reviewText = reviewTextEl.cloneNode(true);
                            const expandClone = reviewText.querySelector('[class*="HZpWkZ8gHOiS0x9ZZ6cw"]');
                            if (expandClone) expandClone.remove();
                            reviewText = reviewText.textContent.trim();
                        } else {
                            reviewText = reviewTextEl.textContent.trim();
                        }
                    }

                    const imageEls = card.querySelectorAll('[class*="eSfatCsIus864IS2fpfv"] [class*="Mc2J9dR5FXPKwZWzJDhK"] img');
                    const images = [];
                    imageEls.forEach((img) => {
                        if (img.src && !img.src.includes('data:image')) {
                            images.push(img.src);
                        }
                    });

                    const replyEl = card.querySelector('[class*="qUERH0dj6c94FltfokWY"]');
                    let hotelReply = '';
                    if (replyEl) {
                        const replyTextEl = replyEl.querySelector('span:last-child');
                        if (replyTextEl) hotelReply = replyTextEl.textContent.trim();
                    }

                    const postDateEl = card.querySelector('[class*="nUgIw0PM47FsRYfjswPo"]');
                    const postDate = postDateEl ? postDateEl.textContent.trim() : '';

                    const usefulEl = card.querySelector('[class*="R2PtKOhg5Hv1NoCOrAqx"]');
                    const usefulVote = usefulEl ? usefulEl.textContent.trim() : '';

                    results.push({
                        nickname,
                        profilePicture,
                        roomType,
                        checkInDate,
                        tripType,
                        reviewCount,
                        rating,
                        ratingLabel,
                        reviewText,
                        images,
                        hotelReply,
                        postDate,
                        usefulVote,
                        writingId: parsedData.data?.writingid || '',
                        masterHotelId: parsedData.data?.masterhotelid || ''
                    });
                });

                return results;
            }''')

            # 清理数据中的特殊字符
            for review in reviews:
                review['nickname'] = clean_text(review.get('nickname', ''))
                review['hotelReply'] = clean_text(review.get('hotelReply', ''))
                review['reviewText'] = clean_text(review.get('reviewText', ''))

            all_reviews.extend(reviews)
            print(f"  已提取 {len(reviews)} 条评论，累计 {len(all_reviews)} 条")

            # 每页保存一次
            csv_file = 'reviews_output.csv'
            fieldnames = ['nickname', 'profilePicture', 'roomType', 'checkInDate', 'tripType',
                          'reviewCount', 'rating', 'ratingLabel', 'reviewText', 'images',
                          'hotelReply', 'postDate', 'usefulVote', 'writingId', 'masterHotelId']

            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for review in all_reviews:
                    row = review.copy()
                    row['images'] = '|'.join(review.get('images', []))
                    writer.writerow(row)

            print(f"  [已保存] {csv_file}")

            # 检测是否跳转到登录页
            if 'login' in page.url.lower() or 'passport' in page.url.lower():
                print("检测到登录页面，保存当前数据并退出")
                break

            # 点击下一页（如果不是最后一页）
            if page_num < total_pages:
                # 滚动到页码区
                page.evaluate('window.scrollBy(0, 2000)')
                page.wait_for_timeout(500)

                # 点击下一页按钮
                next_button = page.locator('[class*="E7ufy5rNpuXnxgcwkjPa"] [class*="KtjTmkGBZvROMSO8zK_Q"]').last
                if next_button.is_visible():
                    next_button.click()
                    print(f"  已点击下一页按钮")
                    # 随机延时，避免被检测
                    time.sleep(random.uniform(1.5, 3.0))
                else:
                    # 尝试直接点击页码2
                    page_buttons = page.locator('[class*="E7ufy5rNpuXnxgcwkjPa"] [class*="Gntq2ON8Z1hf4AG2HMEB"]')
                    if page_buttons.count() > 1:
                        page_buttons.nth(1).click()
                        print(f"  已点击第2页")
                        time.sleep(random.uniform(1.5, 3.0))
                    else:
                        print("  未找到下一页按钮，尝试刷新...")
                        page.reload()
                        page.wait_for_timeout(2000)

        print(f"\n共提取 {len(all_reviews)} 条评论")

        browser.close()

if __name__ == '__main__':
    scrape_ctrip_reviews()
