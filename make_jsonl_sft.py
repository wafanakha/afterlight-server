import json
import requests
import time

# 1. Masukkan API Key Groq Anda di sini (JANGAN DIBAGIKAN KE PUBLIK)
GROQ_API_KEY = ""

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
TEACHER_MODEL = "llama-3.1-8b-instant"

# Instruksi SFT
SFT_INSTRUCTION = "You are the AI Dungeon Master for a lighthearted, comedic D&D-style RPG. Write a creative 2nd-person narrative based on the player's action and the system's dice roll outcome. Follow it with a JSON block wrapped in `CODE_BLOCK_START` and `CODE_BLOCK_END` containing the mechanical consequences."

try:
    with open("scenarios.json", "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    print(f"Berhasil memuat {len(scenarios)} skenario dari file scenarios.json!")
except FileNotFoundError:
    print("[!] Error: File scenarios.json tidak ditemukan di folder ini!")
    exit()


def generate_teacher_response(input_text):
    teacher_system_prompt = f"""You are an expert AI data generator. Read the Game Engine Prompt below.
You must generate a response consisting of exactly TWO parts:
1. A short, funny, and slapstick 2nd-person narrative reflecting the Player Action and the System Directive rules (evaluating the D20 roll + Stat against the DC). DO NOT wrap the narrative in quotes.
2. A JSON block wrapped EXACTLY in `CODE_BLOCK_START` and `CODE_BLOCK_END`.

JSON Schema MUST follow this exactly:
{{
  "dm_logic": {{
    "stat_chosen": "string (e.g., STR, DEX, CHA)",
    "stat_value": int,
    "dc_set": int,
    "total_score": int,
    "is_success": bool
  }},
  "player_hp_change": int (0 if no damage, negative for damage, positive for heal),
  "player_energy_change": int,
  "exp_gained": int (e.g., 10, 20, 50),
  "player_stat_change": {{
    "strength": int, "dexterity": int, "endurance": int, 
    "intelligence": int, "awareness": int, "charisma": int, "luck": int
  }},
  "target_hp_change": int,
  "target_status_effect": "string or null",
  "items_given": ["list", "of", "strings"],
  "equipment_given": ["list", "of", "strings"]
}}

Game Engine Prompt:
{input_text}

Generate only the narrative and the JSON. Do not add markdown like ```json."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": TEACHER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise data generation assistant for a comedic D&D RPG."},
            {"role": "user", "content": teacher_system_prompt}
        ],
        "temperature": 0.6 
    }
    
    # KITA NAIKKAN RETRY AGAR SCRIPT LEBIH TANGGUH DITINGGAL LAMA
    max_retries = 10 
    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status() 
            
            raw_output = response.json()["choices"][0]["message"]["content"].strip()
            raw_output = raw_output.replace("```json", "").replace("```", "")
            return raw_output.strip()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # KUNCI PERUBAHAN: Set waktu tunggu statis menjadi 10.5 menit (630 detik)
                wait_time = 630 
                print(f"      [!] Terkena Rate Limit Groq. Sistem beristirahat selama 10.5 menit ({wait_time} detik)... (Percobaan {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                print("      [+] Istirahat selesai. Mencoba mengirim ulang...")
            else:
                print(f"\n[!] HTTP Error: {e}")
                return None
        except Exception as e:
            print(f"\n[!] Error menghubungi Groq API: {e}")
            return None
            
    print("\n[!] Gagal memproses setelah mencoba maksimal 10 kali berturut-turut.")
    return None

def main():
    output_filename = "dataset_sft_final.jsonl"
    print(f"Memulai sintesis data. Target file: {output_filename}")
    
    with open(output_filename, 'a', encoding='utf-8') as f:
        # PENTING: Jika script Anda tadi mati di skenario 90, 
        # pastikan Anda mengubah angka 0 di bawah ini menjadi 89 agar tidak mengulang dari awal!
        start_index = 0 
        
        for i in range(start_index, len(scenarios)):
            scene = scenarios[i]
            print(f"Memproses Skenario {i+1}/{len(scenarios)}...")
            
            godot_input = f"{scene['context']}\n\nPlayer Action: \"{scene['action']}\"\n\n[System Directive]\nYou are the AI DM. \n1. Decide which Stat best fits the Player Action.\n2. Determine a logical Difficulty Class (DC) between 5 and 20.\n3. Calculate Total Score = Raw D20 Roll + Chosen Stat.\n4. If Total Score >= DC, the action is a SUCCESS. Otherwise, FAILURE.\n5. Write a comedic narrative based on this outcome, then output the JSON."
            
            ideal_output = generate_teacher_response(godot_input)
            
            if ideal_output:
                data_row = {
                    "instruction": SFT_INSTRUCTION,
                    "input": godot_input,
                    "output": ideal_output
                }
                f.write(json.dumps(data_row) + '\n')
                f.flush() 
                print(f"-> Skenario {i+1} sukses!")
            else:
                print(f"-> Gagal memproses Skenario {i+1}.")
            
            # Jeda 4 detik antar skenario agar aman dari batas token per menit
            time.sleep(4)

    print(f"\n[SELESAI] Data SFT berhasil di-generate dan disimpan ke {output_filename}")

if __name__ == "__main__":
    main()