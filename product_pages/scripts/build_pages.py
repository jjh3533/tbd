"""배치 1: Pro Max 16 / Pro Max 16 PoE / Flex 10 GbE 상세페이지 생성.

기존 20개 .dc.html과 동일한 구조(공용 섹션은 그대로, 제품별 섹션만 교체)를
그대로 코드로 재현한다. 공용 섹션(TBD Seoul/통관/배송반품/FAQ/Footer)은
UCG Ultra 페이지에서 그대로 가져온 것과 100% 동일한 텍스트.
"""

# 브랜드별로 바뀌는 부분(헤더/히어로 로고, 트러스트·FAQ·푸터의 브랜드 표기)만
# 파라미터화. head()/trust_to_footer()/hero()는 이 값을 안 넘기면 기존 UniFi
# 문구와 100% 동일한 결과를 내도록 UNIFI_BRAND를 기본값으로 쓴다.
UNIFI_BRAND = {
    "header_logo_src": "assets/common/common_logo-supply.svg",
    "header_logo_alt": "Unifi Supply",
    "hero_logo_src": "assets/common/common_logo-symbol.svg",
    "hero_logo_alt": "UniFi",
    "hero_logo_height": "60px",
    "eyebrow_label": "UNIFI SUPPLY BY TBD SEOUL",
    "supply_label": "Unifi Supply",
    "product_name": "UniFi",  # 트러스트 헤드라인/재고 문구에 쓰는 제품 라인명
    "official_name": "Ubiquiti",  # 공식 채널/A/S 문구에 쓰는 제조사명
    "store_line": "Unifi Supply by TBD Seoul",
}

GLINET_BRAND = {
    "header_logo_src": "assets/common/common_logo-glinet.svg",
    "header_logo_alt": "GL.iNet",
    "hero_logo_src": "assets/common/common_logo-glinet.svg",
    "hero_logo_alt": "GL.iNet",
    "hero_logo_height": "22px",
    "eyebrow_label": "GL.INET SUPPLY BY TBD SEOUL",
    "supply_label": "GLiNET Supply",
    "product_name": "GL.iNet",
    "official_name": "GL.iNet",
    "store_line": "GLiNET Supply by TBD Seoul",
}

# /settings 페이지(common_settings.json)에서 브랜드 로고/문구를 코드 수정 없이
# 바꿀 수 있게 오버라이드를 병합한다. common_settings는 저장소 루트 모듈이라
# 이 스크립트를 product_pages/scripts/에서 단독 실행할 때는(sys.path에 루트가
# 없어) import가 실패할 수 있음 - 그 경우 조용히 기본값 그대로 사용한다
# (대시보드 프로세스에서는 app.py가 이미 루트를 sys.path에 넣어두므로 정상 로드됨).
try:
  import common_settings as _common_settings
  _settings = _common_settings.load()
  _brand_overrides = _settings.get("brands", {})
  _common_copy = _settings.get("common_copy", {})
except Exception:
  _brand_overrides = {}
  _common_copy = {}

UNIFI_BRAND = {**UNIFI_BRAND, **_brand_overrides.get("UniFi", {})}
GLINET_BRAND = {**GLINET_BRAND, **_brand_overrides.get("GL.inet", {})}

_RETURN_WINDOW_WEEKS = _common_copy.get("return_window_weeks", 2)
_DELIVERY_MIN_DAYS = _common_copy.get("delivery_min_days", 7)
_DELIVERY_MAX_DAYS = _common_copy.get("delivery_max_days", 14)


def head(brand=UNIFI_BRAND):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <script src="./image-slot.js"></script>
  <style>
    @font-face{{font-family:'UI Sans';src:url('assets/common/common_font-ui-sans-400.otf') format('opentype');font-weight:400;font-style:normal;}}
    @font-face{{font-family:'UI Sans';src:url('assets/common/common_font-ui-sans-500.otf') format('opentype');font-weight:500;font-style:normal;}}
    @font-face{{font-family:'UI Sans';src:url('assets/common/common_font-ui-sans-700.otf') format('opentype');font-weight:700;font-style:normal;}}
    @font-face{{font-family:'UI Sans';src:url('assets/common/common_font-ui-sans-900.otf') format('opentype');font-weight:900;font-style:normal;}}
    *{{box-sizing:border-box;word-break:keep-all;overflow-wrap:break-word;}}
    a{{color:#3371FB;}}
    a:hover{{color:#2452C3;}}
  </style>
</helmet>
<div style="background:#E8E8ED;display:flex;justify-content:center;padding:40px 0 120px;font-family:'UI Sans','Pretendard',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;color:#212326;">
<div style="width:860px;background:#ffffff;box-shadow:0 0 40px rgba(0,0,0,0.08);" data-screen-label="상세페이지">

  <div style="padding:22px 60px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #E4E4E9;" data-screen-label="Header">
    <div style="display:flex;align-items:center;gap:14px;">
      <img src="{brand['header_logo_src']}" alt="{brand['header_logo_alt']}" style="height:20px;width:auto;display:block;">
      <div style="width:1px;height:16px;background:#E4E4E9;"></div>
      <img src="assets/common/common_logo-tbd.svg" alt="TBD Seoul" style="height:14px;width:auto;display:block;opacity:0.75;">
    </div>
    <div style="font-size:12px;color:#57C76B;font-weight:500;border:1px solid rgba(87,199,107,0.3);background:rgba(87,199,107,0.08);border-radius:20px;padding:4px 12px;">해외직구 · 정식 유통</div>
  </div>
"""


HEAD = head()

_TRUST_TO_FOOTER_TEMPLATE = """
  <section style="padding:100px 60px;" data-screen-label="TBD Seoul">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">__EYEBROW__</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">__PRODUCT__ 전문 해외직구로<br>안심하고 구매하세요</h2>
    </div>
    <div style="display:flex;gap:20px;max-width:760px;margin:0 auto;">
      <div style="flex:1;padding:28px 24px;border-radius:16px;background:#fff;border:1px solid #E4E4E9;text-align:left;">
        <div style="width:36px;height:36px;border-radius:10px;background:#F5F4F7;display:flex;align-items:center;justify-content:center;margin-bottom:14px;font-size:16px;">✓</div>
        <h4 style="font-size:15.5px;font-weight:600;margin-bottom:6px;">정품 병행/직수입</h4>
        <p style="font-size:13.5px;color:#696F78;line-height:1.55;">미국의 __OFFICIAL__ 공식 채널을<br>통해 유통되는 정품만을 구매해<br>한국의 고객님께 보내드려요.</p>
      </div>
      <div style="flex:1;padding:28px 24px;border-radius:16px;background:#fff;border:1px solid #E4E4E9;text-align:left;">
        <div style="width:36px;height:36px;border-radius:10px;background:#F5F4F7;display:flex;align-items:center;justify-content:center;margin-bottom:14px;font-size:16px;">↻</div>
        <h4 style="font-size:15.5px;font-weight:600;margin-bottom:6px;">__RETURN_WEEKS__주 초기불량 전액 보장</h4>
        <p style="font-size:13.5px;color:#696F78;line-height:1.55;">구매 후 __RETURN_WEEKS__주 이내 초기불량은<br><b style="color: rgb(33, 35, 38);">TBD Seoul이 전액 부담</b>하여 처리합니다. 왕복 배송비, 진단, 교환<br>까지 별도 비용이 없습니다.</p>
      </div>
      <div style="flex:1;padding:28px 24px;border-radius:16px;background:#fff;border:1px solid #E4E4E9;text-align:left;">
        <div style="width:36px;height:36px;border-radius:10px;background:#F5F4F7;display:flex;align-items:center;justify-content:center;margin-bottom:14px;font-size:16px;">⏱</div>
        <h4 style="font-size:15.5px;font-weight:600;margin-bottom:6px;">배송 소요 안내</h4>
        <p style="font-size:13.5px;color:#696F78;line-height:1.55;">미국의 해외직구 특성상 보통<br>__DELIVERY_MIN__일에서 __DELIVERY_MAX__일 정도 소요됩니다.<br>(미국 현지의 __PRODUCT__ 재고 상황에<br>따라 더 길어질 수 있습니다.)</p>
      </div>
    </div>
  </section>

  <section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="통관 안내">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">해외직구 필수 정보</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">통관 안내</h2>
      <p style="margin-top:14px;font-size:17px;color:#696F78;line-height:1.6;">해외직구 상품은 관세법에 따라 구매자의 개인통관고유부호가 필요합니다.</p>
    </div>
    <div style="max-width:740px;margin:0 auto;background:#fff;border:1px solid #E4E4E9;border-radius:22px;overflow:hidden;">
      <div style="padding:32px 36px;border-bottom:1px solid #E4E4E9;display:flex;align-items:center;justify-content:space-between;">
        <h3 style="font-size:19px;font-weight:700;">개인통관고유부호</h3>
        <div style="font-size:12px;color:#3371FB;font-weight:600;background:rgba(51,113,251,0.08);padding:5px 12px;border-radius:20px;">주문 시 필수 입력</div>
      </div>
      <div style="display:flex;padding:22px 36px;border-bottom:1px solid #E4E4E9;gap:24px;">
        <div style="width:170px;flex-shrink:0;font-size:14px;font-weight:600;color:#212326;">왜 필요한가요</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">해외에서 구매자에게 <b style="color: rgb(33, 35, 38); font-weight: 600;">직접 발송</b>되는 전자상거래 물품은 개인 명의로 수입신고가<br>진행되어, 통관고유부호·이름·연락처·주소가 <b style="color: rgb(33, 35, 38); font-weight: 600;">정확히 일치</b>해야 합니다.</div>
      </div>
      <div style="display:flex;padding:22px 36px;border-bottom:1px solid #E4E4E9;gap:24px;">
        <div style="width:170px;flex-shrink:0;font-size:14px;font-weight:600;color:#212326;">발급 방법</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">관세청 <b style="color: rgb(33, 35, 38); font-weight: 600;">UNI-PASS(개인통관고유부호 발급 시스템)</b>에서 본인인증 후<br>무료로 즉시 발급받을 수 있습니다.</div>
      </div>
      <div style="display:flex;padding:22px 36px;border-bottom:1px solid #E4E4E9;gap:24px;">
        <div style="width:170px;flex-shrink:0;font-size:14px;font-weight:600;color:#212326;">입력 시점</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">주문서 작성 시 수취인 정보와 함께 입력합니다.<br>정보가 일치하지 않으면 통관이 지연되거나 반송될 수 있습니다.</div>
      </div>
      <div style="display:flex;padding:22px 36px;gap:24px;">
        <div style="width:170px;flex-shrink:0;font-size:14px;font-weight:600;color:#212326;">관/부가세</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">본 상품 가격에는 개인 사용 목적, 1개 제품 구매 기준의 목록통관 관세·부가세가 이미 포함되어 있습니다. 다만 여러 제품을 함께 구매하시거나 같은 날 통관되는 구매자님의 다른 해외직구 물품이 있는 경우, 목록통관 기준을 초과해 관세·부가세가 별도로 부과될 수 있습니다.</div>
      </div>
    </div>
  </section>

  <section style="padding:100px 60px;" data-screen-label="배송/반품 안내">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">배송 · 교환 · 반품</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">배송/반품 안내</h2>
    </div>
    <div style="max-width:740px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#E4E4E9;border:1px solid #E4E4E9;border-radius:18px;overflow:hidden;">
      <div style="background:#fff;padding:28px 30px;">
        <h4 style="font-size:14.5px;font-weight:700;margin-bottom:10px;">배송 안내</h4>
        <p style="font-size:13.5px;color:#696F78;line-height:1.7;">해외 발송 후 통관을 거쳐 순차 배송됩니다. 보통 __DELIVERY_MIN__-__DELIVERY_MAX__일<br>정도 소요되며, 미국 창고에서 출고되면 배송 및 통관<br>조회가 가능합니다.</p>
      </div>
      <div style="background:#fff;padding:28px 30px;">
        <h4 style="font-size:14.5px;font-weight:700;margin-bottom:10px;">단순변심 반품</h4>
        <p style="font-size:13.5px;color:#696F78;line-height:1.7;">고객의 책임으로 인한 반품 시 <span style="color: rgb(33, 35, 38); font-weight: 600;">국내외 왕복 배송비는<br>구매자 부담</span>이며, 해외직구 특성상 국내 상품보다 반품<br>배송비가 높을 수 있습니다.</p>
      </div>
      <div style="background:#fff;padding:28px 30px;">
        <h4 style="font-size:14.5px;font-weight:700;margin-bottom:10px;">상품 하자/오배송</h4>
        <p style="font-size:13.5px;color:#696F78;line-height:1.7;">상품 하자, 오배송, 파손의 경우 반품 배송비를<br><span style="color: rgb(33, 35, 38); font-weight: 600;">TBD Seoul이 부담</span>합니다.</p>
      </div>
      <div style="background:#fff;padding:28px 30px;">
        <h4 style="font-size:14.5px;font-weight:700;margin-bottom:10px;">반품 회수 절차</h4>
        <p style="font-size:13.5px;color:#696F78;line-height:1.7;">반품 신청 접수 확인이 되면 예상되는 왕복 배송비 안내 후<br>제품을 수거할 택배접수를 해드립니다. 배송상자 내 제품 <br>상자는 훼손되지 말고 보내셔야 반품 처리 가능합니다.</p>
      </div>
    </div>
  </section>

  <section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="FAQ">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">FAQ</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">자주 묻는 질문</h2>
    </div>
    <div style="max-width:640px;margin:0 auto;">
      <div style="padding:22px 0;border-bottom:1px solid #E4E4E9;">
        <div style="font-size:15.5px;font-weight:600;margin-bottom:8px;">개인통관고유부호가 없으면 주문할 수 없나요?</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">네, 해외직구 상품 특성상 필수입니다. 관세청 홈페이지에서 1분 내 무료 발급 가능합니다.</div>
      </div>
      <div style="padding:22px 0;border-bottom:1px solid #E4E4E9;">
        <div style="font-size:15.5px;font-weight:600;margin-bottom:8px;">국내 정발과 무엇이 다른가요?</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">제품은 동일하나 해외 채널을 통해 직접 수입되어 더 합리적인 가격에 제공됩니다.</div>
      </div>
      <div style="padding:22px 0;border-bottom:1px solid #E4E4E9;">
        <div style="font-size:15.5px;font-weight:600;margin-bottom:8px;">전압/플러그 관련 이슈는 없나요?</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">해당 제품은 프리볼트(100–240V)로 국내에서 별도 변압기 없이 사용 가능합니다.</div>
      </div>
      <div style="padding:22px 0;border-bottom:1px solid #E4E4E9;">
        <div style="font-size:15.5px;font-weight:600;margin-bottom:8px;">A/S는 어떻게 진행되나요?</div>
        <div style="font-size:14px;color:#696F78;line-height:1.7;">구매 후 __RETURN_WEEKS__주 이내 초기불량은 TBD Seoul이 왕복 배송비를 포함해 전액 부담합니다. __RETURN_WEEKS__주 이후에는 __OFFICIAL__ 미국 무상 A/S 기간·항목에 해당하는 경우, 고객이 왕복 배송료만 부담하면 TBD Seoul이 해외 A/S까지 대행해 드립니다.</div>
      </div>
    </div>
  </section>

  <div style="padding:60px;background:#F5F4F7;font-size:12px;color:#696F78;line-height:1.8;" data-screen-label="Footer">
    <img src="assets/common/common_logo-footer.svg" alt="TBD Seoul" style="height: 31px; width: 111px; opacity: 0.55; margin-bottom: 18px">
    <div style="display:flex;gap:8px;"><span style="flex-shrink:0;color:#212326;font-weight:500;">상호</span><span>TBD Seoul</span></div>
    <div style="display:flex;gap:8px;"><span style="flex-shrink:0;color:#212326;font-weight:500;">스토어</span><span>__STORE__</span></div>
    <div style="display:flex;gap:8px;"><span style="flex-shrink:0;color:#212326;font-weight:500;">고지</span><span>본 상품은 해외에서 발송되는 병행/직수입 상품으로, 통관 절차 및 반품 정책은 국내 상품과 다를 수 있습니다.</span></div>
  </div>

</div>
</div>

</x-dc>
<script type="text/x-dc" data-dc-script>
class Component extends DCLogic {
  renderVals() {
    return {};
  }
}
</script>
</body>
</html>
"""


def trust_to_footer(brand=UNIFI_BRAND):
    return (
        _TRUST_TO_FOOTER_TEMPLATE
        .replace("__EYEBROW__", brand["eyebrow_label"])
        .replace("__PRODUCT__", brand["product_name"])
        .replace("__OFFICIAL__", brand["official_name"])
        .replace("__STORE__", brand["store_line"])
        .replace("__RETURN_WEEKS__", str(_RETURN_WINDOW_WEEKS))
        .replace("__DELIVERY_MIN__", str(_DELIVERY_MIN_DAYS))
        .replace("__DELIVERY_MAX__", str(_DELIVERY_MAX_DAYS))
    )


TRUST_TO_FOOTER = trust_to_footer()


def hero(title, tagline_html, img_src, img_alt, brand=UNIFI_BRAND):
    return f'''
  <div style="padding:100px 60px 4px;text-align:center;" data-screen-label="Hero">
    <img src="{brand['hero_logo_src']}" alt="{brand['hero_logo_alt']}" style="height:{brand['hero_logo_height']};width:auto;display:block;margin:0 auto;">
    <h1 style="font-size:52px;font-weight:700;letter-spacing:-0.03em;line-height:1.15;margin-top:48px;">{title}</h1>
    <div style="margin-top:18px;font-size:21px;color:#696F78;font-weight:400;">{tagline_html}</div>
    <div style="margin-top:56px;">
      <img src="{img_src}" alt="{img_alt}" style="width:100%;height:auto;display:block;">
    </div>
  </div>
'''


def why_section(eyebrow, headline_html, sub_html, cards, bg=False):
    bg_style = "background:#F5F4F7;" if bg else ""
    cards_html = "\n".join(f'''      <div style="padding:36px 28px;background:#fff;border:1px solid #E4E4E9;border-radius:18px;">
        <div style="font-size:13px;color:#3371FB;font-weight:700;margin-bottom:16px;">{i:02d}</div>
        <h3 style="font-size:19px;font-weight:600;margin-bottom:10px;">{h}</h3>
        <p style="font-size:14.5px;color:#696F78;line-height:1.6;">{p}</p>
      </div>''' for i, (h, p) in enumerate(cards, 1))
    return f'''
  <section style="padding:100px 60px;{bg_style}" data-screen-label="{eyebrow}">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">{eyebrow}</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">{headline_html}</h2>
      <p style="margin-top:14px;font-size:17px;color:#696F78;line-height:1.6;">{sub_html}</p>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:32px;">
{cards_html}
    </div>
  </section>
'''


def design_section(img_src, img_alt, headline_html, body_html, bg=True):
    bg_style = "background:#F5F4F7;" if bg else ""
    return f'''
  <section style="padding:100px 60px;{bg_style}" data-screen-label="Design">
    <div style="display:flex;align-items:center;gap:60px;">
      <div style="flex:1;">
        <img src="{img_src}" alt="{img_alt}" style="width:100%;height:auto;display:block;">
      </div>
      <div style="flex:1;">
        <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;margin-bottom:12px;">Design</div>
        <h2 style="font-size:30px;font-weight:700;letter-spacing:-0.02em;line-height:1.3;margin-bottom:16px;">{headline_html}</h2>
        <p style="font-size:16px;color:#696F78;line-height:1.7;">{body_html}</p>
      </div>
    </div>
  </section>
'''


def compare_cell(text, highlight=False, border_top=True, bottom_radius=False):
    bg = "background:rgba(51,113,251,0.06);" if highlight else ""
    bt = "border-top:1px solid #E4E4E9;" if border_top else ""
    br = "border-radius:0 0 12px 12px;" if bottom_radius else ""
    return f'<div style="padding:16px 12px;{bt}text-align:center;font-size:13.5px;{bg}{br}">{text}</div>'


def compare_section(headline_html, sub_html, cols, rows):
    """cols: list of (img_src, alt, name, desc_html, highlight_bool)
       rows: list of (label, [values per col])"""
    n = len(cols)
    header_imgs = "\n".join(
        f'''      <div style="padding:0 16px 20px;text-align:center;height:130px;display:flex;align-items:flex-end;justify-content:center;{"background:rgba(51,113,251,0.06);border-radius:12px 12px 0 0;" if hl else ""}">
        <img src="{img}" alt="{alt}" style="max-width:100%;max-height:100%;object-fit:contain;display:block;">
      </div>''' for img, alt, name, desc, hl in cols)
    name_cells = "\n".join(
        f'''      <div style="padding:0 12px 20px;text-align:center;{"background:rgba(51,113,251,0.06);" if hl else ""}">
        <div style="font-size:16px;font-weight:700;color:#3371FB;margin-bottom:8px;">{name}</div>
        <div style="font-size:12.5px;color:#696F78;line-height:1.5;">{desc}</div>
      </div>''' for img, alt, name, desc, hl in cols)
    row_html_parts = []
    total_rows = len(rows)
    for ridx, (label, values) in enumerate(rows):
        is_last = ridx == total_rows - 1
        label_style = "padding:16px 0;border-top:1px solid #E4E4E9;font-size:13.5px;color:#696F78;"
        if is_last:
            label_style += "border-bottom:1px solid #E4E4E9;"
        row = [f'<div style="{label_style}">{label}</div>']
        for cidx, val in enumerate(values):
            hl = cols[cidx][4]
            bg = "background:rgba(51,113,251,0.06);" if hl else ""
            bt = "border-top:1px solid #E4E4E9;"
            bb = "border-bottom:1px solid #E4E4E9;" if is_last else ""
            brad = "border-radius:0 0 12px 12px;" if (is_last and hl) else ""
            row.append(f'<div style="padding:16px 12px;{bt}{bb}text-align:center;font-size:13.5px;{bg}{brad}">{val}</div>')
        row_html_parts.append("\n      ".join(row))
    rows_html = "\n      ".join(row_html_parts)
    cols_template = " ".join(["1fr"] * n)
    min_width = 200 + n * 160
    return f'''
  <section style="padding:100px 60px;" data-screen-label="Compare">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">Compare</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">{headline_html}</h2>
      <p style="margin-top:14px;font-size:17px;color:#696F78;line-height:1.6;">{sub_html}</p>
    </div>
    <div style="overflow-x:auto;">
    <div style="display:grid;grid-template-columns:170px {cols_template};min-width:{min_width}px;">
      <div></div>
{header_imgs}
      <div></div>
{name_cells}
      {rows_html}
    </div>
    </div>
  </section>
'''


def spec_row(label, value, highlight=False):
    bg = "background:rgba(51,113,251,0.06);" if highlight else ""
    return (f'<div style="display:flex;padding:18px 0;border-bottom:1px solid #E4E4E9;{bg}">'
            f'<div style="width:220px;font-size:14px;color:#696F78;">{label}</div>'
            f'<div style="flex:1;font-size:15px;font-weight:500;">{value}</div></div>')


def tech_specs_section(rows):
    body = "\n      ".join(spec_row(l, v) for l, v in rows)
    return f'''
  <section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Tech Specs">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">Tech Specs</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">주요 사양</h2>
    </div>
    <div style="max-width:640px;margin:0 auto;">
      {body}
    </div>
  </section>
'''
