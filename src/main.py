import os
import time
import argparse
from openai import OpenAI, AzureOpenAI
import pickle
from markdownify import markdownify as md

from env import Env
import dotenv

dotenv.load_dotenv()
print("AZURE_OPENAI_ENDPOINT:", os.getenv('AZURE_OPENAI_ENDPOINT'))
print("AZURE_OPENAI_KEY:", os.getenv('AZURE_OPENAI_KEY'))
print("AZURE_OPENAI_API_VERSION:", os.getenv('AZURE_OPENAI_API_VERSION'))


def extract_tables_from_markdown_with_labels(markdown_text, label_position='before'):
    lines = markdown_text.split('\n')
    tables_with_labels = []
    table = []
    label = ""
    in_table = False
    after_label = ""  # 'after' 라벨을 위한 변수

    for line in lines:
        if line.strip() == '' and not in_table:
            continue
        if '|' in line and not in_table:
            in_table = True
            if label_position == 'before':
                table.append(label)  # 라벨을 테이블 앞에 추가
            table.append(line)
            label = ""  # 라벨 초기화
        elif '|' in line and in_table:
            table.append(line)
        elif '|' not in line and in_table:
            in_table = False
            if label_position == 'after' and after_label:
                table.append(after_label)  # 라벨을 테이블 뒤에 추가
            tables_with_labels.append('\n'.join(table))
            table = []
            after_label = ""  # 'after' 라벨 초기화
        else:
            if in_table and label_position == 'after':
                after_label = line  # 테이블 뒤의 첫 번째 라인을 라벨로 저장
            else:
                label = line  # 테이블 앞의 마지막 라인을 라벨로 저장

    if table:
        if label_position == 'after' and after_label:
            table.append(after_label)  # 마지막 테이블에 대해 라벨을 뒤에 추가
        tables_with_labels.append('\n'.join(table))

    return tables_with_labels


if __name__ == '__main__':
    original_file_paths = os.listdir("./data")
    for file_path in original_file_paths:
        filename = file_path.split(".")[0]
        if file_path == ".gitignore":
            continue
        with open(f"./data/{file_path}", "r") as f:
            html_content = f.read()
            markdown_text = md(html_content)
            tables = extract_tables_from_markdown_with_labels(
                markdown_text)  # 테이블 추출
            # tables = tables[:3]  # 테스트를 위해 3개의 테이블만 사용

            # 테이블을 파일로 저장하거나 다른 처리를 수행
            print(f"Found {len(tables)} tables in {filename}.md")
            print(tables[0])

    # Azure OpenAI API를 사용하여 Assistant 생성
    client = AzureOpenAI(
        api_key=Env.AZURE_OPENAI_API_KEY,
        api_version=Env.AZURE_OPENAI_API_VERSION,
        azure_endpoint=Env.AZURE_OPENAI_ENDPOINT,
    )

    # ./input/assistant.pkl이 없을시
    if not os.path.exists("./input/assistant.pkl"):

        with open("./input/instructions.txt", "r") as f:
            instructions = f.read()
        assistant = client.beta.assistants.create(
            name="Table Analyst Assistant",
            instructions=instructions,
            model="auto-report-oai",
        )
        pickle.dump(assistant, open("./input/assistant.pkl", "wb"))
    else:
        assistant = pickle.load(open("./input/assistant.pkl", "rb"))

    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        temperature=1,
        top_p=1,
    )
    print(assistant)

    # Thread 생성
    thread = client.beta.threads.create()
    for table in tables:
        table_content = "\n".join(table)
        thread_message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=table,
        )
        print(thread_message)
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        print(run)
        print("Sleeping for 15 seconds...")
        time.sleep(15)

    messages = [message for message in client.beta.threads.messages.list(
        thread_id=thread.id) if message.role != "user"]
    # messages 역순으로 정렬
    messages = messages[::-1]
    with open("./output/output.txt", "w") as f:
        for message in messages:
            print(message.content)
            message_content = message.content[0].text
            f.write(message_content.value)
            print(message_content.value)
            f.write("\n---\n")
            print("---")
