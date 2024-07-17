from bs4 import BeautifulSoup
import re

# HTML 파일 열기
with open('./data/ss.html', 'r', encoding='utf-8') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')

# 새 TXT 파일 생성 및 열기
with open('./output/extracted_text.txt', 'w', encoding='utf-8') as txt_file:
    # 모든 figcaption 태그 찾기
    for figcaption in soup.find_all('figcaption'):
        # figcaption 내의 텍스트를 추출하고, HTML 엔티티를 처리
        text = figcaption.get_text(separator=' ', strip=True)
        text = text.replace('\n', '').replace('\r', '')

        # 띄어쓰기 2번 이상을 1번으로 바꾸기
        text = re.sub(r'\s+', ' ', text)

        print(text)
        # "Table {num}:" 패턴 찾기
        if re.search(r'Table\s+\d+:', text):
            # 해당 텍스트를 TXT 파일에 추가
            txt_file.write(text + '\n')
