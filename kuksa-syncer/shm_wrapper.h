#ifndef SHM_WRAPPER_H
#define SHM_WRAPPER_H

#include <iostream>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <string>
#include <vector>
#include <map>
#include <cstring>
#include <atomic>
#include <thread>
#include <vector>
#include <csignal>

// Shared memory constants
const char* SHM_NAME = "/my_shm";
const int MAX_VARS = 10;
const int VAR_NAME_SIZE = 32;
const int VAR_VALUE_SIZE = 64;
const int METADATA_SIZE = 4;
const int ENTRY_SIZE = VAR_NAME_SIZE + VAR_VALUE_SIZE;
const int SHM_SIZE = METADATA_SIZE + (MAX_VARS * ENTRY_SIZE);

namespace shm_wrapper {

// Map to associate variable names with their pointers and types
std::map<std::string, std::pair<void*, std::string>> var_map;
void* shm_ptr = MAP_FAILED;
std::atomic<bool> run_thread(true);
std::thread shm_thread;

void handle_set_request(const std::string& var_name, const std::string& new_value_str) {
    if (var_map.find(var_name) == var_map.end()) {
        return;
    }

    auto& var_info = var_map[var_name];
    void* var_ptr = var_info.first;
    const std::string& type = var_info.second;

    try {
        if (type == "int") {
            *static_cast<std::atomic<int>*>(var_ptr) = std::stoi(new_value_str);
        } else if (type == "double") {
            *static_cast<std::atomic<double>*>(var_ptr) = std::stod(new_value_str);
        } else if (type == "string") {
            // Not implemented for atomic strings. Requires fixed-size buffers.
        }
    } catch (const std::exception& e) {
        // Handle conversion error
    }
}

void shm_loop() {
    while (run_thread) {
        if(shm_ptr == MAP_FAILED) {
            usleep(100000);
            continue;
        }
        int num_vars;
        memcpy(&num_vars, shm_ptr, METADATA_SIZE);

        if (num_vars > 0 && num_vars <= MAX_VARS) {
            for (int i = 0; i < num_vars; ++i) {
                char* entry_ptr = (char*)shm_ptr + METADATA_SIZE + i * ENTRY_SIZE;
                char var_name_buf[VAR_NAME_SIZE];
                memcpy(var_name_buf, entry_ptr, VAR_NAME_SIZE);
                std::string var_name(var_name_buf);

                if (var_map.count(var_name)) {
                    auto& var_info = var_map[var_name];
                    void* var_ptr = var_info.first;
                    const std::string& type = var_info.second;
                    char* value_ptr = entry_ptr + VAR_NAME_SIZE;

                    char current_value_buf[VAR_VALUE_SIZE];
                    memcpy(current_value_buf, value_ptr, VAR_VALUE_SIZE);
                    std::string current_value_str(current_value_buf);

                    if (current_value_str.rfind("SET:", 0) == 0) {
                        std::string new_val = current_value_str.substr(4);
                        handle_set_request(var_name, new_val);
                        memset(value_ptr, 0, VAR_VALUE_SIZE);
                    }

                    std::string value_str;
                    if (type == "int") {
                        value_str = std::to_string(*static_cast<std::atomic<int>*>(var_ptr));
                    } else if (type == "double") {
                        value_str = std::to_string(*static_cast<std::atomic<double>*>(var_ptr));
                    }
                    strncpy(value_ptr, value_str.c_str(), VAR_VALUE_SIZE - 1);
                    value_ptr[VAR_VALUE_SIZE - 1] = '\0';
                }
            }
        }
        usleep(100000); // 100ms
    }
}

void init() {
    int shm_fd = shm_open(SHM_NAME, O_RDWR, 0666);
    if (shm_fd == -1) {
        perror("shm_open");
        return;
    }

    shm_ptr = mmap(0, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shm_ptr == MAP_FAILED) {
        perror("mmap");
        close(shm_fd);
        return;
    }
    close(shm_fd);

    std::cout << "C++ app connected to shared memory." << std::endl;
    shm_thread = std::thread(shm_loop);
}

void cleanup() {
    run_thread = false;
    if (shm_thread.joinable()) {
        shm_thread.join();
    }
    if (shm_ptr != MAP_FAILED) {
        munmap(shm_ptr, SHM_SIZE);
    }
    shm_unlink(SHM_NAME);
}

void signal_handler(int signum) {
   cleanup();
   exit(signum);
}

// Macro to add a variable to the watch map
#define WATCH_VAR(var, type_str) \
    shm_wrapper::var_map[#var] = {&var, type_str};

#define INIT_SHM() \
    signal(SIGINT, shm_wrapper::signal_handler); \
    signal(SIGTERM, shm_wrapper::signal_handler); \
    shm_wrapper::init();

#define CLEANUP_SHM() \
    shm_wrapper::cleanup();

} // namespace shm_wrapper

#endif // SHM_WRAPPER_H
