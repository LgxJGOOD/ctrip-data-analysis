import asyncio
from playwright.async_api import async_playwright
import csv
import os

URL = "https://you.ctrip.com/sight/beijing1/229.html"
CSV_FILE = "comments.csv"
TOTAL_PAGES = 300


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 初始化 CSV 文件
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
        with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["用户名", "评分", "内容", "图片链接", "IP属地", "发布时间", "点赞数"])

        headers = ["用户名", "评分", "内容", "图片链接", "IP属地", "发布时间", "点赞数"]

        for page_num in range(1, TOTAL_PAGES + 1):
            print(f"\r[页面 {page_num}/{TOTAL_PAGES}] 正在获取...", end="", flush=True)

            if page_num == 1:
                await page.goto(URL, wait_until="networkidle")
            else:
                next_btn = page.locator(".ant-pagination-next a")
                is_disabled = await next_btn.get_attribute("aria-disabled")
                if is_disabled == "true":
                    print("\n已到达最后一页")
                    break
                await next_btn.click()
                await page.wait_for_load_state("networkidle")

            await page.wait_for_selector(".commentItem", timeout=10000)

            comments = await page.evaluate("""() => {
                const items = document.querySelectorAll('.commentItem');
                const result = [];
                items.forEach(item => {
                    const userName = item.querySelector('.userName')?.innerText?.trim() || '';
                    const scoreText = item.querySelector('.averageScore')?.innerText?.trim() || '';
                    const scoreMatch = scoreText.match(/(\\d+)分/);
                    const rating = scoreMatch ? scoreMatch[1] : '';
                    const content = item.querySelector('.commentDetail')?.innerText?.trim() || '';
                    const imgs = Array.from(item.querySelectorAll('.commentImgList img')).map(img => img.src.replace('_D_', '_W_'));
                    const imgLinks = imgs.join(',');
                    const ipText = item.querySelector('.ipContent')?.innerText?.trim() || '';
                    const ipLocation = ipText.replace('IP属地：', '').replace('IP属地:', '').trim();
                    const timeElem = item.querySelector('.commentTime');
                    const timeText = timeElem?.innerText?.trim() || '';
                    const postTime = timeText.split('IP')[0].trim();
                    const votedIcon = item.querySelector('.votedIcon');
                    let likes = '0';
                    if (votedIcon) {
                        const parent = votedIcon.parentElement;
                        const parentText = parent?.innerText || '';
                        const likesMatch = parentText.match(/(\\d+)/);
                        likes = likesMatch ? likesMatch[1] : '0';
                    }
                    result.push([userName, rating, content, imgLinks, ipLocation, postTime, likes]);
                });
                return result;
            }""")

            # 边下载边存储
            with open(CSV_FILE, "a", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(comments)

            # 进度条
            progress = int(page_num / TOTAL_PAGES * 40)
            bar = "█" * progress + "░" * (40 - progress)
            print(f"\r[{bar}] {page_num}/{TOTAL_PAGES} 页，已获取 {len(comments)} 条评论", end="", flush=True)

        print(f"\n\n完成！评论已保存到 {CSV_FILE}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
