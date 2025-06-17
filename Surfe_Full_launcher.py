import subprocess
import sys
import os

def run_streamlit_app():
    try:
        print("🚀 Starting Surfe API Toolkit...")
        
        # Get the directory where this launcher script is located.
        # This will be your 'Surfe full' folder.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define the full path to the main_app.py script
        app_path = os.path.join(script_dir, "main_app.py")
        
        print(f"Project directory set to: {script_dir}")
        print(f"Attempting to run: {app_path}")
        
        # Run the streamlit command, forcing the working directory (cwd)
        # to be the folder where your project is.
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", app_path],
            cwd=script_dir 
        )
        
    except Exception as e:
        print(f"❌ Error launching Streamlit: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    run_streamlit_app()