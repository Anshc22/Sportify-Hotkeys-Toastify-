import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import time
import traceback
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class SpotifyClient:
    def __init__(self):
        # Initialize with empty values first
        self.auth_manager = type('EmptyAuth', (), {
            'client_id': None,
            'client_secret': None,
            'redirect_uri': 'http://localhost:8888/callback'
        })()
        self.sp = None
        
        # Try to load credentials
        credentials = self.load_credentials()
        
        if not credentials:
            print("No valid credentials found. Please add them in settings.")
            return
        
        # Only attempt authentication if we have credentials
        try:
            print("Starting Spotify authentication...")
            self.auth_manager = SpotifyOAuth(
                client_id=credentials['client_id'],
                client_secret=credentials['client_secret'],
                redirect_uri=credentials['redirect_uri'],
                scope='user-read-currently-playing user-modify-playback-state user-read-playback-state',
                cache_path='.spotify_cache',
                open_browser=True
            )
            
            # Force token refresh
            token_info = self.auth_manager.get_cached_token()
            if not token_info:
                print("No cached token found. Please authenticate in your browser...")
                auth_url = self.auth_manager.get_authorize_url()
                print(f"Please visit this URL to authorize: {auth_url}")
                
                try:
                    # Wait for authentication
                    code = self.auth_manager.get_auth_response()
                    token_info = self.auth_manager.get_access_token(code)
                    print("Authentication successful!")
                except Exception as e:
                    print(f"Authentication failed: {e}")
                    self.sp = None
                    raise
            
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            
            # Test the connection
            try:
                me = self.sp.current_user()
                print(f"Successfully connected to Spotify as {me['display_name']}")
            except Exception as e:
                print(f"Error verifying Spotify connection: {e}")
                self.sp = None
                raise
                
        except Exception as e:
            print(f"Error during Spotify authentication: {e}")
            self.sp = None
            raise

    def load_credentials(self):
        """Load credentials from config file or environment variables"""
        try:
            # Try loading from config file first
            if os.path.exists('spotify_config.json'):
                with open('spotify_config.json', 'r') as f:
                    config = json.load(f)
                print("Using credentials from config file")
                return config
            
            # Fall back to environment variables
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if client_id and client_secret:
                print("Using credentials from environment variables")
                return {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': 'http://localhost:8888/callback'
                }
                    
            print("No valid credentials found")
            return None
                
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None

    def has_valid_credentials(self):
        """Check if valid credentials are present"""
        if hasattr(self, 'auth_manager'):
            # Print for debugging
            print(f"Checking credentials - ID: {self.auth_manager.client_id}, Secret: {bool(self.auth_manager.client_secret)}")
            return bool(self.auth_manager.client_id and self.auth_manager.client_secret)
        return False

    def get_current_track(self):
        """Get current track info with safety checks"""
        if not self.sp:
            return None
            
        try:
            playback = self.sp.current_playback()
            # print("Current playback:", playback)  # Debug print
            
            if playback and playback.get('item'):
                track_info = {
                    'track_id': playback['item']['id'],  # Add track ID
                    'title': playback['item']['name'],
                    'artist_list': [artist['name'] for artist in playback['item']['artists']],
                    'artist_uris': [artist['uri'].split(':')[-1] for artist in playback['item']['artists']],
                    'album_art_url': playback['item']['album']['images'][0]['url'] if playback['item']['album']['images'] else None,
                    'is_playing': playback['is_playing'],
                    'progress_ms': playback['progress_ms'],
                    'duration_ms': playback['item']['duration_ms'],
                    'is_shuffled': playback['shuffle_state'],
                    'volume': playback['device']['volume_percent'] if 'device' in playback else 100,
                    'timestamp': time.time()  # Add timestamp for progress interpolation
                }
                # print("Returning track info:", track_info)  # Debug print
                return track_info
                
            print("No current playback")  # Debug print
            return None
        except Exception as e:
            print(f"Error getting current track: {e}")
            traceback.print_exc()  # Add full traceback
            return None

    def seek_to_position(self, position_ms):
        if not self.sp:
            return
        try:
            self.sp.seek_track(position_ms)
        except Exception as e:
            print(f"Error seeking to position: {e}")

    def toggle_shuffle(self):
        if not self.sp:
            return
        try:
            current_playback = self.sp.current_playback()
            if current_playback:
                shuffle_state = current_playback['shuffle_state']
                self.sp.shuffle(not shuffle_state)
        except Exception as e:
            print(f"Error toggling shuffle: {e}")

    def previous_track(self):
        if not self.sp:
            return
        try:
            self.sp.previous_track()
        except Exception as e:
            print(f"Error skipping to previous track: {e}")

    def next_track(self):
        if not self.sp:
            return
        try:
            self.sp.next_track()
        except Exception as e:
            print(f"Error skipping to next track: {e}")

    def toggle_playback(self):
        if not self.sp:
            return
        try:
            current_playback = self.sp.current_playback()
            if current_playback:
                if current_playback['is_playing']:
                    self.sp.pause_playback()
                else:
                    self.sp.start_playback()
        except Exception as e:
            print(f"Error toggling playback: {e}")

    def toggle_volume(self):
        if not self.sp:
            return
        try:
            current_playback = self.sp.current_playback()
            if current_playback:
                current_volume = current_playback['device']['volume_percent']
                if current_volume > 0:
                    self.last_volume = current_volume
                    self.sp.volume(0)
                else:
                    self.sp.volume(getattr(self, 'last_volume', 100))
        except Exception as e:
            print(f"Error toggling volume: {e}")

    def open_artist_profile(self, uri):
        """Open artist profile in Spotify desktop app"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(f"spotify:artist:{uri}")
            else:  # macOS and Linux
                os.system(f"xdg-open 'spotify:artist:{uri}'")
        except Exception as e:
            print(f"Error opening artist profile: {e}")
            # Try alternative method
            try:
                import webbrowser
                webbrowser.open(f"spotify:artist:{uri}")
            except Exception as e:
                print(f"Error using alternative method: {e}")

    def set_volume(self, volume):
        """Set volume level (0-100)"""
        if not self.sp:
            return
        try:
            self.sp.volume(volume)
        except Exception as e:
            print(f"Error setting volume: {e}")

    def open_spotify_app(self, uri):
        try:
            os.system(f"start spotify:{uri}")
        except Exception as e:
            print(f"Error opening Spotify app: {e}")