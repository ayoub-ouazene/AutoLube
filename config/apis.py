from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import os 
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

apikey_groq = os.getenv("GROQ_API_KEY2")
dahl_api_key = os.getenv("DAHL_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

main_groq_model = ChatGroq(model="openai/gpt-oss-120b", api_key=apikey_groq ,  temperature=0.0 , )
alternative_groq_model = ChatGroq(model="qwen/qwen3.8-27b" , api_key=apikey_groq ,  temperature=0.0 , )
small_groq_model =  ChatGroq(model="openai/gpt-oss-20b" , api_key=apikey_groq ,  temperature=0.0 , )


dahl_model = ChatOpenAI(model="zai-org/GLM-5.3-Flash" , base_url="https://inference.dahl.global/v1" , api_key=dahl_api_key , temperature=0.0 , )

openrouter_model = ChatOpenAI(model="nvidia/nemotron-3-super-120b-a12b:free" , base_url="https://openrouter.ai/api/v1" , api_key=openrouter_api_key , temperature=0.0)
openrouter_alternative = ChatOpenAI(model="google/gemma-4-31b-it:free" , base_url="https://openrouter.ai/api/v1" , api_key=openrouter_api_key , temperature=0.0)