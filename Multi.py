# launcher.py
import multiprocessing
import os
import sys
import traceback

def run_admin():
    try:
        print("Starting Admin Portal...")
        import admin
        config_path = os.path.join(os.path.dirname(__file__), 'urls.json')
        admin_portal = admin.AdminPortal(config_path)
        sys.exit(admin.app.exec_())
    except Exception as e:
        print(f"Error starting Admin Portal: {e}")
        traceback.print_exc()

def run_frontend():
    try:
        print("Starting Frontend...")
        import frontend
        config_path = os.path.join(os.path.dirname(__file__), 'urls.json')
        frontend.open_fullscreen_browser_with_features(config_path)
    except Exception as e:
        print(f"Error starting Frontend: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')  # Ensure proper start method on all platforms
    
    # Create two processes: one for Admin and one for Frontend
    admin_process = multiprocessing.Process(target=run_admin)
    frontend_process = multiprocessing.Process(target=run_frontend)

    # Start both processes
    admin_process.start()
    frontend_process.start()

    # Wait for both processes to finish
    admin_process.join()
    frontend_process.join()