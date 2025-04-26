from src.spotify_client import SpotifyClient
from src.toast_window import ToastWindow
import traceback
import sys
import time

def main():
    try:
        print("Starting application...")
        spotify_client = SpotifyClient()
        
        print("Creating window...")
        app = ToastWindow(spotify_client)
        
        # Force visibility
        app.root.deiconify()
        app.root.lift()
        app.root.attributes('-topmost', True)
        app.root.update()
        
        print("Running application...")
        app.run()
        
    except Exception as e:
        print(f"Error in main: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")  # Keep the console open

if __name__ == "__main__":
    main()