import json
import requests
import time
import random
GROQ_API_KEY = ""

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

TEACHER_MODEL = "llama-3.1-8b-instant"

SFT_INSTRUCTION = "You are the AI DM for a lighthearted, comedic D&D-style RPG. Write a short, funny 2nd-person narrative based EXACTLY on the GODOT SYSTEM VERDICT and the player's EQUIPPED GEAR. Then, output the JSON mechanical consequences wrapped in `CODE_BLOCK_START` and `CODE_BLOCK_END`."

try:
    with open("scenarios.json", "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    print(f"Berhasil memuat {len(scenarios)} skenario!")
except FileNotFoundError:
    print("[!] Error: File scenarios.json tidak ditemukan!")
    exit()

SILLY_WEAPONS = ["Rubber Chicken", "Wet Noodle", "Baguette of Doom", "Slightly Bent Spoon", "Frying Pan", "Bare Hands"]
SILLY_ARMORS = ["Cardboard Box", "Trash Can Lid", "Oversized Sweater", "Tin Foil Hat", "Nothing but Confidence"]
SILLY_ACCESSORIES = ["Fake Mustache", "Squeaky Shoes", "Googly Eye Glasses", "Glittery Cape"]

def generate_sft_response(godot_prompt):
    teacher_system_prompt = f"""You are an expert AI data generator crafting training data for a comedic RPG game.
Read the Godot Game Engine Prompt below.

You must generate a valid JSON object with EXACTLY two keys: "narrative" and "consequences".

1. "narrative": A short, highly comedic, and cheerful 2nd-person narrative reflecting the Player Action. 
   - You MUST obey the GODOT SYSTEM VERDICT.
   - You MUST vividly describe the player using their [Equipped Gear] if it logically fits the action.
2. "consequences": A JSON object containing the mechanical effects.

[Consequences Strict Rules]
- OMIT "dm_logic" entirely.
- "items_given" must be a list of objects containing: "id", "name", "description", "restore_hp" (int), and "restore_energy" (int).
- "equipment_given" must be a list of objects containing: "id", "name", "description", "type" (weapon/armor/accessory), and "stat_boosts" (object).
- "new_plot_id" and "new_location_id" must be strings or "none".

Return ONLY a valid JSON object matching this schema:
{{
  "narrative": "Your funny story here...",
  "consequences": {{
    "player_hp_change": 0,
    "player_energy_change": 0,
    "exp_gained": 0,
    "player_stat_change": {{
      "strength": 0, "dexterity": 0, "endurance": 0,
      "intelligence": 0, "awareness": 0, "charisma": 0, "luck": 0
    }},
    "target_hp_change": 0,
    "target_status_effect": "none",
    "items_given": [],
    "equipment_given": [],
    "new_plot_id": "none",
    "new_location_id": "none",
    "enemy_defeated": false
  }}
}}

Game Engine Prompt:
{godot_prompt}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Memaksa Groq untuk merespons dengan JSON murni
    payload = {
        "model": TEACHER_MODEL,
        "messages": [
            {"role": "system", "content": "You output strict JSON containing 'narrative' and 'consequences' for RPG training data."},
            {"role": "user", "content": teacher_system_prompt}
        ],
        "temperature": 0.8,
        "response_format": {"type": "json_object"}
    }
    
    max_retries = 10 
    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status() 
            
            raw_output = response.json()["choices"][0]["message"]["content"].strip()
            result_json = json.loads(raw_output)
            
            narrative = result_json.get("narrative", "")
            consequences_dict = result_json.get("consequences", {})
            consequences_string = json.dumps(consequences_dict, indent=2)
            
            final_stitched_output = f"{narrative}\n`CODE_BLOCK_START`\n{consequences_string}\n`CODE_BLOCK_END`"
            return final_stitched_output
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait_time = 100
                print(f"      [!] Terkena Rate Limit Groq. Istirahat 10.5 menit... (Percobaan {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"\n[!] HTTP Error: {e}")
                time.sleep(5)
        except json.JSONDecodeError as e:
            print(f"\n[!] AI gagal membuat JSON yang valid, mencoba lagi... ({e})")
            time.sleep(2)
        except Exception as e:
            print(f"\n[!] Error menghubungi Groq API: {e}")
            time.sleep(5)
            
    return None

def main():
    output_filename = "dataset_sft_groq_equipped.jsonl"
    print(f"Memulai sintesis data SFT dengan {TEACHER_MODEL}... Target file: {output_filename}")
    
    with open(output_filename, 'a', encoding='utf-8') as f:
        start_index = 0 
        
        for i in range(start_index, len(scenarios)):
            scene = scenarios[i]
            print(f"Memproses Skenario {i+1}/{len(scenarios)}...")
            
            d20_roll = random.randint(1, 20)
            if d20_roll >= 10:
                godot_verdict = "SUCCESS! The player's action succeeds brilliantly."
            else:
                godot_verdict = "FAILURE! The player's action fails in a comedic way."
            
            wep = random.choice(SILLY_WEAPONS)
            arm = random.choice(SILLY_ARMORS)
            acc = random.choice(SILLY_ACCESSORIES)
                
            godot_prompt = f"""[Game Context]
{scene['context']}

[Equipped Gear]
- Weapon: {wep}
- Armor: {arm}
- Accessory: {acc}

[GODOT SYSTEM VERDICT]
Player Action: "{scene['action']}"
Dice Roll: {d20_roll}. Therefore, this action is a {godot_verdict}

[JSON Template]
`CODE_BLOCK_START`
{{
  "player_hp_change": 0,
  "player_energy_change": 0,
  "exp_gained": 0,
  "player_stat_change": {{
    "strength": 0, "dexterity": 0, "endurance": 0,
    "intelligence": 0, "awareness": 0, "charisma": 0, "luck": 0
  }},
  "target_hp_change": 0,
  "target_status_effect": "none",
  "items_given": [],
  "equipment_given": [],
  "new_plot_id": "none",
  "new_location_id": "none",
  "enemy_defeated": false
}}
`CODE_BLOCK_END`"""
            
            ideal_output = generate_sft_response(godot_prompt)
            
            if ideal_output:
                data_row = {
                    "instruction": SFT_INSTRUCTION,
                    "input": godot_prompt,
                    "output": ideal_output
                }
                f.write(json.dumps(data_row) + '\n')
                f.flush() 
                print(f"-> Skenario {i+1} sukses! (Senjata: {wep})")
            else:
                print(f"-> Gagal memproses Skenario {i+1}.")
            
            # Groq sangat cepat, tetapi TPM-nya ketat. Jeda 4 detik cukup aman.
            time.sleep(4)

    print(f"\n[SELESAI] Data SFT berhasil di-generate ke {output_filename}")

if __name__ == "__main__":
    main()