import requests
import subprocess
import time
import threading

class OllamaChatBot:
    def __init__(self, model="llama3", host="http://localhost:11434"):
        self.model = model
        self.host = host
        self.model_running = False
        self.lock = threading.Lock()

    def is_model_ready(self):
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": "ping", "stream": False},
                timeout=2
            )
            return response.status_code == 200
        except:
            return False

    def start_model(self):
        # Run ollama in a subprocess, non-blocking
        def _run_model():
            subprocess.Popen(["ollama", "run", self.model])

        thread = threading.Thread(target=_run_model, daemon=True)
        thread.start()

    def ensure_model_running(self):
        with self.lock:
            if self.is_model_ready():
                self.model_running = True
                return True
            print("🔧 Starting Ollama model...")
            self.start_model()
            return False

    def wait_until_ready(self, timeout=30):
        for _ in range(timeout):
            if self.is_model_ready():
                self.model_running = True
                return True
            time.sleep(1)
        return False

    def get_response(self, prompt):
        if not self.ensure_model_running():
            return None, "Launching bot now..."

        if not self.model_running:
            self.wait_until_ready()

        try:
            res = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False}
            )
            res.raise_for_status()
            return res.json()["response"].strip(), None
        except Exception as e:
            return None, f"[LLM error] {e}"
