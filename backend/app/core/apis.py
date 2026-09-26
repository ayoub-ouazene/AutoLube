from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import os 
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

groq_keys = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]
apikey_groq = os.getenv("GROQ_API_KEY2") or (groq_keys[1] if len(groq_keys) > 1 else (groq_keys[0] if groq_keys else None))
apikey_groq2=os.getenv("GROQ_API_KEY") or (groq_keys[0] if groq_keys else None)
apikey_groq3=os.getenv("GROQ_API_KEY3") or (groq_keys[2] if len(groq_keys) > 2 else (groq_keys[0] if groq_keys else None))


dahl_api_key = os.getenv("DAHL_API_KEY")
openrouter_keys = [k.strip() for k in os.getenv("OPENROUTER_KEYS", "").split(",") if k.strip()]
openrouter_api_key = os.getenv("OPENROUTER_API_KEY") or (openrouter_keys[0] if openrouter_keys else None)




main_groq_model = ChatGroq(model="openai/gpt-oss-120b", api_key=apikey_groq2 ,  temperature=0.0 , )
alternative_groq_model = ChatGroq(model="qwen/qwen3.8-27b" , api_key=apikey_groq ,  temperature=0.0 , )
small_groq_model =  ChatGroq(model="openai/gpt-oss-20b" , api_key=apikey_groq ,  temperature=0.0 , )


dahl_model = ChatOpenAI(model="zai-org/GLM-5.3-Flash" , base_url="https://inference.dahl.global/v1" , api_key=dahl_api_key , temperature=0.0 , )

openrouter_model = ChatOpenAI(model="" , base_url="https://openrouter.ai/api/v1" , api_key=openrouter_api_key , temperature=0.0)
openrouter_alternative = ChatOpenAI(model="google/gemma-4-31b-it:free" , base_url="https://openrouter.ai/api/v1" , api_key=openrouter_api_key , temperature=0.0)