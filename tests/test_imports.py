import unittest


class ImportSmokeTests(unittest.TestCase):
    def test_agent_imports(self):
        from app.agents.db_tools.specs_lookup import specs_lookup
        from app.agents.db_tools.stock_lookup import stock_lookup
        from app.agents.main_agent import process_turn, run_chat_session
        from app.agents.search_agent.agent import Use_Search_Agent

        self.assertIsNotNone(specs_lookup)
        self.assertIsNotNone(stock_lookup)
        self.assertIsNotNone(process_turn)
        self.assertIsNotNone(run_chat_session)
        self.assertIsNotNone(Use_Search_Agent)

    def test_db_and_schema_imports(self):
        from app.agents.schemas import SearchInput
        from app.core.llm_pool import load_keys_from_env, run_with_failover
        from app.db.models.tables import (
            Oil_Engine_Cache,
            Oil_Engine_Item,
            Oil_Transmission_Item,
            Transmission_Oil_Cache,
        )
        from app.db.session import SessionLocal, engine

        self.assertIsNotNone(SearchInput)
        self.assertIsNotNone(load_keys_from_env)
        self.assertIsNotNone(run_with_failover)
        self.assertIsNotNone(engine)
        self.assertIsNotNone(SessionLocal)
        self.assertIsNotNone(Oil_Engine_Cache)
        self.assertIsNotNone(Transmission_Oil_Cache)
        self.assertIsNotNone(Oil_Engine_Item)
        self.assertIsNotNone(Oil_Transmission_Item)


if __name__ == "__main__":
    unittest.main()
