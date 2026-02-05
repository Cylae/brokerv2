import os
import sys
import subprocess
import time
from dotenv import load_dotenv

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_setup():
    if not os.path.exists(".env"):
        print("\n⚠️  WARNING: No '.env' file found!")
        print("   Please copy '.env.example' to '.env' and add your API keys.")
        time.sleep(2)

    load_dotenv()
    if not os.getenv("OPENROUTER_KEY"):
        print("\n⚠️  WARNING: OPENROUTER_KEY is missing.")
        time.sleep(2)

def main():
    check_setup()

    while True:
        clear_screen()
        print("=============================================")
        print("   🤖 AI TRADING SYSTEM - EASY LAUNCHER")
        print("=============================================")
        print("1. 📊 Launch Dashboard")
        print("2. 🚀 Run Auto-Trader (IBKR Mode)")
        print("3. 🪙 Run Auto-Trader (Binance Crypto Mode)")
        print("4. 🧪 Run Tests")
        print("5. ❌ Exit")
        print("=============================================")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == '1':
            print("\nStarting Dashboard...")
            try:
                subprocess.run(["streamlit", "run", "dashboard/app.py"], check=True)
            except KeyboardInterrupt:
                pass

        elif choice == '2':
            print("\nStarting Auto-Trader (IBKR)...")
            symbols = input("Enter symbols (default: AAPL TSLA): ").strip() or "AAPL TSLA"
            cmd = [sys.executable, "main.py", "--loop", "--mode", "IBKR", "--symbols"] + symbols.split()
            try:
                subprocess.run(cmd, check=True)
            except KeyboardInterrupt:
                pass

        elif choice == '3':
            print("\nStarting Auto-Trader (Binance)...")
            symbols = input("Enter pairs (default: BTC/USDT ETH/USDT): ").strip() or "BTC/USDT ETH/USDT"
            cmd = [sys.executable, "main.py", "--loop", "--mode", "BINANCE", "--symbols"] + symbols.split()
            try:
                subprocess.run(cmd, check=True)
            except KeyboardInterrupt:
                pass

        elif choice == '4':
            print("\nRunning Tests...")
            try:
                subprocess.run([sys.executable, "-m", "pytest"], check=True)
                input("\nTests Passed! Press Enter...")
            except subprocess.CalledProcessError:
                input("\nTests Failed. Press Enter...")

        elif choice == '5':
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
