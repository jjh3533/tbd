"""공홈 크롤러 공통 데이터 모델."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProductData:
  """브랜드 크롤러가 공통으로 반환하는 상품 정보.

  스펙/설명은 구조화하지 않고 description 텍스트에 그대로 합쳐서 담는다.
  이 데이터는 NocoDB에 자동으로 저장되는 게 아니라 대시보드에서 사람이
  검토/수정한 뒤 저장하는 용도이기 때문."""
  title: str
  price_usd: float
  model_number: str
  description: str
  image_urls: list[str] = field(default_factory=list)
