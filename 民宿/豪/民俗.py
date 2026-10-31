import json
import csv
import os
from glob import glob


def extract_hotel_data(json_data):
    """
    从携程酒店JSON数据中提取关键字段

    Args:
        json_data: 解析后的JSON数据

    Returns:
        list: 酒店数据列表，每个酒店为一个字典
    """
    hotels = []

    # 获取酒店列表
    hotel_list = json_data.get("data", {}).get("hotelList", [])

    for hotel in hotel_list:
        hotel_info = hotel.get("hotelInfo", {})
        room_info = hotel.get("roomInfo", [{}])[0]  # 取第一个房型

        # 提取基本信息
        summary = hotel_info.get("summary", {})
        name_info = hotel_info.get("nameInfo", {})
        position_info = hotel_info.get("positionInfo", {})
        comment_info = hotel_info.get("commentInfo", {})
        hotel_category = hotel_info.get("hotelCategory", {})
        hotel_star = hotel_info.get("hotelStar", {})
        hotel_tags = hotel_info.get("hotelTags", {})

        # 提取价格信息
        price_info = room_info.get("priceInfo", {})

        # 提取床型信息
        bed_info = room_info.get("bedInfo", {})
        bed_list = bed_info.get("contentList", [])
        bed_text = "、".join(bed_list) if bed_list else ""

        # 提取评分详情
        sub_scores = comment_info.get("subScore", [])
        score_dict = {}
        for score in sub_scores:
            score_type = score.get("content", "")
            score_value = score.get("number", "")
            if score_type:
                score_dict[f"{score_type}分"] = score_value

        # 提取一句话点评
        one_sentence = comment_info.get("oneSentenceComment", [])
        comment_tag = one_sentence[0].get("tagTitle", "") if one_sentence else ""

        # 提取促销标签
        promotion_tags = room_info.get("roomTags", {}).get("promotionTags", [])
        promotion_list = [tag.get("tagTitle", "") for tag in promotion_tags]

        # 提取优势标签
        advantage_tags = room_info.get("roomTags", {}).get("advantageTags", [])
        advantage_list = [tag.get("tagTitle", "") for tag in advantage_tags]

        # 构建单条酒店数据
        hotel_data = {
            "酒店ID": summary.get("hotelId", ""),
            "酒店名称": name_info.get("name", ""),
            "英文名称": name_info.get("enName", ""),
            "酒店类型": hotel_category.get("categoryName", ""),
            "星级": hotel_star.get("star", ""),
            "评分": comment_info.get("commentScore", ""),
            "评分描述": comment_info.get("commentDescription", ""),
            "点评数": comment_info.get("commenterNumber", ""),
            "一句话点评": comment_tag,
            "地址": position_info.get("address", ""),
            "位置描述": position_info.get("positionDesc", ""),
            "城市ID": position_info.get("cityId", ""),
            "城市名称": position_info.get("cityName", ""),
            "商圈": "、".join(position_info.get("zoneNames", [])),
            "纬度": position_info.get("mapCoordinate", [{}])[0].get("latitude", ""),
            "经度": position_info.get("mapCoordinate", [{}])[0].get("longitude", ""),
            "房型名称": room_info.get("summary", {}).get("saleRoomName", ""),
            "床型": bed_text,
            "价格": price_info.get("price", ""),
            "显示价格": price_info.get("displayPrice", ""),
            "原价": price_info.get("deletePrice", ""),
            "原价显示": price_info.get("deleteDisplayPrice", ""),
            "价格后缀": price_info.get("afterPriceText", ""),
            "支付类型": room_info.get("payInfo", {}).get("payType", ""),
            "可住人数": room_info.get("guestInfo", {}).get("adultCount", ""),
            "促销标签": "、".join(promotion_list),
            "优势标签": "、".join(advantage_list),
            "是否优享会": "是" if hotel_tags.get("primeHotel") else "否",
        }

        # 添加评分详情
        for key, value in score_dict.items():
            hotel_data[key] = value

        hotels.append(hotel_data)

    return hotels


def process_json_files(json_folder=".", output_csv="hotels_data.csv"):
    """
    处理文件夹内所有JSON文件，合并导出为CSV

    Args:
        json_folder: JSON文件所在文件夹路径
        output_csv: 输出CSV文件名
    """
    # 查找所有JSON文件
    json_files = glob(os.path.join(json_folder, "*.json"))

    # 排除输出文件（如果有）
    json_files = [f for f in json_files if not f.endswith("hotels_data.json")]

    if not json_files:
        print(f"在 {json_folder} 中未找到JSON文件")
        return

    print(f"找到 {len(json_files)} 个JSON文件:")
    for f in json_files:
        print(f"  - {os.path.basename(f)}")

    all_hotels = []

    for json_file in json_files:
        print(f"\n正在处理: {os.path.basename(json_file)}")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            hotels = extract_hotel_data(data)
            all_hotels.extend(hotels)
            print(f"  提取了 {len(hotels)} 条酒店数据")
        except Exception as e:
            print(f"  处理失败: {e}")

    if not all_hotels:
        print("\n未提取到任何数据")
        return

    print(f"\n总共提取了 {len(all_hotels)} 条酒店数据")

    # 获取所有字段名
    fieldnames = list(all_hotels[0].keys())

    # 写入CSV
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_hotels)

    print(f"\n数据已导出到: {output_csv}")

    # 显示前几条数据预览
    print("\n前5条数据预览:")
    for i, hotel in enumerate(all_hotels[:5]):
        print(f"  {i + 1}. {hotel.get('酒店名称', '')} - {hotel.get('价格', '')} - {hotel.get('评分', '')}分")


if __name__ == "__main__":
    # 使用说明
    print("=" * 60)
    print("携程酒店JSON数据合并工具")
    print("=" * 60)
    print("\n使用说明:")
    print("1. 将每个数据包保存为独立的JSON文件")
    print("2. 将所有JSON文件放在当前文件夹（或指定文件夹）")
    print("3. 运行此脚本，会自动合并所有JSON数据")
    print("4. 输出为 hotels_data.csv")
    print("=" * 60)

    # 运行处理
    # 如果你的JSON文件在子文件夹中，修改路径，例如: process_json_files("data_folder")
    process_json_files(".")