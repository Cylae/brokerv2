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
        print("   (The system will try to run with defaults/env vars if you have them set)")
        time.sleep(2)

    load_dotenv()
    if not os.getenv("OPENROUTER_KEY"):
        print("\n⚠️  WARNING: OPENROUTER_KEY is missing in your configuration.")
        print("   The AI components will not work without it.")
        time.sleep(2)

def main():
    check_setup()

    while True:
        clear_screen()
        print("=============================================")
        print("   🤖 AI TRADING SYSTEM - EASY LAUNCHER")
        print("=============================================")
        print("1. 📊 Launch Dashboard (Visual Interface)")
        print("2. 🚀 Run Auto-Trader (Continuous Loop)")
        print("3. 🧪 Run Tests (Check if everything works)")
        print("4. ❌ Exit")
        print("=============================================")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == '1':
            print("\nStarting Dashboard...")
            try:
                subprocess.run(["streamlit", "run", "dashboard/app.py"], check=True)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")

        elif choice == '2':
            print("\nStarting Auto-Trader...")
            symbols = input("Enter symbols to trade (space separated, default: AAPL TSLA): ").strip()
            if not symbols:
                symbols = "AAPL TSLA"

            # Construct command
            cmd = [sys.executable, "main.py", "--loop", "--symbols"] + symbols.split()

            try:
                subprocess.run(cmd, check=True)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")

        elif choice == '3':
            print("\nRunning Tests...")
            try:
                subprocess.run([sys.executable, "-m", "pytest"], check=True)
                input("\nTests Passed! Press Enter to continue...")
            except subprocess.CalledProcessError:
                input("\nTests Failed. Check errors above. Press Enter to continue...")
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")

        elif choice == '4':
            print("\nGoodbye!")
            break
        else:
            input("\nInvalid choice. Press Enter to try again...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
