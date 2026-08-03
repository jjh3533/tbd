"""상세페이지 브리프(태그라인/Why 3카드/Design/Tech Specs) 초안을 Claude로 생성.

CheapSub(https://cheapsub.im, Anthropic Messages API 호환 중계 게이트웨이)를
통해 claude-sonnet-5를 호출한다. 이 모듈은 detail_page_builder.py(로컬 전용
상세페이지 제작 도구)에서만 쓰이므로, CHEAPSUB_API_KEY가 없어도 나머지
대시보드는 영향받지 않는다(config.py에서 required=False, 호출부도 지연
import).

생성된 결과는 항상 사람이 검토/수정한 뒤 저장하는 초안일 뿐이다 - 이 프로젝트의
다른 자동화(리테일러 후보 검색, 카테고리 자동선택 등)와 동일하게 최종 판단은
사람이 한다.

주의: 이 게이트웨이의 /v1/messages는 stream=true면 400을 반환한다(공식 문서
"AI에게 시킬 때" 섹션 참고) - 아래 client.messages.create()는 stream 파라미터를
쓰지 않는다(기본값이 non-stream이라 안전).
"""
from __future__ import annotations

import json
import os
import sys

import anthropic

import config

_CHEAPSUB_BASE_URL = "https://api.cheapsub.im"  # /v1 붙이지 않음 - SDK가 /v1/messages를 자동으로 붙임
_MODEL = "claude-sonnet-5"


def _load_example_briefs(limit: int = 2) -> list[dict]:
  """실제로 라이브에 쓰인 브리프를 스타일 예시로 프롬프트에 포함시킨다
  (톤/구조를 맞추기 위함). build_detail_page는 product_pages/scripts/에 있어서
  다른 지연 import들과 동일한 방식으로 sys.path에 추가해서 불러온다."""
  scripts_dir = os.path.join(
      os.path.dirname(os.path.abspath(__file__)), "product_pages", "scripts"
  )
  if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
  import build_detail_page as bdp

  examples = []
  for slug in bdp.list_briefs()[:limit]:
    try:
      examples.append(bdp.load_brief(slug))
    except Exception:  # noqa: BLE001
      continue
  return examples


_BRIEF_TOOL = {
    "name": "submit_brief",
    "description": "완성된 상세페이지 브리프 초안을 제출한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tagline": {
                "type": "string",
                "description": "히어로 섹션 태그라인. 1~2문장, 필요하면 <br>로 자연스러운 위치에 줄바꿈.",
            },
            "why_headline": {"type": "string", "description": "Why 섹션 헤드라인, <br> 가능"},
            "why_sub": {"type": "string", "description": "Why 섹션 서브텍스트 1문장"},
            "why_cards": {
                "type": "array",
                "description": "정확히 3개. 각각 제목(<br> 가능)과 본문(2~3문장)",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["heading", "body"],
                },
                "minItems": 3,
                "maxItems": 3,
            },
            "design_headline": {"type": "string", "description": "Design 섹션 헤드라인, <br> 가능"},
            "design_body": {"type": "string", "description": "Design 섹션 본문 2~3문장"},
            "specs": {
                "type": "array",
                "description": "Tech Specs 표. 참고자료에서 실제로 확인된 값만 넣고, 모르는 항목은 아예 포함하지 않는다(지어내지 않음).",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["label", "value"],
                },
            },
        },
        "required": [
            "tagline", "why_headline", "why_sub", "why_cards",
            "design_headline", "design_body", "specs",
        ],
    },
}


def _build_system_prompt() -> str:
  examples = _load_example_briefs()
  examples_text = "\n\n".join(
      f"예시 {i + 1} ({ex.get('brand')} {ex.get('title')}):\n" + json.dumps(
          {k: v for k, v in ex.items() if k not in ("hero_source", "design_source")},
          ensure_ascii=False, indent=2,
      )
      for i, ex in enumerate(examples)
  ) or "(아직 저장된 예시 없음)"

  return (
      "너는 'TBD Seoul'이라는 병행수입/구매대행 스마트스토어의 상세페이지 카피라이터다. "
      "UniFi/GL.inet 등 네트워크 장비를 한국 소비자에게 파는 상세페이지 브리프를 작성한다.\n\n"
      "규칙:\n"
      "- 전부 한국어로 작성 (스펙 항목명 Label은 영어 관례를 유지해도 됨, 예: Dimensions/CPU/Wi-Fi Standard)\n"
      "- 과장되거나 근거 없는 표현 금지 - 참고자료에 실제로 있는 사실만 사용\n"
      "- specs는 참고자료에서 확인된 값만 넣는다. 모르는 항목은 절대 지어내지 말고 아예 넣지 않는다\n"
      "- 문체는 담백하고 정보 위주 (과도한 판매 상술 톤 지양)\n"
      "- <br>은 헤드라인/태그라인에서 자연스러운 줄바꿈 위치에만 사용\n\n"
      "아래는 실제로 만들어져 라이브에 쓰인 브리프 예시다 (톤/구조 참고용):\n\n"
      f"{examples_text}"
  )


def generate_brief_draft(
    brand: str, title: str, model_number: str, reference_text: str, category: str = "",
) -> dict:
  """Claude(claude-sonnet-5, CheapSub 게이트웨이)로 브리프 초안을 생성한다.

  반환값은 detail_page_builder.py의 폼 필드에 그대로 채워 넣을 수 있는 dict:
      {tagline, why_headline, why_sub, why_cards: [[heading, body], ...],
       design_headline, design_body, specs: [[label, value], ...]}
  brand/title/hero_source/design_source/why_bg_gray는 이미 폼에 있는 값을
  그대로 쓰므로 여기서 생성하지 않는다."""
  if not config.CHEAPSUB_API_KEY:
    raise RuntimeError("CHEAPSUB_API_KEY가 설정되지 않았습니다 (.env 확인).")

  client = anthropic.Anthropic(api_key=config.CHEAPSUB_API_KEY, base_url=_CHEAPSUB_BASE_URL)

  user_content = (
      f"브랜드: {brand}\n상품명: {title}\n모델명: {model_number or '(없음)'}\n"
      f"카테고리: {category or '(없음)'}\n\n"
      f"참고 자료(공홈 설명/스펙):\n{reference_text}\n\n"
      "위 참고자료를 바탕으로 submit_brief 도구로 브리프 초안을 제출해줘."
  )

  message = client.messages.create(
      model=_MODEL,
      max_tokens=4096,
      system=_build_system_prompt(),
      tools=[_BRIEF_TOOL],
      tool_choice={"type": "tool", "name": "submit_brief"},
      messages=[{"role": "user", "content": user_content}],
  )

  tool_use = next((block for block in message.content if block.type == "tool_use"), None)
  if tool_use is None:
    raise RuntimeError("Claude 응답에서 브리프 데이터를 찾지 못했습니다.")

  data = tool_use.input
  return {
      "tagline": data.get("tagline", ""),
      "why_headline": data.get("why_headline", ""),
      "why_sub": data.get("why_sub", ""),
      "why_cards": [[c.get("heading", ""), c.get("body", "")] for c in data.get("why_cards", [])],
      "design_headline": data.get("design_headline", ""),
      "design_body": data.get("design_body", ""),
      "specs": [[s.get("label", ""), s.get("value", "")] for s in data.get("specs", [])],
  }
