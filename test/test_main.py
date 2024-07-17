import os
import pytest
from unittest.mock import patch, MagicMock
from src.main import extract_tables_from_markdown_with_labels  # main.py 모듈 임포트
import subprocess

# # API 호출 모의
# @patch('main.AzureOpenAI')
# def test_api_call(mock_azure):
#     mock_client = MagicMock()
#     mock_azure.return_value = mock_client
#     mock_client.beta.assistants.create.return_value = MagicMock(id="test_id")
#     mock_client.beta.assistants.update.return_value = MagicMock(temperature=1, top_p=1)

#     # main.py의 함수 실행
#     main.some_function()  # main.py 내의 테스트하고자 하는 함수 호출

#     # API가 예상대로 호출되었는지 확인
#     mock_client.beta.assistants.create.assert_called_once()
#     mock_client.beta.assistants.update.assert_called_with(assistant_id="test_id", temperature=1, top_p=1)

# # 파일 입출력 모의
# @patch('os.path.exists')
# @patch('builtins.open')
# def test_file_io(mock_open, mock_exists):
#     mock_exists.return_value = False  # 파일이 존재하지 않는 경우를 시뮬레이션

#     # main.py의 함수 실행
#     main.some_function()  # main.py 내의 테스트하고자 하는 함수 호출

#     # 파일 입출력이 예상대로 수행되었는지 확인
#     mock_open.assert_called_with("./input/assistant.pkl", "wb")


def test_func():
    test_tables_with_labels = extract_tables_from_markdown_with_labels("""Table 3: 처음 음주 연령
 








    |  | 카테고리 | 평균 ± 표준편차 |
    | --- | --- | --- |
    | 전체 |  | 9.21 ± 3.03 |
    | 연령별 | 초등학교 5학년 | 8.31 ± 2.5 |
    |  | 중학교 2학년 | 10.94 ± 3.22 |
    | 지역별 | 북부 | 8.8 ± 3.24 |
    |  | 중부 | 9.74 ± 2.84 |
    |  | 남부 | 8.14 ± 3.12 |
    | 부모음주별 | 예 | 9.21 ± 3.01 |
    |  | 아니오 | 9.21 ± 3.09 |
    """)
    print(test_tables_with_labels[0])
    assert len(test_tables_with_labels) == 1
    assert "Table 3: 처음 음주 연령" in test_tables_with_labels[0]


def test_main_py_execution():
    # 상위 디렉토리 경로 설정
    parent_directory = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))
    # main.py 실행
    result = subprocess.run(['python3', 'src/main.py'],
                            capture_output=True, text=True, cwd=parent_directory)
    print(result)
    # 성공적으로 실행되었는지 확인 (종료 코드가 0인지)
    assert result.returncode == 0, "main.py did not exit successfully"

    # # 예상되는 출력이 있는지 검증
    # expected_output = "Hello, World!"  # 예상되는 출력을 여기에 적어주세요
    # assert expected_output in result.stdout, "Expected output not found in main.py execution result"
