#include "LlamaManager.hpp"
#include <iostream>

int main() {
    hell_adventure::LlamaManager llm;

    // PASTIKAN: Ubah string ini sesuai dengan lokasi dan nama file .gguf Anda!
    // Jika file gguf ada di luar folder server, gunakan path relatif seperti "../nama_model.gguf"
    std::string model_path = "Llama-3.2-3B-Instruct.Q4_K_M.gguf"; 

    std::cout << "=== MEMULAI SERVER HELL ADVENTURE ===\n";
    if (!llm.load_model(model_path)) {
        std::cerr << "Gagal memuat otak AI. Pastikan path file GGUF benar!\n";
        return 1;
    }

    // Simulasi aksi pemain dan hasil lemparan dadu dari Godot
    std::string player_action = "Action: The player tries to intimidate the goblin by doing a backflip, but trips on a rock. Dice Roll: 3 (Failure).";
    
    std::cout << "\n[Input Godot]: " << player_action << "\n";
    std::cout << "[AI sedang berpikir...]\n\n";

    // Memanggil fungsi yang sudah kita buat
    auto response = llm.generate_response(player_action);

    if (response.has_value()) {
        std::cout << "=== HASIL OUTPUT ===\n";
        std::cout << response.value() << "\n";
        std::cout << "====================\n";
    } else {
        std::cout << "AI gagal memberikan respons.\n";
    }

    return 0;
}