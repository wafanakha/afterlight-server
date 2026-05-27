#include "LlamaManager.hpp"
#include "httplib.h"
#include <iostream>

int main() {
    hell_adventure::LlamaManager llm;


    std::string model_path = "Llama-3.2-3B-Instruct.Q4_K_M.gguf"; 

    std::cout << "=== INISIALISASI MODEL===\n";
    if (!llm.load_model(model_path)) {
        std::cerr << "Gagal memuat Model\n";
        return 1;
    }

    httplib::Server svr;

    svr.Post("/generate", [&](const httplib::Request& req, httplib::Response& res) {
        std::cout << "\n[Menerima aksi dari Godot]: " << req.body << "\n";
        std::cout << "[Model sedang memproses...]\n";

        auto response = llm.generate_response(req.body);

        if (response.has_value()) {
            res.set_content(response.value(), "text/plain");
            std::cout << "[Respons berhasil dikirim ke Godot]\n";
        } else {
            res.status = 500;
            res.set_content("Error: Model gagal memproses.", "text/plain");
        }
    });

    std::cout << "=== SERVER AKTIF ===\n";
    std::cout << "Menunggu instruksi dari Godot di http://localhost:8080/generate ...\n\n";
    
    svr.listen("localhost", 8080);

    return 0;
}