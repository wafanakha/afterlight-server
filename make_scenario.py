import json
import requests
import time

GROQ_API_KEY = "" 
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

BATCH_SIZE = 20 
TOTAL_BATCHES = 15 # 

def generate_scenario_batch(batch_num):
    print(f"-> Meminta Batch {batch_num}/{TOTAL_BATCHES} ke Groq API...")
    
    # SYSTEM PROMPT DIPERBARUI DENGAN WORLD DATABASE BARU (D&D COMEDY)
    system_prompt = f"""You are an expert game designer for a classic D&D-style fantasy RPG that is highly comedic, satirical, and lighthearted. 
You need to generate training data scenarios for an AI DM.
Generate EXACTLY {BATCH_SIZE} scenarios.
Output MUST be a raw JSON array of objects. Do NOT wrap in ```json or add any other text. 

World Lore Context:
- Locations: Oakhaven Village (tavern is rebuilt weekly, locals are heavily insured), Muttering Woods (trees passively-aggressively judge your fashion), Mount Inconvenience (steep stairs, goblin camps, no handrails).
- Enemies: Unionized Goblin (takes mandated 15-minute breaks mid-fight), Insecure Mimic (disguised as a very unconvincing wobbly bar stool), Overencumbered Skeleton (rattles loudly, refuses to drop rusty spoons), Orc Life Coach (shouts motivational quotes while attacking), Dramatic Slime (reacts like a soap opera actor).
- NPCs: Mayor Bartholomew (corrupt but terrible at hiding it, drops monocle in soup), Archmage Fizzlebang (uses cosmic magic to ensure his tea is the perfect temperature), Iron Thumb Olga (muscular blacksmith who secretly just wants to knit), Sir Lancelittle (brave paladin with a terrible sense of direction).
- Equipment: Slightly Used Broadsword, Staff of Splinters, Tactical Frying Pan (sword/blunt), Chafing Chainmail, Vegan Leather Tunic, Hand-me-down Robes, Ring of Mild Convenience, Amulet of Pointless Advice, Lucky D20 Pendant.
- Items: Questionable Red Potion (tastes like cough syrup), Caffeinated Blue Elixir (makes teeth vibrate), Tactical Pocket Sand, Scroll of Fireball (warning: do not read indoors).
- Plot/Goals: Surviving a goblin crashing through the tavern window, finding a glowing MacGuffin for the Mayor, navigating Mount Inconvenience to confront a bandit king, discovering the 'evil' necromancer just wants friends.
- The vibe is classic fantasy trope parody, very goofy, wholesome, and slapstick. Zero dark/grimdark elements.

Schema for each object:
{{
  "context": "[Story Context]\\nMain Objective: <pick one from Plot/Goals or random funny objective>\\n\\n[Environmental Context]\\nLocation: <pick one of the lore locations>\\nEnemy: <Enemy Name> (Type: <humanoid/monstrosity/undead/ooze>) or None\\nNPC: <quirky npc or None>\\n\\n[Player Context]\\nHP: <1-100>, Level: <1-10>\\nStats: STR: <1-10> | DEX: <1-10> | END: <1-10> | INT: <1-10> | AWR: <1-10> | CHA: <1-10> | LCK: <1-10>\\nRaw D20 Roll: <random number 1-20>",
  "action": "<1st person player action, can use Items/Equipment, can be heroic, clumsy, or utterly ridiculous>"
}}

CRITICAL RULES:
1. Ensure high variety: Slapstick combat, funny dialogue, ridiculous puzzles, resting in cozy places, and absurd actions.
2. DO NOT use double quotes (") inside the values. If you need quotes, use single quotes (').
3. The JSON must be perfectly valid."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": system_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 6000 
    }

    max_retries = 5 
    
    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status() 
            
            raw_text = response.json()["choices"][0]["message"]["content"].strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            scenarios_array = json.loads(raw_text)
            return scenarios_array
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait_time = 20 * (attempt + 1)
                print(f"   [!] Terkena Rate Limit (429). Menunggu {wait_time} detik sebelum mencoba lagi (Percobaan {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"[!] HTTP Error pada Batch {batch_num}: {e}")
                break
        except Exception as e:
            print(f"[!] Gagal parsing JSON pada Batch {batch_num}: {e}")
            break
            
    print(f"[!] Batch {batch_num} dilewati karena gagal terus-menerus.")
    return []

def main():
    all_scenarios = []
    
    for i in range(1, TOTAL_BATCHES + 1):
        batch_data = generate_scenario_batch(i)
        if batch_data:
            all_scenarios.extend(batch_data)
            print(f"   Berhasil mendapat {len(batch_data)} skenario. Total terkumpul: {len(all_scenarios)}")
        
        print("   -> Menunggu 10 detik untuk mendinginkan API...")
        time.sleep(10)
        
    with open("scenarios.json", "w", encoding="utf-8") as f:
        json.dump(all_scenarios, f, indent=4)
        
    print(f"\n[SELESAI] {len(all_scenarios)} skenario telah disimpan di 'scenarios.json'!")

if __name__ == "__main__":
    main()