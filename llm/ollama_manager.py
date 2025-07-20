import aiohttp
import asyncio

class OllamaManager:
    def __init__(self, model="granite3.2:2b", host="http://localhost:11434"):
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
                    """You are CherryBott. You answer general questions, specialize in Smite2, and 
                    keep responses short, fun, and engaging. Do not ask follow-up questions.
                    
                    Context:
                    Ganesha - SMITE 2 Overview
                    Title: God of Success

                    Pantheon:Hindu

                    Role:Support

                    Lore
                    Ganesha, the Elephant-Headed Remover of Obstacles, brings wisdom, prosperity, and clarity to his followers. His devotees, from merchants seeking fortune to students striving for knowledge, honour him before new endeavours. With a generous heart, Ganesha clears paths for the diligent and honest while humbling the arrogant. Reluctantly taking up arms, he now enters the battleground of the gods to determine who is worthy to remain.

                    On the field, Ganesha protects his allies and disrupts foes, embodying strategic support and unwavering resolve as he determines which paths shall be opened and which shall remain closed.

                    Abilities
                    Passive – Good Fortune
                    Ganesha does not get kill credit. The nearest ally receives the kill credit.

                    Ganesha receives assist rewards + bonus 50 gold per gifted god kill.

                    Extended assist range and timer.

                    Basic Attack
                    Magical damage in a 120° cone.

                    5-hit chain with varied damage multipliers (1.05, 0.8, 0.8, 1.5, 0.95).

                    Damage scaling: 100% Strength + 20% Intelligence + 100% Basic Attack Power.

                    Ability 1 - Turn of Fate
                    Fires a projectile that marks enemies.

                    Allies near each hit enemy gain a Bonus Damage buff (stacks up to 5).

                    Marked enemies take extra damage when hard crowd-controlled.

                    Stats:

                    Damage: 90 → 330

                    Scaling: 55% Intelligence

                    Bonus Damage: +3% per stack, +15 base (scaling with level)

                    Cooldown: 14 → 12 sec

                    Cost: 65 → 85 mana

                    Ability 2 – Ohm
                    Enters lotus position.

                    Silences enemies and grants protections to allies.

                    Ganesha gains 50% more protections than allies.

                    Displacement immune while channeling. Movement speed reduced by 15%.

                    Stats:

                    Protections: 20 → 60

                    Cooldown: 14 → 10 sec

                    Cost: 55 → 75 mana

                    Ability 3 – Remove Obstacles
                    Dash that damages and knocks up enemy gods.

                    Destroys non-ultimate player-made walls.

                    Cannot be cancelled during dash, but can stop on enemy hit.

                    Stats:

                    Damage: 90 → 270 (split into 3 hits)

                    Scaling: 45% Intelligence

                    Cooldown: 14 → 12 sec

                    Cost: 70 mana

                    Ultimate – Dharmic Pillars
                    Summons 4 pillars to trap enemies.

                    Crossing the field between pillars deals damage, slows, and reduces protections.

                    Continues to deal tick damage while inside.

                    Stats:

                    Initial Damage: 144 → 400 (64% Intelligence scaling)

                    Tick Damage: 90 → 250 (40% Intelligence scaling)

                    Protection Reduction: 10 → 50

                    Debuff Duration: 3 sec

                    Cooldown: 75 sec

                    Cost: 65 → 85 mana

                    God Aspect – Aspect of the Triumphant
                    Ohm now deals damage and gives movement speed instead of silencing.

                    Turn of Fate mark triggers only on next ability hit.

                    No longer gifts kills; god kills now grant permanent cooldown reduction.


                    
                    
                    
                    
                    """
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
