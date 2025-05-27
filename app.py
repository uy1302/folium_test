import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from math import radians, cos, sin, asin, sqrt
import time

st.set_page_config(layout="wide")

st.title("Platewise")

geolocator = Nominatim(user_agent="test_geocoder_1.0")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, error_wait_seconds=10.0, max_retries=2, swallow_exceptions=False)

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 
    return c * 1000 

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        if "latitude" not in df.columns or "longitude" not in df.columns:
             st.error(f"Lỗi: Tệp {file_path} thiếu cột 'latitude' hoặc 'longitude'.")
             return pd.DataFrame()
        df.dropna(subset=["latitude", "longitude"], inplace=True)

        expected_cols = {
            "rating": {"type": "numeric", "default": pd.NA},
            "review_count": {"type": "numeric", "default": 0},
            "category": {"type": "string", "default": "Unknown"},
            "opening_hours": {"type": "string", "default": "Unknown"},
            "price_range": {"type": "string", "default": "Unknown"}
        }

        for col, details in expected_cols.items():
            if col not in df.columns:
                df[col] = details["default"]
            else:
                if details["type"] == "numeric":
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if pd.isna(details["default"]):
                         pass 
                    else:
                         df[col] = df[col].fillna(details["default"])

                elif details["type"] == "string":
                    df[col] = df[col].fillna(details["default"]).astype(str) 

        core_cols = ["name", "address", "latitude", "longitude"]
        for col in core_cols:
             if col not in df.columns:
                 st.warning(f"Cột '{col}' không có trong tệp, có thể gây lỗi hiển thị.")
                 df[col] = "Missing" 

        final_cols = ["name", "address", "latitude", "longitude", "category", "rating", "review_count", "opening_hours", "price_range"]
        for col in final_cols:
            if col not in df.columns:
                 df[col] = expected_cols.get(col, {}).get("default", "Unknown") 
        return df[final_cols] 

    except FileNotFoundError:
        st.error(f"Lỗi: Không tìm thấy tệp dữ liệu tại {file_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        return pd.DataFrame()

data_file = "restaurantsHanoi_augmented.csv"
restaurants_df = load_data(data_file)

if restaurants_df.empty:
    st.warning("Không có dữ liệu nhà hàng để tải hoặc dữ liệu không hợp lệ.")
    st.stop() 

DEFAULT_LOCATION = [21.0285, 105.8542]
DEFAULT_ZOOM = 13

if "map_center" not in st.session_state:
    st.session_state["map_center"] = DEFAULT_LOCATION
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = DEFAULT_ZOOM
if "selected_location" not in st.session_state:
    st.session_state["selected_location"] = None
if "radius_meters" not in st.session_state:
    st.session_state["radius_meters"] = 500
if "nearby_restaurants" not in st.session_state:
     st.session_state["nearby_restaurants"] = pd.DataFrame() 

st.sidebar.header("Tìm kiếm và Lọc")

address_query = st.sidebar.text_input("Tìm kiếm địa chỉ/phố:", "")
search_button_clicked = st.sidebar.button("Tìm kiếm")

if search_button_clicked and address_query:
    try:
        location = geocode(address_query + ", Hanoi, Vietnam", timeout=10)
        if location:
            st.session_state["selected_location"] = [location.latitude, location.longitude]
            st.session_state["map_center"] = [location.latitude, location.longitude]
            st.session_state["map_zoom"] = 15
            st.sidebar.success(f"Tìm thấy: {location.address}")
            st.session_state["nearby_restaurants"] = pd.DataFrame()
            st.rerun() 
        else:
            st.sidebar.error("Không tìm thấy địa chỉ.")
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.sidebar.error(f"Lỗi Geocoding: {e}")
    except Exception as e:
        st.sidebar.error(f"Lỗi không xác định: {e}")

st.session_state["radius_meters"] = st.sidebar.slider(
    "Chọn bán kính (mét):",
    min_value=100,
    max_value=5000,
    value=st.session_state["radius_meters"],
    step=50
)
st.sidebar.write(f"Bán kính đã chọn: {st.session_state['radius_meters']}m")

st.sidebar.header("Lọc nâng cao")

if "category" in restaurants_df.columns:
    category_options = sorted(restaurants_df["category"].fillna("Unknown").unique())
else:
    category_options = ["Unknown"]

filter_category = st.sidebar.multiselect(
    "Loại hình nhà hàng:",
    options=category_options,
    default=[]
)

filter_rating = st.sidebar.slider(
    "Rating tối thiểu:",
    min_value=0.0,
    max_value=5.0,
    value=0.0, 
    step=0.1
)

if "price_range" in restaurants_df.columns:
     price_ranges = sorted([pr for pr in restaurants_df["price_range"].fillna("Unknown").unique() if pr != "Unknown"])
else:
     price_ranges = [] 

filter_price_range = st.sidebar.multiselect(
    "Khoảng giá:",
    options=price_ranges,
    default=[]
)

opening_hours_options = ["Sáng (6:00-11:00)", "Trưa (11:00-14:00)", "Chiều (14:00-17:00)", "Tối (17:00-22:00)", "Đêm (22:00-6:00)"]
filter_opening_hours = st.sidebar.multiselect(
    "Giờ mở cửa:",
    options=opening_hours_options,
    default=[]
)

filtered_restaurants_df = pd.DataFrame() 
nearby_df = pd.DataFrame() 

if st.session_state["selected_location"]:
    selected_lat, selected_lon = st.session_state["selected_location"]

    nearby_restaurants_list = []
    for index, row in restaurants_df.iterrows():
        if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
            dist = haversine(selected_lon, selected_lat, row["longitude"], row["latitude"])
            if dist <= st.session_state["radius_meters"]:
                nearby_restaurants_list.append(row)

    nearby_df = pd.DataFrame(nearby_restaurants_list)

    if not nearby_df.empty:
        temp_df = nearby_df.copy() 

        if filter_category and "category" in temp_df.columns:
            temp_df = temp_df[temp_df["category"].isin(filter_category)]

        if filter_rating > 0.0 and "rating" in temp_df.columns:
             temp_df["rating"] = pd.to_numeric(temp_df["rating"], errors='coerce')
             temp_df = temp_df[temp_df["rating"].notna() & (temp_df["rating"] >= filter_rating)]

        if filter_price_range and "price_range" in temp_df.columns:
            temp_df = temp_df[temp_df["price_range"].isin(filter_price_range)]

        if filter_opening_hours and "opening_hours" in temp_df.columns:
            filtered_by_hours_indices = []
            for index, row in temp_df.iterrows():
                hours_str = str(row["opening_hours"]).lower()
                include_row = False
                for period in filter_opening_hours:
                    period_lower = period.lower()
                    if ("sáng" in period_lower and ("sáng" in hours_str or "morning" in hours_str or any(t in hours_str for t in ["6:", "7:", "8:", "9:", "10:"]))):
                        include_row = True; break
                    elif ("trưa" in period_lower and ("trưa" in hours_str or "noon" in hours_str or any(t in hours_str for t in ["11:", "12:", "13:"]))):
                         include_row = True; break
                    elif ("chiều" in period_lower and ("chiều" in hours_str or "afternoon" in hours_str or any(t in hours_str for t in ["14:", "15:", "16:"]))):
                         include_row = True; break
                    elif ("tối" in period_lower and ("tối" in hours_str or "evening" in hours_str or any(t in hours_str for t in ["17:", "18:", "19:", "20:", "21:"]))):
                         include_row = True; break
                    elif ("đêm" in period_lower and ("đêm" in hours_str or "night" in hours_str or any(t in hours_str for t in ["22:", "23:", "0:", "1:", "2:"]))):
                         include_row = True; break
                if include_row:
                    filtered_by_hours_indices.append(index)

            temp_df = temp_df.loc[filtered_by_hours_indices]

        filtered_restaurants_df = temp_df
    else:
         filtered_restaurants_df = pd.DataFrame()

    st.session_state["nearby_restaurants"] = filtered_restaurants_df

m = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"], tiles="OpenStreetMap")

if st.session_state["selected_location"]:
    selected_lat, selected_lon = st.session_state["selected_location"]
    folium.Marker(
        location=[selected_lat, selected_lon],
        popup="Địa điểm tiềm năng",
        icon=folium.Icon(color="red", icon="pushpin")
    ).add_to(m)
    folium.Circle(
        location=[selected_lat, selected_lon],
        radius=st.session_state["radius_meters"],
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.1
    ).add_to(m)

    if "nearby_restaurants" in st.session_state and not st.session_state["nearby_restaurants"].empty:
        fg = folium.FeatureGroup(name="Nhà hàng lân cận (đã lọc)")
        for index, row in st.session_state["nearby_restaurants"].iterrows():
            popup_html = f"<b>{row.get('name', 'N/A')}</b><br>Địa chỉ: {row.get('address', 'N/A')}"
            category = row.get('category', 'Unknown')
            rating = row.get('rating') 
            price_range = row.get('price_range', 'Unknown')
            opening_hours = row.get('opening_hours', 'Unknown')

            if pd.notna(category) and category != "Unknown":
                popup_html += f"<br>Loại hình: {category}"
            if pd.notna(rating):
                popup_html += f"<br>Rating: {rating:.1f}" 
            if pd.notna(price_range) and price_range != "Unknown":
                popup_html += f"<br>Giá: {price_range}"
            if pd.notna(opening_hours) and opening_hours != "Unknown":
                 popup_html += f"<br>Giờ mở cửa: {opening_hours}"

            if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
                 folium.Marker(
                     location=[row["latitude"], row["longitude"]],
                     popup=folium.Popup(popup_html, max_width=300),
                     icon=folium.Icon(color="green", icon="cutlery", prefix="fa")
                 ).add_to(fg)
        fg.add_to(m)
        folium.LayerControl().add_to(m) 

st.write("Nhấp vào bản đồ để chọn địa điểm hoặc tìm kiếm địa chỉ.")
map_data = st_folium(m, center=st.session_state["map_center"], zoom=st.session_state["map_zoom"], width="100%", height=600, key="folium_map")

if map_data and map_data["last_clicked"]:
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]
    current_selection = st.session_state["selected_location"]

    if current_selection is None or \
       abs(current_selection[0] - clicked_lat) > 1e-5 or \
       abs(current_selection[1] - clicked_lon) > 1e-5:

        st.session_state["selected_location"] = [clicked_lat, clicked_lon]
        st.session_state["nearby_restaurants"] = pd.DataFrame()
        st.rerun() 

st.subheader("Các nhà hàng trong bán kính đã chọn (đã lọc)")
if st.session_state["selected_location"]:
    if "nearby_restaurants" in st.session_state and not st.session_state["nearby_restaurants"].empty:
        display_cols = ["name", "address", "category", "rating", "price_range", "opening_hours"]
        cols_to_show = [col for col in display_cols if col in st.session_state["nearby_restaurants"].columns]
        st.dataframe(st.session_state["nearby_restaurants"][cols_to_show].reset_index(drop=True))
    elif not nearby_df.empty and filtered_restaurants_df.empty:
         st.info("Không tìm thấy nhà hàng nào phù hợp với bộ lọc đã chọn trong bán kính này.")
    else:
        st.info("Không tìm thấy nhà hàng nào trong bán kính này hoặc chưa chọn địa điểm.")
else:
    st.info("Vui lòng chọn một địa điểm trên bản đồ hoặc tìm kiếm địa chỉ.")


st.header("Quiz gợi ý địa điểm phù hợp")
st.write("Trả lời các câu hỏi dưới đây để nhận gợi ý về địa điểm phù hợp để mở nhà hàng mới.")

with st.expander("Bắt đầu Quiz", expanded=True):
    st.subheader("Thông tin cơ bản")

    q1_options = [
            "Ẩm thực Việt",
            "Ẩm thực Á (Nhật, Hàn, Trung, Thái...)",
            "Ẩm thực Âu (Ý, Pháp, Tây Ban Nha...)",
            "Đồ ăn nhanh/Quốc tế",
            "Quán cà phê/Trà sữa",
            "Quán ăn vặt/Đồ ngọt",
            "Nhà hàng chay",
            "Khác"
        ]
    q1 = st.selectbox(
        "1. Bạn muốn mở loại hình nhà hàng nào?",
        options=q1_options, index=0 
    )

    q2_options = [
            "Sinh viên",
            "Nhân viên văn phòng",
            "Gia đình",
            "Khách du lịch",
            "Người nước ngoài",
            "Nhóm bạn bè",
            "Khách doanh nghiệp"
        ]
    q2 = st.multiselect(
        "2. Đối tượng khách hàng mục tiêu của bạn là ai?",
        options=q2_options,
        default=["Nhân viên văn phòng"]
    )

    q3_options = ["Bình dân (< 100.000đ)", "Trung bình (100.000đ - 300.000đ)", "Cao cấp (> 300.000đ)"]
    q3 = st.select_slider(
        "3. Mức giá dự kiến của nhà hàng?",
        options=q3_options,
        value="Trung bình (100.000đ - 300.000đ)"
    )

    q4_options = [
            "Sáng (6:00-11:00)",
            "Trưa (11:00-14:00)",
            "Chiều (14:00-17:00)",
            "Tối (17:00-22:00)",
            "Đêm (22:00-6:00)"
        ]
    q4 = st.multiselect(
        "4. Thời gian hoạt động chính?",
        options=q4_options,
        default=["Trưa (11:00-14:00)", "Tối (17:00-22:00)"]
    )

    st.subheader("Yêu cầu về địa điểm")
    q5_options = [
            "Quận Ba Đình",
            "Quận Hoàn Kiếm",
            "Quận Hai Bà Trưng",
            "Quận Đống Đa",
            "Quận Tây Hồ",
            "Quận Cầu Giấy",
            "Quận Thanh Xuân",
            "Quận Hà Đông",
            "Quận Long Biên",
            "Quận Nam Từ Liêm",
            "Quận Bắc Từ Liêm",
            "Quận Hoàng Mai"
        ]
    q5 = st.multiselect(
        "5. Khu vực ưu tiên?",
        options=q5_options,
        default=["Quận Cầu Giấy", "Quận Đống Đa"]
    )

    q6_options = [
            "Trường học/Đại học",
            "Văn phòng/Tòa nhà thương mại",
            "Khu dân cư",
            "Trung tâm thương mại",
            "Điểm du lịch",
            "Công viên",
            "Bệnh viện"
        ]
    q6 = st.multiselect(
        "6. Bạn muốn gần các tiện ích nào?",
        options=q6_options,
        default=["Văn phòng/Tòa nhà thương mại"]
    )

    q7_options = [
            "Tránh khu vực có nhiều nhà hàng cùng loại",
            "Chọn khu vực tập trung nhiều nhà hàng để thu hút khách sẵn có",
            "Không quan trọng, tập trung vào chất lượng sản phẩm"
        ]
    q7 = st.radio(
        "7. Chiến lược cạnh tranh của bạn?",
        options=q7_options,
        index=0
    )

    q8_options = ["Nhỏ (< 50m²)", "Trung bình (50-150m²)", "Lớn (> 150m²)"]
    q8 = st.select_slider(
        "8. Diện tích mặt bằng cần thiết?",
        options=q8_options,
        value="Trung bình (50-150m²)"
    )

    q9_options = ["Thấp (< 500 triệu)", "Trung bình (500 triệu - 2 tỷ)", "Cao (> 2 tỷ)"]
    q9 = st.select_slider(
        "9. Ngân sách đầu tư?",
        options=q9_options,
        value="Trung bình (500 triệu - 2 tỷ)"
    )

    q10_options = [
            "Chỗ đậu xe",
            "Wifi miễn phí",
            "Không gian ngoài trời",
            "Phòng riêng/VIP",
            "Giao hàng",
            "Đặt chỗ trước",
            "Thanh toán không tiền mặt",
            "Nhạc sống/Giải trí"
        ]
    q10 = st.multiselect(
        "10. Tính năng bổ sung của nhà hàng?",
        options=q10_options,
        default=["Wifi miễn phí", "Giao hàng"]
    )

    if st.button("Nhận gợi ý địa điểm"):
        st.subheader("Gợi ý địa điểm (Tính năng đang phát triển)")
        st.info("Dựa trên câu trả lời của bạn, chúng tôi sẽ phân tích dữ liệu để đưa ra gợi ý khu vực phù hợp.")
        st.write("Lựa chọn của bạn:")
        st.write(f"- Loại hình: {q1}")
        st.write(f"- Khách hàng: {', '.join(q2)}")
        st.write(f"- Mức giá: {q3}")
        st.write(f"- Giờ hoạt động: {', '.join(q4)}")
        st.write(f"- Khu vực: {', '.join(q5)}")
        st.write(f"- Tiện ích lân cận: {', '.join(q6)}")
        st.write(f"- Cạnh tranh: {q7}")
        st.write(f"- Diện tích: {q8}")
        st.write(f"- Ngân sách: {q9}")
        st.write(f"- Tính năng: {', '.join(q10)}")

