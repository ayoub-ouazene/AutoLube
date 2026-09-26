"""
Manual CLI tester for the main agent, independent of the backend.
Run with: python -m tests.test_cli_chat
"""
from app.agents.main_agent import run_chat_session

if __name__ == "__main__":
    run_chat_session()
