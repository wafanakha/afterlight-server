from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MockServerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Baca data yang dikirim dari Godot
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request_json = json.loads(post_data.decode('utf-8'))
            print("\n" + "="*60)
            print("📥 MENDAPATKAN PROMPT DARI GODOT:")
            print("-" * 60)
            print(request_json.get("prompt", "Tidak ada key 'prompt' ditemukan."))
            print("="*60 + "\n")
        except Exception as e:
            print("Gagal membaca JSON dari Godot:", e)

        # 2. Siapkan Jawaban Palsu (Simulasi AI DM) - Tema D&D Komedi
        fake_narrative = "You loudly remind the Unionized Goblin that it is precisely 12:00 PM. The goblin gasps, drops his weapon mid-swing, and immediately sits down for his mandated lunch break. He even hands you some of his spare gear as an apology for almost violating labor laws!"
        
        # Simulasi JSON yang dikembalikan AI (Hadiah disesuaikan dengan database baru)
        fake_json_logic = {
            "dm_logic": {
                "stat_chosen": "CHA",
                "stat_value": 5,
                "dc_set": 10,
                "total_score": 15,
                "is_success": True
            },
            "player_hp_change": 0,
            "player_energy_change": -5,
            "exp_gained": 50,
            "player_stat_change": {
                "strength": 0, "dexterity": 0, "endurance": 0, 
                "intelligence": 0, "awareness": 0, "charisma": 1, "luck": 0
            },
            "target_hp_change": 0,
            "target_status_effect": "on lunch break",
            "items_given": ["questionable_red_potion"],
            "equipment_given": ["tactical_frying_pan"]
        }
        
        # 3. Rangkai dengan format `CODE_BLOCK_START` dan `CODE_BLOCK_END`
        response_text = f"{fake_narrative}\n`CODE_BLOCK_START`\n{json.dumps(fake_json_logic)}\n`CODE_BLOCK_END`"
        
        # 4. Bungkus dalam key "response" sesuai permintaan Godot
        final_response = {"response": response_text}
        
        # Ubah ke bytes untuk menghitung panjang karakter dengan akurat
        response_data = json.dumps(final_response).encode('utf-8')
        
        # 5. Kirim balik ke Godot dengan Content-Length
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_data))) 
        self.end_headers()
        
        self.wfile.write(response_data)

def run():
    server_address = ('127.0.0.1', 8080)
    httpd = HTTPServer(server_address, MockServerHandler)
    print("🚀 Mock Server AI (Versi D&D Komedi) berjalan di http://127.0.0.1:8080")
    print("Menunggu request dari Godot...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()