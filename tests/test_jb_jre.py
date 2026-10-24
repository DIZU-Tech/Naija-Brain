import tempfile
import unittest
from pathlib import Path
from datetime import date
from jarvis_brain import JarvisBrain, ConversationStore
from jarvis_brain.core import age, calc, intent, language

class JbJreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.brain = JarvisBrain(store=ConversationStore(str(Path(self.tmp.name) / "test.sqlite3")))
    def tearDown(self):
        self.tmp.cleanup()
    def ask(self, message, session="test"):
        return self.brain.respond(session, message)
    def test_greeting(self):
        self.assertIn("Hello", self.ask("Hello 👋")["reply"])
    def test_broad_request_clarifies(self):
        self.assertIn("starting point", self.ask("I'll like to know everything")["reply"])
    def test_wow_uses_context(self):
        self.ask("I'll like to know everything")
        self.assertIn("one step at a time", self.ask("Wow")["reply"])
    def test_criticism_is_not_treated_as_fact_query(self):
        self.assertIn("limited, rule-based system", self.ask("How bad are you")["reply"])
    def test_pidgin_clarification(self):
        self.assertEqual("pcm", language("As how na"))
        self.assertIn("mean say", self.ask("As how na")["reply"])
    def test_bola_age(self):
        self.assertIn("74 years old", self.ask("How old is Tinubu")["reply"])
    def test_remi_age(self):
        self.assertIn("66 years old", self.ask("How old is Remi Tinubu")["reply"])
    def test_wife_followup_resolves_remi(self):
        self.ask("How old is Bola Tinubu", "follow")
        self.assertIn("Oluremi", self.ask("What about his wife?", "follow")["reply"])
    def test_local_calculator(self):
        self.assertEqual("450", calc("18% of 2500"))
        self.assertEqual("1,200", calc("25 * 48"))
    def test_local_time(self):
        self.assertIn("West Africa Time", self.ask("What time is it in Nigeria?")["reply"])
    def test_local_knowledge(self):
        self.assertIn("Abuja", self.ask("What is the capital of Nigeria?")["reply"])
    def test_live_data_is_not_fabricated(self):
        self.assertIn("can't verify live or current information", self.ask("What is the current price of every stock in Nigeria?")["reply"])
    def test_name_memory_is_session_scoped(self):
        self.ask("My name is Ada", "memory")
        self.assertIn("Ada", self.ask("What is my name?", "memory")["reply"])
        self.assertNotIn("Ada", self.ask("What is my name?", "other")["reply"])
    def test_no_external_model(self):
        self.assertFalse(self.ask("What is AI?")["model_used"])
    def test_age_calculation(self):
        self.assertEqual(74, age("1952-03-29", date(2026, 10, 24)))
    def test_dialogue_classification(self):
        self.assertEqual("broad_request", intent("I want to know everything"))
        self.assertEqual("clarification", intent("As how na"))

if __name__ == "__main__":
    unittest.main()
