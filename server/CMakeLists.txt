cmake_minimum_required(VERSION 3.15)
project(afterlight_server CXX)

# Memaksa penggunaan standar C++17 sesuai proyek hell_adventure Anda
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. Tambahkan subdirektori llama.cpp agar CMake mengaturnya secara otomatis
add_subdirectory(vendor/llama.cpp)

# 2. Tentukan file C++ apa saja yang akan dikompilasi menjadi aplikasi
add_executable(server_app 
    main.cpp 
    LlamaManager.cpp
)

# 3. Hubungkan library utama llama ke aplikasi kita
target_link_libraries(server_app PRIVATE llama)

# 4. (Opsional tapi penting) Beri tahu lokasi header jika IntelliSense masih butuh bantuan
target_include_directories(server_app PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}/vendor/llama.cpp/include
    ${CMAKE_CURRENT_SOURCE_DIR}/vendor/llama.cpp/common
    ${CMAKE_CURRENT_SOURCE_DIR}/vendor/llama.cpp
)