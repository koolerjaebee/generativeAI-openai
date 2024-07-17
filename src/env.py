import os
import dotenv


dotenv.load_dotenv()


class Env:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
