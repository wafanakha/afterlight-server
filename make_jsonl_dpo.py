import json
import requests
import time
import os

GROQ_API_KEY = ""

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

BAD_TEACHER_MODEL = "llama-3.1-8b-instant" 

input_filename = "dataset_sft_final.jsonl"
sft_data = []

try:
    with open(input_filename, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                sft_data.append(json.loads(line))
    print(f"Berhasil memuat {len(sft_data)} baris dari {input_filename}!")
except FileNotFoundError:
    print(f"[!] Error: File {input_filename} tidak ditemukan. Pastikan file SFT Anda ada di folder ini!")
    exit()
# --------------------------------------

def generate_rejected_response(input_text):
    bad_teacher_prompt = f"""You are an AI generating BAD/REJECTED examples for a Direct Preference Optimization (DPO) dataset. 
Read the Game Engine Prompt below. You MUST generate a response that completely VIOLATES the game's comedic, lighthearted, and goofy tone.

Rules for the REJECTED response:
1. TONAL FAILURE: Make the narrative completely wrong for a comedy game. You can make it overly dramatic, generic boring fantasy (like a textbook), or unnecessarily violent/grimdark. Take yourself far too seriously and remove all humor.
2. STAT HALLUCINATION: In the JSON block, invent fake, serious RPG stats inside `player_stat_change`. Do not just use the standard stats. Hallucinate things like "corruption", "honor", "fear", "sanity", or "karma" (e.g., "corruption": 10).
3. MATH & LOGIC FAILURE: Explicitly contradict the D20 roll math. If the Total Score is lower than the DC, force "is_success": true anyway. If the roll is a critical 20, make them fail miserably. 
4. LORE VIOLATION: In the "items_given" or "equipment_given", reward the player with generic, serious, or edgy items that don't belong in a silly game (e.g., "Blade of Eternal Suffering", "Elven Mithril Armor", or "Health Potion").

Game Engine Prompt:
{input_text}

Generate only the bad narrative and the flawed JSON. Do not add markdown like ```json."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": BAD_TEACHER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a bad AI assistant generating intentionally incorrect and edgy responses."},
            {"role": "user", "content": bad_teacher_prompt}
        ],
        "temperature": 0.7 
    }
    
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
                # Waktu tunggu 10.5 menit jika menabrak limit
                wait_time = 630 
                print(f"      [!] Terkena Rate Limit Groq. Sistem beristirahat selama 10.5 menit ({wait_time} detik)...")
                time.sleep(wait_time)
                print("      [+] Istirahat selesai. Mencoba mengirim ulang...")
            else:
                print(f"\n[!] HTTP Error: {e}")
                return None
        except Exception as e:
            print(f"\n[!] Error menghubungi Groq API: {e}")
            return None
            
    return None

def main():
    output_filename = "dataset_dpo_final.jsonl"
    print(f"Memulai sintesis data DPO. Target file: {output_filename}")
    
    # Cek sudah sampai mana file DPO dibuat (agar bisa dilanjutkan jika terputus)
    start_index = 0
    if os.path.exists(output_filename):
        with open(output_filename, 'r', encoding='utf-8') as f:
            start_index = sum(1 for _ in f)
        print(f"File {output_filename} sudah ada dengan {start_index} baris. Melanjutkan dari index {start_index}...")

    with open(output_filename, 'a', encoding='utf-8') as f:
        for i in range(start_index, len(sft_data)):
            row = sft_data[i]
            print(f"Memproses DPO Skenario {i+1}/{len(sft_data)}...")
            
            prompt_text = row["input"]
            chosen_text = row["output"]
            
            rejected_text = generate_rejected_response(prompt_text)
            
            if rejected_text:
                dpo_row = {
                    "prompt": prompt_text,
                    "chosen": chosen_text,
                    "rejected": rejected_text
                }
                f.write(json.dumps(dpo_row) + '\n')
                f.flush() 
                print(f"-> Skenario DPO {i+1} sukses dibuat!")
            else:
                print(f"-> Gagal memproses Skenario DPO {i+1}.")
            
            # Jeda 4 detik agar aman dari batas token per menit
            time.sleep(15)

    print(f"\n[SELESAI] Data DPO berhasil di-generate dan disimpan ke {output_filename}")

if __name__ == "__main__":
    main()