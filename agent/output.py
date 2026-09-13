from agent.tools import Search , Search2 
from langchain_groq import ChatGroq
from pathlib import Path
import os
from dotenv import load_dotenv
from agent.model import run_chat_session
# Load environment

load_dotenv(Path(__file__).parent / ".env")
apikey = os.getenv("GROQ_API_KEY")

# Initialize LLM
model_g = ChatGroq(model="openai/gpt-oss-120b", api_key=apikey)


def test():
    name  = input("car name : ")
    model = input("car's model : ")
    year = input("car's year : ")
    refrence = input("engine/transmission refrence : ")
    oil_type = input("oil type : ")

    result1 = Search.invoke({
    "name": name,
    "year": year,
    "model": model,
    "refrence": refrence,
    "fluid_type": oil_type
    })

    result2 = Search2.invoke({
    "name": name,
    "year": year,
    "model": model,
    "refrence": refrence,
    "fluid_type": oil_type
    })

    query = f"OEM {oil_type} specification viscosity capacity {name} {model} {year} {refrence} in algeria"
        
    result3 = model_g.invoke(query)

    print("=============Result 1 =====================")
    print(result1)
    print("===========================================")
    print("********************************************")
    print("=============Result 2 =====================")
    print(result2)
    print("********************************************")
    print("=============Result 3 =====================")
    print(result3.content)
    print("=============Result 4 =====================")
    run_chat_session()



    



if __name__ == "__main__" :
    test()     
