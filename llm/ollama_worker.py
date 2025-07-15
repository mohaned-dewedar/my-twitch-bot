import asyncio
from llm.ollama_manager import OllamaManager



class OllamaWorkerQueue:
    def __init__(self, concurrency=2):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(concurrency)
        self.ollama = OllamaManager()

    async def enqueue(self, prompt, respond):
        print(f"🆕 Enqueued prompt: {prompt[:60]}...")
        await self.queue.put((prompt, respond))

    async def start(self):
        print("🚀 OllamaWorkerQueue started.")
        while True:
            prompt, respond = await self.queue.get()
            print(f"🎯 Dequeued prompt: {prompt[:60]}...")

            async with self.semaphore:
                print(f"🔍 Sending prompt to Ollama: {prompt[:60]}...")
                response, status = await self.ollama.ask(prompt)

                if status:
                    print(f"⚠️ Ollama error: {status}")
                else:
                    print(f"✅ Ollama response: {response[:60]}...")

                await respond(status if status else response)

            self.queue.task_done()
