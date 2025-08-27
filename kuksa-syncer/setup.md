# C++ Debugger Utility Setup Guide

This guide will help you set up the required tools (`g++` and `gcc`) for running the C++ debugger utility on Windows, Linux, and macOS.

---

## Windows

### Using MinGW-w64 (Recommended)
1. Download the MinGW-w64 installer from: https://www.mingw-w64.org/downloads/
2. Run the installer and follow the prompts:
   - Architecture: x86_64
   - Threads: posix
   - Exception: seh
   - Build revision: latest
3. Add the `bin` directory (e.g., `C:\Program Files\mingw-w64\...\bin`) to your `PATH` environment variable.
4. Open a new Command Prompt and verify installation:
   ```sh
   g++ --version
   gcc --version
   ```

### Using MSYS2 (Alternative)
1. Download MSYS2 from: https://www.msys2.org/
2. Install and open the MSYS2 shell.
3. Update the package database:
   ```sh
   pacman -Syu
   ```
4. Install GCC and G++:
   ```sh
   pacman -S mingw-w64-x86_64-gcc
   ```
5. Add the MSYS2 `mingw64\bin` directory to your `PATH`.

---

## Linux (Ubuntu/Debian)

1. Open a terminal.
2. Update package lists:
   ```sh
   sudo apt update
   ```
3. Install GCC and G++:
   ```sh
   sudo apt install build-essential
   ```
4. Verify installation:
   ```sh
   g++ --version
   gcc --version
   ```

---

## macOS

### Using Homebrew (Recommended)
1. Install Homebrew if you haven't already:
   ```sh
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install GCC (includes G++):
   ```sh
   brew install gcc
   brew install gdb
   ```
3. Verify installation:
   ```sh
   g++ --version
   gcc --version
   ```

---

## Additional Notes
- Ensure `g++` and `gcc` are available in your system `PATH`.
- For debugging features, you may also need `gdb`:
  - **Windows (MSYS2):** `pacman -S mingw-w64-x86_64-gdb`
  - **Linux:** `sudo apt install gdb`
  - **macOS:** `brew install gdb`

---

If you encounter issues, please refer to the official documentation for your platform or ask for help.
