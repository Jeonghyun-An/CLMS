import os
import json
import torch
import numpy as np
from paddleocr import PaddleOCR
from pdf2image import convert_from_path

LANGUAGE = 'korean'
DETECT_BOX_THRESH = 0.3
USE_GPU = True 

SHOW_LOG = False
PDF_PATH = "/data/clms_seocho/입찰공고문.pdf"
OUTPUT_JSON_PATH = "/data/clms_seocho/ocr_result_v2.json"

def sort_boxes(ocr_results):
    if not ocr_results or ocr_results[0] is None:
        return ""
    
    lines = ocr_results[0]
    lines.sort(key=lambda x: x[0][0][1])
    
    sorted_content = []
    y_threshold = 10
    
    if lines:
        current_line = [lines[0]]
        for i in range(1, len(lines)):
            if abs(lines[i][0][0][1] - current_line[-1][0][0][1]) < y_threshold:
                current_line.append(lines[i])
            else:
                current_line.sort(key=lambda x: x[0][0][0])
                sorted_content.append(" ".join([line[1][0] for line in current_line]))
                current_line = [lines[i]]
        
        current_line.sort(key=lambda x: x[0][0][0])
        sorted_content.append(" ".join([line[1][0] for line in current_line]))
        
    return "\n".join(sorted_content)

def main():
    
    ocr = PaddleOCR(
        lang=LANGUAGE,
        use_angle_cls=False,
        det_db_box_thresh=DETECT_BOX_THRESH,
        use_gpu=USE_GPU,
        show_log=SHOW_LOG,
        # --- 아래 2개 파라미터 추가 ---
        det_limit_side_len=3000, # 모델이 이미지를 강제로 축소하지 못하게 상한선을 대폭 늘립니다.
        drop_score=0.1           # 확신이 부족한 옅고 작은 글씨도 버리지 않고 추출하게 만듭니다.
    )

    if not os.path.exists(PDF_PATH):
        print(f"[Error] 파일을 찾을 수 없습니다: {PDF_PATH}")
        return

    print(f"[Info] PDF 분석 시작: {PDF_PATH}")
    images = convert_from_path(PDF_PATH, dpi=300)

    accumulated_results = []

    for i, image in enumerate(images):
        page_num = i + 1
        print(f"[Info] {page_num}페이지 OCR 분석 중...")
        
        # 확실하게 RGB 포맷으로 고정한 뒤 BGR로 뒤집기
        img_array = np.array(image.convert('RGB'))[:, :, ::-1] 
        result = ocr.ocr(img_array, cls=False)
        
        # [디버깅 추가] 모델이 뽑아낸 날것 그대로의 데이터를 화면에 출력
        print(f"[{page_num}페이지 원본 추출 데이터]: {result}")
        
        page_text = sort_boxes(result)
        
        page_data = {
            "page": page_num,
            "content": page_text
        }
        accumulated_results.append(page_data)
        
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(accumulated_results, f, ensure_ascii=False, indent=4)
            
        print(f"[Success] {page_num}페이지 결과 저장 완료.")

    print(f"\n[Finish] 추출 완료: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    main()