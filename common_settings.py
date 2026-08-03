"""브랜드 로고/문구 + 공통 구매·배송 안내를 코드 수정 없이 바꿀 수 있게 하는
JSON 설정 저장소. 대시보드 `/settings` 페이지가 이 파일을 통해 읽고 쓰고,
`product_pages/scripts/build_pages.py`가 여기서 불러온 값을 UNIFI_BRAND/
GLINET_BRAND/트러스트 템플릿 기본값 위에 덮어씌워 사용한다.

주의: 이미 생성된 .dc.html에는 소급 적용되지 않는다 - 값을 바꾼 뒤 해당
상품의 상세페이지를 다시 생성해야 반영된다.
"""
from __future__ import annotations

import json
import os

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "common_settings.json")

DEFAULTS: dict = {
    "brands": {
        "UniFi": {
            "header_logo_src": "assets/common/common_logo-supply.svg",
            "header_logo_alt": "Unifi Supply",
            "hero_logo_src": "assets/common/common_logo-symbol.svg",
            "hero_logo_alt": "UniFi",
            "hero_logo_height": "60px",
            "eyebrow_label": "UNIFI SUPPLY BY TBD SEOUL",
            "supply_label": "Unifi Supply",
            "product_name": "UniFi",
            "official_name": "Ubiquiti",
            "store_line": "Unifi Supply by TBD Seoul",
        },
        "GL.inet": {
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
        },
    },
    "common_copy": {
        # "2주 초기불량 전액 보장" 등 트러스트 섹션에 쓰이는 값들.
        "return_window_weeks": 2,
        "delivery_min_days": 7,
        "delivery_max_days": 14,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
  result = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
  for k, v in override.items():
    if isinstance(v, dict) and isinstance(result.get(k), dict):
      result[k] = _deep_merge(result[k], v)
    else:
      result[k] = v
  return result


def load() -> dict:
  """저장된 JSON을 기본값 위에 병합해서 돌려준다 (파일이 없으면 기본값 그대로)."""
  if not os.path.exists(_SETTINGS_PATH):
    return json.loads(json.dumps(DEFAULTS))
  with open(_SETTINGS_PATH, encoding="utf-8") as f:
    saved = json.load(f)
  return _deep_merge(DEFAULTS, saved)


def save(data: dict) -> None:
  with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
