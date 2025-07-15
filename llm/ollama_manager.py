import aiohttp
import asyncio

class OllamaManager:
    def __init__(self, model="tinydolphin", host="http://localhost:11434"):
        self.model = model
        self.host = host

    async def is_ready(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.host}/api/tags", timeout=2) as res:
                    return res.status == 200
        except:
            return False


    async def wait_until_ready(self, timeout=30):
        for _ in range(timeout):
            if await self.is_ready():
                return True
            await asyncio.sleep(1)
        return False

    async def ask(self, prompt: str):
        if not await self.is_ready():
            print("🧠 Ollama not ready, waiting...")
            if not await self.wait_until_ready():
                print("Ollama not ready after timeout.")
                return None, "Ollama model is not available. Try again soon."

        try:
            async with aiohttp.ClientSession() as session:
                print(f"📡 Asking Ollama: {prompt[:60]}...")
                updated_prompt = (
                    "You are CherryBott. You answer general questions, specialize in Smite2, and "
                    "keep responses short, fun, and engaging. Do not ask follow-up questions."
                )

                async with session.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,         # User input only
                        "system": updated_prompt, # System instructions
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as res:
                    res.raise_for_status()
                    data = await res.json()
                    return data["response"].strip(), None


        except Exception as e:
            import traceback
            traceback.print_exc()  # <-- Add this
            print(f" Exception during Ollama call: {e}")
            return None, f"[LLM error] {e}"
