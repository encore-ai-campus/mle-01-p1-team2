import os
from getpass import getpass
from pathlib import Path
from pprint import pprint
import pandas as pd

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI


PROJECT_DIR = Path.cwd()
if not (PROJECT_DIR / "data").is_dir() and (PROJECT_DIR.parent / "data").is_dir():
    PROJECT_DIR = PROJECT_DIR.parent

load_dotenv(PROJECT_DIR / ".env")
CHROMA_DIR = PROJECT_DIR.parent / "data" / "chroma_db"

embedding_model = HuggingFaceEmbeddings(
    model_name="jhgan/ko-sroberta-multitask",
    encode_kwargs={"normalize_embeddings": True},
)

OPENAI_API_KEY = '../.streamlit/secrets.toml'

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
parser = StrOutputParser()


vector_db = Chroma(
    collection_name="pet_care",
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_DIR),
)