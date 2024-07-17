import os
import time
import argparse
from openai import OpenAI, AzureOpenAI
import dotenv
import pickle


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', default=False)
    parser.add_argument('--assistant_name', type=str,
                        default="Data Analyst Assistant")
    parser.add_argument('--store_name', type=str, default="Data Statements")
    parser.add_argument('--annotation', action='store_true', default=False)
    parser.add_argument('--azure', action='store_true', default=False)

    is_annotation = parser.parse_args().annotation
    is_azure = parser.parse_args().azure
    vector_store_name = parser.parse_args().store_name

    dotenv.load_dotenv()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    print(AZURE_OPENAI_API_KEY)
    print(AZURE_OPENAI_API_VERSION)
    print(AZURE_OPENAI_ENDPOINT)

    if is_azure:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )
    else:
        client = OpenAI(api_key=OPENAI_API_KEY)

    if parser.parse_args().init:
        if is_azure:
            vector_store = client.beta.vector_stores.create(
                name=vector_store_name)
        else:
            vector_store = client.beta.vector_stores.create(
                name=vector_store_name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": 7
                }
            )

        instructions = ""
        with open("./input/instructions.txt", "r") as f:
            instructions = f.read()
        if is_azure:
            assistant = client.beta.assistants.create(
                name=parser.parse_args().assistant_name,
                instructions=instructions,
                model="auto-report-oai",
            )
        else:
            assistant = client.beta.assistants.create(
                name=parser.parse_args().assistant_name,
                instructions=instructions,
                model="gpt-4o",
            )

        pickle.dump(vector_store, open("./input/vector_store.pkl", "wb"))
        pickle.dump(assistant, open("./input/assistant.pkl", "wb"))
    else:
        vector_store = pickle.load(open("./input/vector_store.pkl", "rb"))
        assistant = pickle.load(open("./input/assistant.pkl", "rb"))
        print(vector_store)
        print(assistant)

    # Ready the files for upload to OpenAI
    original_file_paths = os.listdir("./data")
    file_paths = []
    for idx, path in enumerate(original_file_paths):
        if path == ".gitignore":
            continue
        else:
            path = f"./data/{path}"
            file_paths.append(path)
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    # You can print the status and the file counts of the batch to see the result of this operation.
    print(file_batch.status)
    print(file_batch.file_counts)

    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tools=[{"type": "file_search", "file_search": {"max_num_results": 5}}],
        tool_resources={"file_search": {
            "vector_store_ids": [vector_store.id]}},
        temperature=1,
        top_p=1,
    )

    # # Upload the user provided file to OpenAI
    # message_file = client.files.create(
    #     file=open("edgar/aapl-10k.pdf", "rb"), purpose="assistants"
    # )
    messages_contents = []
    with open("./input/messages.txt", "r") as f:
        messages_contents = f.readlines()
        # Remove \n
        messages_contents = [msg.strip() for msg in messages_contents]
        print(messages_contents)

    # Create a thread and attach the file to the message
    thread = client.beta.threads.create()

    # The thread now has a vector store with that file in its tool resources.
    print(thread.tool_resources)
    # print(thread.tool_resources.file_search)

    # Use the create and poll SDK helper to create a run and poll the status of
    # the run until it's in a terminal state.
    for message_content in messages_contents:
        thread_message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_content,
        )
        print(thread_message)
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        print(run)
        # time.sleep(15)
        # print("Sleeping for 15 seconds")

    messages = list(client.beta.threads.messages.list(thread_id=thread.id))

    with open("./output/output.txt", "w") as f:
        for message in messages:
            print(message.content)
            message_content = message.content[0].text
            annotations = message_content.annotations
            citations = []
            for index, annotation in enumerate(annotations):
                if is_annotation:
                    message_content.value = message_content.value.replace(
                        annotation.text, f"[{index}]")
                else:
                    message_content.value = message_content.value.replace(
                        annotation.text, "")
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")
            f.write(message_content.value)
            print(message_content.value)
            if is_annotation:
                f.write("\n".join(citations))
                print("\n".join(citations))
            f.write("\n---\n")
            print("---")
