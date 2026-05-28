#include "LlamaManager.hpp"
#include "httplib.h"
#include "json.hpp" 
#include <iostream>

using json = nlohmann::json;

int main() {
    hell_adventure::LlamaManager llm;

    std::string model_path = "game_master.gguf"; 

    std::cout << "=== MENGINISIALISASI OTAK AI ===\n";
    if (!llm.load_model(model_path)) {
        std::cerr << "Gagal memuat otak AI. Pastikan path file GGUF benar!\n";
        return 1;
    }

    httplib::Server svr;

    svr.Post("/generate", [&](const httplib::Request& req, httplib::Response& res) {
        std::cout << "\n[Menerima request JSON dari Godot]\n";
        
        try {
            json req_data = json::parse(req.body);
            std::string prompt_text = req_data["prompt"];
            
            std::cout << "[AI sedang memproses...]\n";

            auto response = llm.generate_response(prompt_text);

            if (response.has_value()) {
                json res_data;
                res_data["response"] = response.value();
                
                res.set_content(res_data.dump(), "application/json");
                std::cout << "[Respons JSON berhasil dikirim ke Godot]\n";
            } else {
                res.status = 500;
                res.set_content("{\"error\": \"AI gagal memproses\"}", "application/json");
            }
        } catch (const json::exception& e) {
            std::cerr << "[!] Error Parsing JSON: " << e.what() << '\n';
            res.status = 400;
            res.set_content("{\"error\": \"Format JSON request tidak valid\"}", "application/json");
        }
    });

    std::cout << "=== SERVER AKTIF ===\n";
    std::cout << "Menunggu instruksi berformat JSON di http://localhost:8080/generate ...\n\n";
    
    svr.listen("localhost", 8080);

    return 0;
}