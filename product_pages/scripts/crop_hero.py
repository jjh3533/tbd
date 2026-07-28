"""Ubiquiti CDN 제품 이미지는 실제 제품 아래에 위아래로 뒤집힌 반사 이미지이 간격
없이 바로 이어붙어 있는 경우가 많음 (사이트 자체 CSS 그라디언트 마스크로 가려지는
게 원본 PNG엔 그대로 남아있음). 행별 alpha 총합(실루엣 프로파일)의 대칭점을 찾아
반사 부분을 잘라낸다."""
import sys
from PIL import Image
import numpy as np


def find_content_bbox(alpha: np.ndarray, threshold: int = 10):
    rows = np.where((alpha > threshold).any(axis=1))[0]
    return rows.min(), rows.max() + 1


def find_reflection_split(alpha: np.ndarray, top: int, bottom: int):
    """실제 제품은 보통 프레임의 상당 부분(세로 기준 55% 이상)을 차지하고,
    반사는 캔버스 하단에서 잘려 더 짧은 경우가 많음. 행별 alpha 총합
    프로파일을 이용해 [top:split] 구간을 뒤집었을 때 [split:] 구간과 가장 잘
    맞아떨어지는 지점을 찾는다."""
    profile = alpha[top:bottom, :].astype(np.float64).sum(axis=1)
    height = bottom - top
    best_split, best_score = None, None
    for split_rel in range(int(height * 0.55), height):
        upper = profile[:split_rel]
        lower = profile[split_rel:]
        h = min(len(upper), len(lower))
        if h < 15:
            continue
        u = upper[-h:]
        l = lower[:h][::-1]
        denom = np.maximum(u, l)
        denom[denom == 0] = 1
        score = (np.abs(u - l) / denom).mean()
        if best_score is None or score < best_score:
            best_score = score
            best_split = split_rel
    return (top + best_split if best_split is not None else bottom), best_score


def crop_hero(src_path: str, dst_path: str, padding: int = 12):
    img = Image.open(src_path).convert("RGBA")
    alpha = np.array(img.split()[-1])
    top, bottom = find_content_bbox(alpha)
    split, score = find_reflection_split(alpha, top, bottom)
    crop_bottom = min(split + padding, bottom)
    cropped = img.crop((0, max(top - padding, 0), img.width, crop_bottom))
    cropped.save(dst_path)
    return {"top": int(top), "bottom": int(bottom), "split": int(split),
            "score": round(float(score), 4), "out_size": cropped.size}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    print(crop_hero(src, dst))
