"""
엑셀 한 행(row) -> 커머스API 상품 등록 요청 바디(JSON) 변환.

참고: 이 스키마는 네이버 커머스API 공식 문서(apicenter.commerce.naver.com) 및
공식 기술지원 GitHub(commerce-api-naver/commerce-api)의 공개 예시를 바탕으로 구성했다.
카테고리별로 필수 항목(예: 전자제품 인증정보, 원산지 등)이 추가로 요구될 수 있으므로,
반드시 실제 계정으로 상품 1건을 먼저 테스트 등록해보고 API가 돌려주는 에러 메시지에 맞춰
detail_attribute 항목을 보강할 것.
"""
import naver_config as config


def build_option_info(option_name: str, option_values: list[str], base_stock: int):
    """단일 옵션 항목(예: 색상)만 지원하는 조합형 옵션 빌더."""
    if not option_name or not option_values:
        return None

    combinations = []
    for value in option_values:
        combinations.append(
            {
                # 신규 등록 시 id는 지정하지 않음 (네이버가 자동 채번; 수정 API에서만 기존 id 사용)
                "optionName1": value,
                "stockQuantity": base_stock,
                "price": 0,  # 옵션별 추가금액 없음. 있으면 여기에 입력
                "usable": True,
            }
        )

    return {
        "optionCombinationGroupNames": {"optionGroupName1": option_name},
        "optionCombinations": combinations,
    }


def build_product_payload(row: dict, image_urls: dict) -> dict:
    """
    row: 엑셀 한 행을 dict로 읽은 값
        (영문상품명, 한글상품명, leafCategoryId, 판매가, 할인가, 옵션명, 옵션값(콤마구분),
         재고수량, 배송비타입, 배송비금액, 상세페이지이미지_경로 등)
    image_urls: {"representative": "https://...", "optional": ["https://...", ...],
                 "detail": ["https://...", "https://...", ...]}  - image_uploader로 미리 업로드해서 얻은 URL.
                 "detail"은 상세페이지 폴더의 이미지들을 번호 순서대로 이어붙인 리스트.
    """
    eng_name = str(row["영문상품명"]).strip()
    kor_name = str(row["한글상품명"]).strip()
    full_name = f"{eng_name} / {kor_name}" if kor_name else eng_name

    sale_price = int(row["판매가"])
    discount_price = row.get("할인가")
    stock = int(row.get("재고수량", 0) or 0)

    delivery_fee_type = "FREE" if str(row.get("배송비타입", "")).strip() == "무료" else "PAID"
    base_fee = int(row.get("배송비금액") or 0) if delivery_fee_type == "PAID" else 0

    detail_urls = image_urls.get("detail", [])
    if isinstance(detail_urls, str):  # 하위호환: 단일 URL로 넘어온 경우
        detail_urls = [detail_urls] if detail_urls else []
    detail_content = "".join(f'<img src="{u}" style="width:860px;display:block;" />' for u in detail_urls)

    origin_product = {
        "statusType": "SALE",  # 등록 즉시 판매 시작. 검수 후 시작하려면 WAIT
        "saleType": "NEW",
        "leafCategoryId": str(row["leafCategoryId"]),
        "name": full_name,
        "images": {
            "representativeImage": {"url": image_urls["representative"]},
            "optionalImages": [{"url": u} for u in image_urls.get("optional", [])],
        },
        "detailContent": detail_content,
        "salePrice": sale_price,
        "stockQuantity": stock,
        "deliveryInfo": {
            "deliveryType": "DELIVERY",
            "deliveryAttributeType": "NORMAL",
            "deliveryCompany": config.DELIVERY_COMPANY,
            "deliveryBundleGroupUsable": True,
            "visitAddressId": config.SHIPPING_ADDRESS_ID,
            "deliveryFee": {
                "deliveryFeeType": delivery_fee_type,
                "baseFee": base_fee,
                "deliveryFeePayType": "PREPAY",
            },
            "claimDeliveryInfo": {
                "returnDeliveryFee": config.DEFAULT_RETURN_DELIVERY_FEE,
                "exchangeDeliveryFee": config.DEFAULT_EXCHANGE_DELIVERY_FEE,
                "shippingAddressId": config.SHIPPING_ADDRESS_ID,
                "returnAddressId": config.RETURN_ADDRESS_ID,
            },
        },
        "detailAttribute": {
            "minorPurchasable": config.MINOR_PURCHASABLE,
            "afterServiceInfo": {
                "afterServiceTelephoneNumber": config.AS_PHONE_NUMBER,
                "afterServiceGuideContent": config.AS_GUIDE_CONTENT,
            },
            "originAreaInfo": {
                "originAreaCode": config.ORIGIN_AREA_CODE,
                "importer": config.IMPORTER_NAME,
                "content": config.ORIGIN_COUNTRY_NAME,
            },
            "productInfoProvidedNotice": {
                "productInfoProvidedNoticeType": config.PRODUCT_INFO_NOTICE_TYPE,
                "officeAppliances": {
                    "itemName": kor_name or full_name,
                    "modelName": eng_name,
                    "certificationType": config.NOT_APPLICABLE_TEXT,
                    "ratedVoltage": config.NOT_APPLICABLE_TEXT,
                    "powerConsumption": config.NOT_APPLICABLE_TEXT,
                    "energyEfficiencyRating": config.NOT_APPLICABLE_TEXT,
                    "releaseDateText": config.NOT_APPLICABLE_TEXT,
                    "manufacturer": config.MANUFACTURER_NAME,
                    "size": config.NOT_APPLICABLE_TEXT,
                    "weight": config.NOT_APPLICABLE_TEXT,
                    "specification": config.NOT_APPLICABLE_TEXT,
                    "warrantyPolicy": config.WARRANTY_POLICY_TEXT,
                    "afterServiceDirector": config.AS_PHONE_NUMBER,
                },
            },
        },
    }

    if discount_price not in (None, "", 0):
        origin_product["customerBenefit"] = {
            "immediateDiscountPolicy": {
                "discountMethod": {
                    "value": sale_price - int(discount_price),
                    "unitType": "WON",
                }
            }
        }

    option_name = str(row.get("옵션명") or "").strip()
    option_values_raw = str(row.get("옵션값(콤마구분)") or "").strip()
    if option_name and option_values_raw:
        values = [v.strip() for v in option_values_raw.split(",") if v.strip()]
        option_info = build_option_info(option_name, values, stock)
        if option_info:
            origin_product["detailAttribute"]["optionInfo"] = option_info

    payload = {
        "originProduct": origin_product,
        "smartstoreChannelProduct": {
            "channelProductDisplayStatusType": "ON",
            "naverShoppingRegistration": True,
        },
    }
    return payload
