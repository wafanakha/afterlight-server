#include "LlamaManager.hpp"
#include "llama.h"

namespace hell_adventure {

LlamaManager::LlamaManager() {
    // Inisialisasi backend llama.cpp (wajib dipanggil sekali di awal)
    llama_backend_init();
    
    model_params = llama_model_default_params();
    ctx_params = llama_context_default_params();
    
    // Alokasikan memori konteks yang cukup besar untuk narasi dan JSON
    ctx_params.n_ctx = 2048; 
}

LlamaManager::~LlamaManager() {
    // Membersihkan memori saat kelas dihancurkan
    if (ctx) {
        llama_free(ctx);
    }
    if (model) {
        llama_free_model(model);
    }
    llama_backend_free();
}

bool LlamaManager::load_model(const std::string& model_path) {
    std::cout << "[LLM] Memuat model dari: " << model_path << "\n";
    
    model = llama_load_model_from_file(model_path.c_str(), model_params);
    if (!model) {
        std::cerr << "[!] Gagal memuat file GGUF.\n";
        return false;
    }

    ctx = llama_new_context_with_model(model, ctx_params);
    if (!ctx) {
        std::cerr << "[!] Gagal membuat konteks model.\n";
        return false;
    }

    std::cout << "[LLM] Model berhasil dimuat\n";
    return true;
}

std::optional<std::string> LlamaManager::generate_response(const std::string& player_action) {
    if (!model || !ctx) return std::nullopt;

    const llama_vocab* vocab = llama_model_get_vocab(model);

    // 1. SIAPKAN PROMPT
    std::string system_instruction = "You are the AI Dungeon Master for a lighthearted, comedic D&D-style RPG. Write a creative 2nd-person narrative based on the player's action and the system's dice roll outcome. Follow it with a JSON block wrapped in `CODE_BLOCK_START` and `CODE_BLOCK_END` containing the mechanical consequences.";
    
    std::string formatted_prompt = 
        "System: " + system_instruction + "\n\n" +
        "User: " + player_action + "\n\n" +
        "Assistant: ";

    // 2. TOKENISASI TEKS
    std::vector<llama_token> tokens_list(formatted_prompt.length() + 1);
    int n_tokens = llama_tokenize(vocab, formatted_prompt.c_str(), formatted_prompt.length(), tokens_list.data(), tokens_list.size(), true, false);
    
    if (n_tokens < 0) {
        tokens_list.resize(-n_tokens);
        n_tokens = llama_tokenize(vocab, formatted_prompt.c_str(), formatted_prompt.length(), tokens_list.data(), tokens_list.size(), true, false);
    }
    tokens_list.resize(n_tokens);

    // 3. EVALUASI DAN GENERASI (CARA BARU & AMAN)
    std::string final_output = "";
    
    // Alokasikan memori batch dengan kapasitas yang cukup (ambil yang lebih besar antara prompt atau 512)
    int max_batch_capacity = (n_tokens > 512) ? n_tokens : 512;
    llama_batch batch = llama_batch_init(max_batch_capacity, 0, 1);

    // Masukkan seluruh prompt ke dalam batch
    batch.n_tokens = n_tokens;
    for (int i = 0; i < n_tokens; i++) {
        batch.token[i] = tokens_list[i];
        batch.pos[i] = i;
        batch.n_seq_id[i] = 1;
        batch.seq_id[i][0] = 0;
        batch.logits[i] = false; // Kita tidak butuh memprediksi kata saat sedang membaca prompt...
    }
    batch.logits[n_tokens - 1] = true; // ...kecuali pada token terakhir untuk mulai membalas!

    if (llama_decode(ctx, batch) != 0) {
        std::cerr << "Llama decode gagal membaca prompt.\n";
        llama_batch_free(batch);
        return std::nullopt;
    }

    // Inisialisasi Sampler
    struct llama_sampler* sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
    llama_sampler_chain_add(sampler, llama_sampler_init_greedy());

    int n_cur = n_tokens;
    int n_max = n_tokens + 500; // Batas balasan maksimal 500 token
    
    while (n_cur <= n_max) {
        llama_token new_token_id = llama_sampler_sample(sampler, ctx, -1); 
        
        // Gunakan nama fungsi baru sesuai saran compiler
        if (new_token_id == llama_vocab_eos(vocab)) {
            break; 
        }

        llama_sampler_accept(sampler, new_token_id);

        char buf[128];
        int n = llama_token_to_piece(vocab, new_token_id, buf, sizeof(buf), 0, true);
        if (n > 0) {
            final_output += std::string(buf, n);
            // Cetak langsung ke terminal seperti efek mesin ketik (opsional)
            std::cout << std::string(buf, n) << std::flush; 
        }

        // Siapkan memori batch dengan aman untuk token berikutnya
        batch.n_tokens = 0;
        batch.token[0] = new_token_id;
        batch.pos[0] = n_cur;
        batch.n_seq_id[0] = 1;
        batch.seq_id[0][0] = 0;
        batch.logits[0] = true;
        batch.n_tokens = 1;

        if (llama_decode(ctx, batch) != 0) {
            std::cerr << "Llama decode gagal pada iterasi ke-" << n_cur << "\n";
            break;
        }
        n_cur += 1;
    }

    std::cout << "\n";

    // Mencegah Memory Leak (sangat penting di C++)
    llama_sampler_free(sampler);
    llama_batch_free(batch);

    return final_output;
}

} // namespace hell_adventure