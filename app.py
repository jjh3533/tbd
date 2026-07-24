import math
import re
from bs4 import BeautifulSoup
import pandas as pd
from pyairtable import Api
import requests
import streamlit as st
import yfinance as yf

# ==========================================
# 1. 페이지 및 환경 설정
# ==========================================
st.set_page_config(
    page_title="TBD SEOUL 대시보드", page_icon="🚀", layout="wide"
)

AIRTABLE_API_TOKEN = "patGCAx3PVLC76hji.998b00597d0a3751e2151d0f1d1e6ef3f2c9790b0ff9686929d4b353cb24c418"
AIRTABLE_BASE_ID = "apphI9EUz746dP0Ye"
AIRTABLE_TABLE_NAME = "Products"

SCRAPERAPI_KEY = "643a1d003d0287a250d8cff2f6016159"

TELEGRAM_TOKEN = "8997002649:AAFku9xJ3fKAEq8yaqE8vQAlu8R34vqIwjw"
TELEGRAM_CHAT_ID = "7729393976"

api = Api(AIRTABLE_API_TOKEN)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)


# ==========================================
# 2. 백엔드 핵심 함수
# ==========================================
def get_current_exchange_rate():
    try:
        ticker = yf.Ticker("KRW=X")
        todays_data = ticker.history(period="1d")
        base_rate = todays_data["Close"].iloc[-1]
        return round(base_rate + 10, 1)
    except Exception:
        return 1380.0


def send_telegram_msg(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        st.error(f"텔레그램 발송 실패: {e}")


def fetch_amazon_info_via_scraperapi(asin):
    target_url = f"https://www.amazon.com/dp/{asin}"
    payload = {
        "api_key": SCRAPERAPI_KEY,
        "url": target_url,
        "country_code": "us",
        "keep_headers": "true",
    }

    try:
        res = requests.get(
            "http://api.scraperapi.com", params=payload, timeout=30
        )
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        amazon_usd = 0.0
        price_selectors = [
            "#corePriceDisplay_desktop_feature_div .a-offscreen",
            "#corePrice_feature_div .a-offscreen",
            "#apex_desktop .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            ".a-price .a-offscreen",
        ]

        for selector in price_selectors:
            elems = soup.select(selector)
            for elem in elems:
                price_text = elem.get_text().strip()
                clean_p = re.sub(r"[^\d.]", "", price_text)
                if clean_p:
                    try:
                        val = float(clean_p)
                        if 5.0 <= val <= 10000.0:
                            amazon_usd = val
                            break
                    except ValueError:
                        pass
            if amazon_usd > 0:
                break

        in_stock = True
        avail_elem = soup.select_one("#availability")
        if avail_elem:
            avail_text = avail_elem.get_text().lower()
            if (
                "currently unavailable" in avail_text
                or "out of stock" in avail_text
            ):
                in_stock = False

        weight_kg = None
        page_text = soup.get_text()
        weight_pattern = r"(?:Item|Package|Product)?\s*Weight\s*[:\n\t]*\s*([\d\.]+)\s*(pounds|lbs|ounces|oz|kg|g)"
        weight_match = re.search(weight_pattern, page_text, re.IGNORECASE)

        if weight_match:
            val = abs(float(weight_match.group(1)))
            unit = weight_match.group(2).lower()

            raw_weight = 0.0
            if unit in ["pounds", "lbs"]:
                raw_weight = val * 0.453592
            elif unit in ["ounces", "oz"]:
                raw_weight = val * 0.0283495
            elif unit == "kg":
                raw_weight = val
            elif unit == "g":
                raw_weight = val / 1000.0

            calc_weight = raw_weight + 0.5
            weight_kg = math.ceil(calc_weight * 2.0) / 2.0

        if weight_kg is None or weight_kg <= 0:
            weight_kg = 1.0

        return {
            "amazon_usd": amazon_usd,
            "in_stock": in_stock,
            "weight_kg": weight_kg,
        }

    except Exception:
        return None


def run_tbd_tracker(log_container):
    log_container.write("🚀 ScraperAPI 동기화 프로세스를 시작합니다...")
    current_rate = get_current_exchange_rate()
    log_container.write(f"💱 적용 환율: {current_rate}원")

    records = table.all()
    total_count = len(records)
    log_container.write(f"📦 에어테이블 레코드 {total_count}개 조회 완료")

    increased_count = 0
    decreased_count = 0
    out_of_stock_count = 0
    back_in_stock_count = 0

    detail_messages = []
    updated_count = 0

    for r in records:
        record_id = r["id"]
        fields = r["fields"]

        sku = fields.get("SKU", "무명 상품")
        asin = fields.get("ASIN")

        if not asin:
            continue

        prev_usd = fields.get("Amazon_USD", 0.0)
        prev_stock = fields.get("In_Stock", False)
        prev_weight = fields.get("Weight_KG")
        prev_rate = fields.get("Exchange_Rate")
        naver_id = fields.get("Naver_Product_No", "-")

        log_container.write(f"🔍 [{sku}] (ASIN: {asin}) 정보 수집 중...")
        amazon_data = fetch_amazon_info_via_scraperapi(asin)

        update_data = {}

        if prev_rate != current_rate:
            update_data["Exchange_Rate"] = current_rate

        if amazon_data:
            curr_usd = (
                amazon_data["amazon_usd"]
                if amazon_data["amazon_usd"] > 0
                else prev_usd
            )
            curr_stock = amazon_data["in_stock"]

            raw_w = (
                amazon_data["weight_kg"]
                if amazon_data["weight_kg"] is not None
                else (prev_weight or 1.0)
            )
            curr_weight = math.ceil(raw_w * 2.0) / 2.0

            if prev_usd != curr_usd:
                update_data["Amazon_USD"] = curr_usd
            if prev_stock != curr_stock:
                update_data["In_Stock"] = curr_stock
            if prev_weight != curr_weight:
                update_data["Weight_KG"] = curr_weight

            if update_data:
                table.update(record_id, update_data)
                updated_count += 1

                updated_record = table.get(record_id)
                new_calc_price = updated_record["fields"].get(
                    "Calculated_Price", 0
                )

                if prev_usd == 0.0 and curr_usd > 0:
                    detail_messages.append(
                        f"✨ **[신규 상품 등록]** *{sku}*\n• 아마존 원가: `${curr_usd}`\n• 추천"
                        f" 판매가: **`{new_calc_price:,}원`**"
                    )

                elif prev_stock != curr_stock:
                    if not curr_stock:
                        out_of_stock_count += 1
                        detail_messages.append(
                            f"🔴 **[품절 발생]** *{sku}*\n• 스마트스토어({naver_id})"
                            " **품절 처리** 필요"
                        )
                    else:
                        back_in_stock_count += 1
                        detail_messages.append(
                            f"🟢 **[재입고 완료]** *{sku}*\n• 추천 판매가:"
                            f" **`{new_calc_price:,}원`**"
                        )

                elif prev_usd != curr_usd and curr_stock:
                    if curr_usd > prev_usd:
                        increased_count += 1
                        direction = "📈 상승"
                    else:
                        decreased_count += 1
                        direction = "📉 하락"

                    detail_messages.append(
                        f"🔔 **[가격 변동 - {direction}]** *{sku}*\n"
                        f"• 아마존 원가: `${prev_usd}` ➡️ **`${curr_usd}`**\n"
                        f"• 추천 판매가: **`{new_calc_price:,}원`**"
                    )

                log_container.write(f"✅ 업데이트 완료: {sku}")
            else:
                log_container.write(f"ℹ️ 변동 사항 없음: {sku}")

    changed_total = (
        increased_count
        + decreased_count
        + out_of_stock_count
        + back_in_stock_count
    )

    summary_header = [
        "📊 **[TBD SEOUL] 웹 수동 동기화 리포트**",
        f"• **총 관리 상품**: {total_count}개",
        f"• **변동 상품**: {changed_total}개 (📈 상승 {increased_count} / 📉 하락"
        f" {decreased_count} / 🔴 품절 {out_of_stock_count} / 🟢 재입고"
        f" {back_in_stock_count})",
        "\n---",
    ]

    if detail_messages:
        final_msg = "\n\n".join(["\n".join(summary_header)] + detail_messages)
        final_msg += (
            "\n\n👉 [스마트스토어 수정"
            " 바로가기](https://sell.smartstore.naver.com/)"
        )
    else:
        final_msg = (
            "\n".join(summary_header)
            + "\n\n✨ 가격 및 재고 변동 사항이 없습니다."
        )

    send_telegram_msg(final_msg)
    log_container.write("🎉 동기화 리포트 발송 완료!")
    return updated_count


# ==========================================
# 3. Streamlit UI 구성
# ==========================================
st.title("🚀 TBD SEOUL 커머스 관리 대시보드")
st.caption("에어테이블 상품 관리, 신규 ASIN 등록 및 동기화 (ScraperAPI 엔진)")

current_rate = get_current_exchange_rate()
st.metric(label="현재 적용 환율 (KRW/USD)", value=f"{current_rate} 원")

st.divider()

tab1, tab2 = st.tabs(
    ["📦 Registered Products & Sync", "➕ Add New Item (신규 등록)"]
)

with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("등록된 상품 현황")
    with col2:
        if st.button(
            "🔄 지금 데이터 동기화 실행", type="primary", use_container_width=True
        ):
            with st.status("동기화 진행 중...", expanded=True) as status:
                count = run_tbd_tracker(status)
                status.update(
                    label=f"동기화 완료! ({count}개 변경됨)",
                    state="complete",
                    expanded=False,
                )
            st.success("에어테이블 및 텔레그램 알림 처리가 완료되었습니다.")
            st.rerun()

    records = table.all()
    if records:
        data_list = []
        for r in records:
            f = r["fields"]
            data_list.append({
                "SKU": f.get("SKU", "-"),
                "ASIN": f.get("ASIN", "-"),
                "Amazon USD ($)": f.get("Amazon_USD", 0.0),
                "In Stock": "🟢 재고있음" if f.get("In_Stock") else "🔴 품절",
                "Weight (kg)": f.get("Weight_KG", 0.0),
                "Shipping (KRW)": f.get("Shipping_KRW", 0),
                "Calculated Price (KRW)": f.get("Calculated_Price", 0),
                "Naver Product No": f.get("Naver_Product_No", "-"),
            })

        df = pd.DataFrame(data_list)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("현재 등록된 상품이 없습니다.")

with tab2:
    st.subheader("신규 트래킹 상품 추가")
    st.write(
        "SKU와 ASIN을 입력하시면, 동기화 실행 시 아마존에서 가격, 재고, 무게를"
        " 자동으로 가져옵니다."
    )

    with st.form("add_product_form", clear_on_submit=True):
        new_sku = st.text_input(
            "상품명 / SKU", placeholder="예: Ubiquiti UniFi Express 7"
        )
        new_asin = st.text_input(
            "아마존 ASIN", placeholder="예: B0CWLKD9RP (10자리 문자/숫자)"
        )
        new_naver_id = st.text_input(
            "네이버 스마트스토어 상품번호 (선택사항)",
            placeholder="예: 10293848",
        )

        submitted = st.form_submit_button("➕ 에어테이블에 신규 상품 등록")

        if submitted:
            if not new_sku or not new_asin:
                st.error("SKU와 ASIN은 필수 입력 항목입니다!")
            else:
                new_record_data = {
                    "SKU": new_sku.strip(),
                    "ASIN": new_asin.strip().upper(),
                    "Exchange_Rate": current_rate,
                }
                if new_naver_id:
                    new_record_data["Naver_Product_No"] = new_naver_id.strip()

                try:
                    table.create(new_record_data)
                    st.success(
                        f"🎉 [{new_sku}] 상품이 에어테이블에 성공적으로"
                        " 추가되었습니다!"
                    )
                    st.info(
                        "상단의 '🔄 지금 데이터 동기화 실행' 버튼을 누르면"
                        " 아마존에서 가격과 무게를 알아서 긁어옵니다."
                    )
                except Exception as e:
                    st.error(f"에어테이블 추가 중 오류 발생: {e}")
