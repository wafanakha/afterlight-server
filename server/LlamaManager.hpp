#pragma once
#include <string>
#include <vector>
#include <iostream>
#include <optional>

// Sertakan header utama dari pustaka llama.cpp
#include "llama.h" 

namespace hell_adventure {

class LlamaManager {
private:
    llama_model* model = nullptr;
    llama_context* ctx = nullptr;
    
    // Parameter standar untuk model dan konteks
    llama_model_params model_params;
    llama_context_params ctx_params;

public:
    LlamaManager();
    ~LlamaManager();

    // Memuat file GGUF dari penyimpanan lokal
    bool load_model(const std::string& model_path);

    // Fungsi utama: Menerima aksi pemain dan mengembalikan narasi + JSON
    std::optional<std::string> generate_response(const std::string& player_action);
};

} // namespace hell_adventure