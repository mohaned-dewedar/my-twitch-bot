import re
import time
from typing import Optional, Tuple
from data.smite import SmiteDataStore, SmiteTriviaEngine
from data.opentdb import OpenTDBClient, ApiQuestionQueue  
from data.custom import CustomTriviaLoader
import requests
import random
from html import unescape
import json
import os
from typing import Optional, Dict
from trivia.base import TriviaBase 

class SmiteTriviaHandler(TriviaBase):
    def __init__(self, data_store: SmiteDataStore):
        self.engine = SmiteTriviaEngine(data_store)

    def start(self) -> str:
        ability = self.engine.start_trivia()
        question = self.engine.get_current_question()

        if ability and question:
            return f"🎯 TRIVIA TIME! {question['question']} Type !answer GodName to answer!"
        else:
            return "❌ Failed to start trivia. No data loaded."

    def get_question(self) -> Optional[Dict]:
        return self.engine.get_current_question()

    def check_answer(self, answer: str, username: Optional[str] = None) -> str:
        if not self.engine.is_trivia_active():
            return "❌ No active trivia."

        is_correct, correct = self.engine.check_answer(answer)
        if is_correct:
            self.engine.end_trivia()
            return f"🎉 @{username} got it correct! {correct} is the right answer!"
        else:
            return f"❌ @{username} - That's not correct. Try again!"

    def is_active(self) -> bool:
        return self.engine.is_trivia_active()

    def end(self) -> str:
        question = self.engine.get_current_question()
        self.engine.end_trivia()
        correct = question['correct_answer'] if question else "unknown"
        return f"Trivia ended! The correct answer was: {correct}"

    def get_help(self) -> str:
        return """🎯 SMITE TRIVIA COMMANDS:
• !trivia smite - Start a new Smite trivia game
• !answer GodName - Answer the current trivia"""

class ApiTriviaHandler(TriviaBase):
    def __init__(self, use_custom=True):
        self.api_queue = ApiQuestionQueue(preload_amount=10)
        self.custom = CustomTriviaLoader() if use_custom else None
        self._question = None
        self._active = False

    def start(self) -> str:
        if self._active:
            return f"⚠️ Trivia already active: {self._question['question'] if self._question else 'unknown question'}"

        self._question = None  # 🧼 Reset last question
        self._active = True

        source = "custom" if self.custom and random.random() < 0.5 else "api"

        if source == "custom":
            qlist = self.custom.get("mcq")
            self._question = random.choice(qlist) if qlist else None

        if not self._question:
            self._question = self.api_queue.get_next()

        return f"📚 {self._question['question']}" if self._question else "❌ Failed to start trivia."


    def get_question(self):
        return self._question

    def check_answer(self, answer, username=None):
        if not self._active:
            return "❌ No trivia active."

        correct = self._question.get("answer") or self._question.get("correct_answer")
        if answer.strip().lower() == correct.strip().lower():
            self._active = False
            return f"✅ {answer} is correct!"
        return f"❌ {answer} is wrong. Try again!"

    def is_active(self):
        return self._active

    def end(self) -> str:
        self._active = False
        correct = self._question.get("answer") or self._question.get("correct_answer")
        self._question = None  # 💡 Clear for next round
        return f"Trivia ended. Correct answer: {correct}"

    def get_help(self):
        return """🎲 TRIVIA COMMANDS:
• !trivia — Get a random trivia question
• !answer <your answer> — Submit your answer
• You may get a custom or OpenTDB question depending on the round."""