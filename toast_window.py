        client_secret = self.client_secret_var.get().strip()
        
        # Don't validate if they're placeholder texts
        if client_id == "Enter your Spotify Client ID" or client_secret == "Enter your Spotify Client Secret":
            self.show_message("Please enter valid credentials!", error=True)
            return
        
        # Validate credentials format
        if not self.validate_credentials(client_id, client_secret):
            self.show_message("Invalid credentials format!", error=True)
            return
            
        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:8888/callback'
        }
        
        try:
            # Test the credentials before saving
            test_client = SpotifyClient()
            test_client.auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri='http://localhost:8888/callback',
                scope='user-read-currently-playing user-modify-playback-state user-read-playback-state'
            )
            
            # Try to get a token
            token = test_client.auth_manager.get_access_token(as_dict=False)
            if not token:
                self.show_message("Invalid credentials! Unable to authenticate.", error=True)
                return
                
            # If we get here, credentials are valid - save them
            with open('spotify_config.json', 'w') as f:
                json.dump(config, f)
            
            self.show_message("Settings saved!\nRestarting app...", error=False)
            self.root.after(1500, self.restart_app)
            
        except Exception as e:
            print(f"Error validating credentials: {e}")
            self.show_message("Invalid credentials! Please check and try again.", error=True)

    def restart_app(self):
        """Restart the application"""
            self.root.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def validate_credentials(self, client_id, client_secret):
        """Validate credential format"""
        # Check if credentials are not empty
        if not client_id or not client_secret:
            return
            
        # Check if client_id is 32 characters long and alphanumeric
        if len(client_id) != 32 or not client_id.isalnum():
            return
            
        # Check if client_secret is 32 characters long and alphanumeric
        if len(client_secret) != 32 or not client_secret.isalnum():
            return
            
        return True

    def show_message(self, message, error=False):
        """Show a temporary message in the settings panel"""
        # Remove any existing message
        for widget in self.settings_panel.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget('text').startswith(('Settings saved', 'Error', 'Invalid')):
                widget.destroy()
        
        msg_label = tk.Label(self.settings_panel,
                           text=message,
                           bg=self.bg_color,
                           fg=self.text_color if not error else '#FF0000',
                           font=('Segoe UI', 9))
        msg_label.pack(pady=5)
        self.root.after(3000, msg_label.destroy)

    def load_saved_color(self):
        """Load saved color theme"""
        try:
            with open('.custom_color', 'r') as f:
                self.text_color = f.read().strip()
        except:
            self.text_color = '#1DB954'  # Default Spotify green

    def on_entry_focus_in(self, event, placeholder):
        """Handle entry field focus in"""
        if event.widget.get() == placeholder:
            event.widget.delete(0, 'end')
            event.widget.configure(fg='#FFFFFF')
            if event.widget == self.client_secret_entry:
                event.widget.configure(show='•')

    def on_entry_focus_out(self, event, placeholder):
        """Handle entry field focus out"""
        if event.widget.get() == '':
            event.widget.insert(0, placeholder)
            event.widget.configure(fg='#666666')
            if event.widget == self.client_secret_entry:
                event.widget.configure(show='')

    def toggle_secret_visibility(self, event):
        """Toggle client secret visibility"""
        if self.client_secret_entry.cget('show') == '•':
            self.client_secret_entry.configure(show='')
            self.eye_button.configure(fg=self.text_color)
        else:
            self.client_secret_entry.configure(show='•')
            self.eye_button.configure(fg=self.artist_color)
            self.eye_button.configure(fg=self.artist_color)

    def get_monitor_info(self):
        """Get information about all connected monitors"""
        monitors = []
        
        if os.name == 'nt':  # Windows
            try:
                callback = get_monitor_callback(monitors)
                # Use c_bool instead of BOOL for the callback
                callback_type = WINFUNCTYPE(c_bool, HMONITOR, HDC, POINTER(RECT), LPARAM)
                callback_function = callback_type(callback)
                windll.user32.EnumDisplayMonitors(None, None, callback_function, 0)
        except Exception as e:
                print(f"Error enumerating monitors: {e}")
                self._fallback_monitor(monitors)
        else:
            self._fallback_monitor(monitors)
        
        # Ensure we have at least one monitor
        if not monitors:
            self._fallback_monitor(monitors)
            
        return monitors

    def _fallback_monitor(self, monitors):
        """Add fallback monitor info using root window dimensions"""
        monitors.append({
            'left': 0,
            'top': 0,
            'right': self.root.winfo_screenwidth(),
            'bottom': self.root.winfo_screenheight(),
            'width': self.root.winfo_screenwidth(),
            'height': self.root.winfo_screenheight()
        })

    def show_hotkeys(self, event=None):
        """Show hotkey configuration panel with slide animation"""
        if hasattr(self, 'hotkey_panel'):
            self.hide_hotkeys()
            return
            
        # Store original height
        self.original_height = self.root.winfo_height()
        
        # Update hotkey icon to current theme color
        self.hotkey_button.configure(fg=self.text_color)
        
        # Create hotkey panel frame with a single border and padding
        self.hotkey_panel = tk.Frame(self.frame, bg=self.bg_color, bd=2, relief='groove', padx=5, pady=5)
        self.hotkey_panel.pack(after=self.playback_frame, before=self.progress_frame, fill='x')  # Ensure it fills horizontally
        
        # Create a canvas for scrolling
        self.hotkey_canvas = tk.Canvas(self.hotkey_panel, bg=self.bg_color, highlightthickness=0)  # Remove highlight border
        self.hotkey_canvas.pack(side='left', fill='both', expand=True)
        
        # Create a scrollbar
        scrollbar = tk.Scrollbar(self.hotkey_panel, orient='vertical', command=self.hotkey_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        
        # Create a frame inside the canvas
        self.hotkey_content_frame = tk.Frame(self.hotkey_canvas, bg=self.bg_color)
        self.hotkey_canvas.create_window((0, 0), window=self.hotkey_content_frame, anchor='nw')
        
        # Create all the hotkey contents
        self.create_hotkey_contents()
        
        # Configure scrollbar
        self.hotkey_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Update the scroll region
        self.hotkey_content_frame.bind("<Configure>", lambda e: self.hotkey_canvas.configure(scrollregion=self.hotkey_canvas.bbox("all")))
        
        # Force an update to ensure dimensions are calculated
        self.root.update_idletasks()
        
        # Set a fixed height for the hotkey panel (doubled)
        self.hotkey_panel.configure(height=88)  # Increased height to double
        
        # Check dimensions
        panel_height = self.hotkey_panel.winfo_height()
        content_height = self.hotkey_content_frame.winfo_height()
        print(f"Hotkey panel height: {panel_height}, Content height: {content_height}")  # Debugging output
        
        # Animate panel sliding up
        def animate_slide(start_time):
            duration = 200
            elapsed = time.time() * 1000 - start_time
            
            if elapsed < duration:
                progress = elapsed / duration
                progress = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out
                
                new_height = self.original_height + (panel_height * progress)
                self.root.geometry(f'{self.width}x{int(new_height)}')
                
                self.root.after(16, lambda: animate_slide(start_time))
            else:
                self.root.geometry(f'{self.width}x{int(self.original_height + panel_height)}')
        
        animate_slide(time.time() * 1000)

    def hide_hotkeys(self):
        """Hide hotkey panel with smooth slide animation"""
        if hasattr(self, 'hotkey_panel'):
            panel_height = self.hotkey_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height
            
            def animate_hide(start_time):
                duration = 200
                elapsed = time.time() * 1000 - start_time
                
                if elapsed < duration:
                    progress = elapsed / duration
                    progress = progress * progress  # Quadratic ease-in
                    
                    remaining_height = panel_height * (1 - progress)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    
                    self.root.after(16, lambda: animate_hide(start_time))
                else:
                    self.hotkey_panel.destroy()
                    delattr(self, 'hotkey_panel')
                    self.hotkey_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
        
        animate_hide(time.time() * 1000)

    def create_hotkey_contents(self):
        """Create Discord-style hotkey configuration panel"""
        # Define hotkey configurations
        self.hotkeys = [
            ("Play/Pause", "Ctrl + Alt + Space"),
            ("Previous Track", "Ctrl + Alt + ←"),
            ("Next Track", "Ctrl + Alt + →"),
            ("Volume Up", "Ctrl + Alt + ↑"),
            ("Volume Down", "Ctrl + Alt + ↓")
        ]
        
        # Create hotkey entries
        for action, keys in self.hotkeys:
            hotkey_row = tk.Frame(self.hotkey_content_frame, bg=self.bg_color, bd=1, relief='flat', padx=5, pady=5)  
            hotkey_row.pack(fill='x', pady=2)
            
            # Action label
            action_label = tk.Label(hotkey_row,
                              text=action,
                              font=('Segoe UI', 9),
                              bg=self.bg_color,
                              fg='#FFFFFF',
                              width=20,  
                              anchor='w')
            action_label.pack(side='left', padx=(0, 10))
            
            # Hotkey display label
            key_label = tk.Label(hotkey_row,
                               text=keys,
                               font=('Segoe UI', 9),
                               bg=self.bg_color,
                               fg='#B3B3B3',
                               padx=8)
            key_label.pack(side='left', fill='y', expand=True)  # Allow it to fill the height

            # Edit button/icon
            edit_button = tk.Button(hotkey_row, text='✎', command=lambda label=key_label: self.assign_hotkey(label), bg=self.bg_color, fg='#FFFFFF', borderwidth=0, font=('Symbola', 10))
            edit_button.pack(side='left', padx=(10, 0))

            # Bind click event to assign new hotkey
            hotkey_row.bind('<Button-1>', lambda e, label=key_label: self.assign_hotkey(label))

        print("Hotkey contents created successfully.")  # Debugging output

    def assign_hotkey(self, label):
        """Assign a new hotkey when the user presses a key"""
        self.current_keys = []  # List to store pressed keys

        def on_key_press(event):
            key = event.keysym  # Get the key symbol
            if key not in self.current_keys and len(self.current_keys) < 3:
                self.current_keys.append(key)  # Add key to the list
            label.config(text=' + '.join(self.current_keys))  # Update the label with the new key combination
            
            # Save combination after three keys
            if len(self.current_keys) == 3:
                # Update the hotkeys list
                for i, (action, _) in enumerate(self.hotkeys):
                    if label.cget("text") == _:
                        self.hotkeys[i] = (action, ' + '.join(self.current_keys))  # Update the hotkey
                        print(f"Updated {action} to {' + '.join(self.current_keys)}")  # Debugging output
                        break
                self.root.unbind('<KeyPress>')  # Unbind the key press event

        def on_key_release(event):
            # Clear the current keys when the user releases a key
            self.current_keys.clear()
            self.root.unbind('<KeyRelease>')  # Unbind the key release event

        self.root.bind('<KeyPress>', on_key_press)  # Bind key press event
        self.root.bind('<KeyRelease>', on_key_release)  # Bind key release event
        print("Press up to three keys to assign them as a hotkey.")  # Debugging output

    def load_hotkeys(self):
        """Load hotkeys from file"""
        try:
            with open('.hotkeys.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                ("Play/Pause", "Ctrl + Alt + Space"),
                ("Previous Track", "Ctrl + Alt + Left"),
                ("Next Track", "Ctrl + Alt + Right"),
            ]
        except Exception as e:
            print(f"Error loading hotkeys: {e}")
            return [
                ("Play/Pause", "Ctrl + Alt + Space"),
                ("Previous Track", "Ctrl + Alt + Left"),
                ("Next Track", "Ctrl + Alt + Right"),
            ]

    def save_hotkeys(self):
        """Save hotkeys to file"""
        try:
            with open('.hotkeys.json', 'w') as f:
                json.dump(self.hotkeys, f)
        except Exception as e:
            print(f"Error saving hotkeys: {e}")

    def create_ui(self):
        """Create all UI elements"""
        # Create main container
        self.container = tk.Frame(self.root, bg=self.bg_color)
        self.container.pack(fill='both', expand=True)
        
        # Add keyboard shortcuts
        self.bind_shortcuts()
        
        # Force initial size
        self.container.update_idletasks()
        
        # Create content frame
        self.frame = tk.Frame(self.container, bg=self.bg_color)
        self.frame.pack(fill='both', expand=True, padx=10, pady=8)
        
        # Create top row frame for title and controls
        self.top_row = tk.Frame(self.frame, bg=self.bg_color)
        self.top_row.pack(fill='x', expand=True)
        
        # Create album art label (after creating top_row)
        self.album_art_label = tk.Label(
            self.top_row,
            bg=self.bg_color,
            width=20,
            height=20,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=self.text_color,
            highlightbackground=self.text_color
        )
        self.album_art_label.pack(side='left', padx=(0, 8))
        
        # Create controls frame first (right side)
        self.controls = tk.Frame(self.top_row, bg=self.bg_color)
        self.controls.pack(side='right', padx=(0, 2))
        
        # Add vertical separator
        self.separator = tk.Frame(self.top_row, 
                                bg='#282828',  # Match color picker theme
                                width=1,
                                height=14)
        self.separator.pack(side='right', fill='y', padx=8, pady=6)
        
        # Create title label (after album art)
        self.title_label = tk.Label(self.top_row, 
                                  text="Not playing", 
                                  bg=self.bg_color,
                                  fg=self.title_color,
                                  font=('Segoe UI', 11, 'bold'),
                                  anchor='w')
        self.title_label.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Remove hover bindings since we want continuous scrolling
        # self.title_label.bind('<Enter>', self.start_title_scroll)
        # self.title_label.bind('<Leave>', self.stop_title_scroll)
        
        # Start continuous scrolling
        self.scroll_offset = 0
        self.scroll_paused = False
        self.continuous_scroll()
        
        # Create window control buttons
        button_style = {
            'bg': self.bg_color,
            'font': ('Segoe UI', 12),
            'width': 2,
            'pady': 3
        }
        
        # Add hotkey button before settings button
        self.hotkey_button = tk.Label(self.controls, 
                                   text="⌘",  # Command symbol
                                   fg=self.artist_color,
                                   bg=self.bg_color,
                                   font=('Segoe UI', 12),  # Adjusted font size
                                   width=2,
                                   pady=3)
        self.hotkey_button.pack(side='left', padx=(0, 1))
        self.hotkey_button.bind('<Button-1>', self.show_hotkeys)

        # Add hover effects like other buttons
        self.hotkey_button.bind('<Enter>', lambda e: self.hotkey_button.configure(fg=self.text_color))
        self.hotkey_button.bind('<Leave>', lambda e: self.hotkey_button.configure(
            fg=self.text_color if hasattr(self, 'hotkey_panel') else self.artist_color
        ))

        # Add tooltip
        self.add_tooltip(self.hotkey_button, "Hotkeys")

        # Add settings button with safer event binding
        self.settings_button = tk.Label(self.controls, 
                                      text="⚙",
                                      fg=self.artist_color,
                                      bg=self.bg_color,
                                      font=('Segoe UI', 12),
                                      width=2,
                                      pady=3)
        self.settings_button.pack(side='left', padx=(0, 1))
        self.settings_button.bind('<Button-1>', self.show_settings)
        
        # Add color picker button (before pin button, after separator)
        self.color_button = tk.Label(self.controls, 
                                   text="🎨",
                                   fg=self.artist_color,  # Start with gray
                                   bg=self.bg_color,
                                   font=('Segoe UI', 12),
                                   width=2,
                                   pady=3)
        self.color_button.pack(side='left', padx=(0, 1))
        self.color_button.bind('<Button-1>', self.show_color_picker)
        
        # Remove hover bindings - we'll handle color state directly
        # self.color_button.bind('<Enter>', lambda e: self.color_button.configure(fg=self.text_color))
        # self.color_button.bind('<Leave>', lambda e: self.color_button.configure(fg=self.artist_color))
        
        # Add pin button (after color button)
        self.pin_button = tk.Label(self.controls, 
                                text="⚲",
                                fg=self.text_color,
                                **button_style)
        self.pin_button.pack(side='left', padx=(0, 1))
        self.pin_button.bind('<Button-1>', self.toggle_pin)
        self.pin_button.bind('<Enter>', lambda e: self.pin_button.configure(fg=self.text_color))
        self.pin_button.bind('<Leave>', lambda e, b=self.pin_button: b.configure(
            fg=self.text_color if b.cget('text') == '⚲' else self.artist_color
        ))
        
        # Add minimize button
        self.minimize_button = tk.Label(self.controls, 
                                      text="−",
                                      fg=self.artist_color,
                                      **button_style)
        self.minimize_button.pack(side='left', padx=(0, 1))
        self.minimize_button.bind('<Button-1>', self.minimize_window)
        
        # Add close button
        self.close_button = tk.Label(self.controls, 
                                   text="×",
                                   fg=self.artist_color,
                                   **button_style)
        self.close_button.pack(side='left')
        self.close_button.bind('<Button-1>', lambda e: self.root.quit())
        
        # Add tooltips to buttons
        self.add_tooltip(self.settings_button, "Settings")
        self.add_tooltip(self.color_button, "Theme")
        self.add_tooltip(self.pin_button, "Pin Window")
        self.add_tooltip(self.minimize_button, "Minimize")
        self.add_tooltip(self.close_button, "Close")
        
        
        # Create artist frame
        self.artist_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.artist_frame.pack(fill='x', expand=True, pady=(2, 4))
        
        # Create playback frame
        self.playback_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.playback_frame.pack(fill='x', expand=True, pady=(2, 4))
        
        # Create progress frame and bar with fixed dimensions
        self.progress_frame = tk.Frame(self.frame, bg=self.bg_color, height=4)
        self.progress_frame.pack(fill='x', expand=True)
        self.progress_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.progress_bar = tk.Canvas(
            self.progress_frame,
            height=4,
            bg='#404040',
            highlightthickness=0,
            cursor='hand2'
        )
        self.progress_bar.pack(fill='x', pady=4)
        self.progress_bar.configure(height=4)  # Force height
        
        # Create progress indicator with fixed dimensions
        self.progress_indicator = self.progress_bar.create_rectangle(
            0, 0, 0, 4,
            fill=self.text_color,
            width=0,
            tags='progress_indicator'
        )
        
        # Force frame to maintain height
        self.progress_frame.configure(height=12)  # Account for padding
        self.progress_frame.pack_propagate(False)
        
        # Create time frame
        self.time_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.time_frame.pack(fill='x', expand=True)
        
        # Create time labels
        self.current_time = tk.Label(self.time_frame,
                                   text="0:00",
                                   bg=self.bg_color,
                                   fg=self.artist_color,
                                   font=('Segoe UI', 9))
        self.current_time.pack(side='left')
        
        self.total_time = tk.Label(self.time_frame,
                                 text="0:00",
                                 bg=self.bg_color,
                                 fg=self.artist_color,
                                 font=('Segoe UI', 9))
        self.total_time.pack(side='right')
        
        # Create playback buttons
        button_configs = [
            {'text': '🔀', 'command': self.toggle_shuffle, 'size': 11, 'tooltip': 'Toggle Shuffle'},
            {'text': '⏮', 'command': self.spotify_client.previous_track, 'size': 11, 'tooltip': 'Previous Track'},
            {'text': '⏯', 'command': self.toggle_playback, 'size': 11, 'tooltip': 'Play/Pause'},
            {'text': '⏭', 'command': self.spotify_client.next_track, 'size': 11, 'tooltip': 'Next Track'},
            {'text': '🔊', 'command': self.toggle_volume, 'size': 11, 'tooltip': 'Mute/Unmute'}
        ]
        
        # Center playback controls
        spacer_left = tk.Frame(self.playback_frame, bg=self.bg_color)
        spacer_left.pack(side='left', expand=True)
        
        # Create playback buttons
        self.playback_buttons = []
        for i, config in enumerate(button_configs):
            btn = tk.Label(
                self.playback_frame,
                text=config['text'],
                bg=self.bg_color,
                fg=self.artist_color,
                font=('Segoe UI', config['size']),
                padx=8
            )
            btn.pack(side='left')
            
            # Add volume bar after volume button
            if i == 4:  # After the volume button
                # Add volume control frame
                self.volume_frame = tk.Frame(self.playback_frame, bg=self.bg_color)
                self.volume_frame.pack(side='left', padx=(2, 8))
                
                self.volume_bar = tk.Canvas(
                    self.volume_frame,
                    height=4,
                    bg='#404040',
                    highlightthickness=0,
                    cursor='hand2',
                    width=60  # Smaller width to fit beside button
                )
                self.volume_bar.pack(side='left', pady=8)  # Align vertically with buttons
                
                # Add volume indicator
                self.volume_bar.create_rectangle(
                    0, 0, 60, 4,
                    fill=self.text_color,
                    width=0,
                    tags='volume_indicator'
                )
                
                # Bind volume bar events
                self.volume_bar.bind('<Button-1>', self.on_volume_click)
                self.volume_bar.bind('<B1-Motion>', self.on_volume_drag)
                self.volume_bar.bind('<Enter>', self.on_volume_hover)
                self.volume_bar.bind('<Leave>', self.on_volume_leave)
            
            # Create tooltip with fixed size and style
            tooltip_text = config['tooltip']
            def create_tooltip(widget=btn, text=tooltip_text):
                tooltip = tk.Toplevel(self.root)  # Make root the parent
                tooltip.wm_overrideredirect(True)
                tooltip.wm_attributes('-topmost', True)
                
                label = tk.Label(
                    tooltip,
                    text=text,
                    bg='#282828',
                    fg='#FFFFFF',
                    font=('Segoe UI', 9),
                    padx=5,
                    pady=2
                )
                label.pack()
                
                # Position tooltip below button
                x = widget.winfo_rootx()
                y = widget.winfo_rooty() + widget.winfo_height() + 2
                
                # Center horizontally
                tooltip.update_idletasks()  # Ensure tooltip size is calculated
                x = x + (widget.winfo_width() // 2) - (tooltip.winfo_width() // 2)
                
                tooltip.geometry(f"+{x}+{y}")
                return tooltip
            
            btn.bind('<Enter>', lambda e, b=btn: setattr(b, 'tooltip', create_tooltip(b)))
            btn.bind('<Leave>', lambda e, b=btn: b.tooltip.destroy() if hasattr(b, 'tooltip') else None)
            
            # Update hover colors
            btn.bind('<Enter>', lambda e, b=btn: b.configure(fg=self.text_color))
            btn.bind('<Leave>', lambda e, b=btn, i=i: b.configure(
                fg=self.text_color if (i == 0 and self.is_shuffled) else self.artist_color
            ))
            
            btn.bind('<Button-1>', lambda e, cmd=config['command']: cmd())
            self.playback_buttons.append(btn)
        
        # Remove the old volume bar from time frame
        if hasattr(self, 'volume_frame') and self.volume_frame in self.time_frame.winfo_children():
            self.volume_frame.destroy()
        
        # Create update thread
        self.update_thread = threading.Thread(target=self.update_track_info, daemon=True)
        self.update_thread.start()
        
        # Bind drag events to frame and all its children
        self.frame.bind('<Button-1>', self.start_move)
        self.frame.bind('<B1-Motion>', self.on_move)
        self.frame.bind('<ButtonRelease-1>', self.stop_move)
        
        # Also bind to top_row and title_label specifically
        self.top_row.bind('<Button-1>', self.start_move)
        self.top_row.bind('<B1-Motion>', self.on_move)
        self.top_row.bind('<ButtonRelease-1>', self.stop_move)
        
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        self.title_label.bind('<ButtonRelease-1>', self.stop_move)
        
        # Add progress bar bindings
        self.progress_bar.bind('<Button-1>', self.on_progress_click)
        self.progress_bar.bind('<B1-Motion>', self.on_progress_drag)
        self.progress_bar.bind('<ButtonRelease-1>', self.on_progress_release)
        self.progress_bar.bind('<Enter>', self.on_progress_hover)
        self.progress_bar.bind('<Leave>', self.on_progress_leave)

    def add_tooltip(self, widget, text):
        """Add tooltip to widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            
            # Ensure tooltip appears above other windows
            tooltip.lift()
            tooltip.wm_attributes('-topmost', True)
            
            # Create tooltip label
            label = tk.Label(
                tooltip,
                text=text,
                bg='#282828',
                fg='#FFFFFF',
                font=('Segoe UI', 9),
                padx=5,
                pady=2
            )
            label.pack()
            
            # Get widget's position relative to screen
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            
            # Center tooltip horizontally relative to widget
            tooltip_width = label.winfo_reqwidth()
            widget_width = widget.winfo_width()
            x_position = x + (widget_width - tooltip_width) // 2
            
            # Position tooltip below the widget with a small gap
            y_position = y + widget.winfo_height() + 2
            
            # Set tooltip position
            tooltip.wm_geometry(f"+{x_position}+{y_position}")
            
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def create_border(self):
        """Create rounded corners for the window"""
        border_color = '#282828'
        self.root.configure(bg=border_color)
        
        if hasattr(self.root, '_root'):  # Check if running on Windows
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                style = windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
                style = style | 0x00080000  # WS_EX_LAYERED
                DWMWCP_ROUND = 2  # Define DWMWCP_ROUND with the appropriate value
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    33,  # DWMWA_WINDOW_CORNER_PREFERENCE
                    byref(c_int(DWMWCP_ROUND)),
                    sizeof(c_int)
                )
            except:
                pass

    def position_window(self):
        """Position window with saved coordinates or default position"""
        try:
            # Try to load saved position
            with open('.window_position', 'r') as f:
                x, y = map(int, f.read().split(','))
        except:
            # Use default position if no saved position exists
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - self.width - 20
            y = screen_height - self.height - 40
        
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')

    def save_window_position(self):
        """Save current window position"""
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            with open('.window_position', 'w') as f:
                f.write(f'{x},{y}')
        except Exception as e:
            print(f"Error saving window position: {e}")

    def load_window_position(self):
        """Load and apply saved window position with multi-monitor support"""
        try:
            with open('.window_position', 'r') as f:
                pos = f.read().strip().split(',')
                if len(pos) == 2:
                    x, y = map(int, pos)
                    
                    # Validate position is within any monitor bounds
                    valid_position = False
                    for monitor in self.monitors:
                        if (monitor['left'] <= x <= monitor['right'] - self.width and
                            monitor['top'] <= y <= monitor['bottom'] - self.height):
                            valid_position = True
                            break
                    
                    if valid_position:
                        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
                        return
                        
            # If no valid saved position, center on primary monitor
            self.center_on_primary_monitor()
            
        except Exception as e:
            print(f"Error loading window position: {e}")
            self.center_on_primary_monitor()

    def center_on_primary_monitor(self):
        """Center the window on the primary monitor"""
        primary = self.monitors[0]  # Primary monitor is typically first
        x = primary['left'] + (primary['width'] - self.width) // 2
        y = primary['top'] + (primary['height'] - self.height) // 2
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')

    def start_move(self, event):
        """Start window drag"""
        self.x = event.x_root - self.root.winfo_x()
        self.y = event.y_root - self.root.winfo_y()

    def on_move(self, event):
        """Handle window drag with edge snapping for all monitors"""
        if hasattr(self, 'x'):
            # Calculate new position
            x = event.x_root - self.x
            y = event.y_root - self.y
            
            # Check each monitor for edge snapping
            snapped = False
            for monitor in self.monitors:
                # Check left edge
                if abs(x - monitor['left']) < self.snap_threshold:
                    x = monitor['left']
                    self.snap_positions['x'] = 'left'
                    snapped = True
                    break
                    
                # Check right edge
                elif abs((x + self.width) - monitor['right']) < self.snap_threshold:
                    x = monitor['right'] - self.width
                    self.snap_positions['x'] = 'right'
                    snapped = True
                    break
                    
            if not snapped:
                self.snap_positions['x'] = None
                
            # Check vertical snapping for current monitor
            current_monitor = self.get_current_monitor(x, y)
            if current_monitor:
                # Top edge
                if abs(y - current_monitor['top']) < self.snap_threshold:
                    y = current_monitor['top']
                    self.snap_positions['y'] = 'top'
                # Bottom edge
                elif abs((y + self.height) - current_monitor['bottom']) < self.snap_threshold:
                    y = current_monitor['bottom'] - self.height
            else:
                    self.snap_positions['y'] = None
                    
            # Update window position
            self.root.geometry(f"+{x}+{y}")

    def get_current_monitor(self, x, y):
        """Determine which monitor the window is currently on"""
        for monitor in self.monitors:
            if (monitor['left'] <= x <= monitor['right'] and 
                monitor['top'] <= y <= monitor['bottom']):
                return monitor
        return self.monitors[0]  # Default to primary monitor

    def stop_move(self, event):
        """Stop window drag and finalize snapping with multi-monitor support"""
        if hasattr(self, 'x'):
            # Get current position
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            
            # Get current monitor
            current_monitor = self.get_current_monitor(x, y)
            
            # Apply monitor-specific snapping
            if current_monitor:
                # Horizontal snapping
                if abs(x - current_monitor['left']) < self.snap_threshold:
                    x = current_monitor['left']
                elif abs((x + self.width) - current_monitor['right']) < self.snap_threshold:
                    x = current_monitor['right'] - self.width
                
                # Vertical snapping
                if abs(y - current_monitor['top']) < self.snap_threshold:
                    y = current_monitor['top']
                elif abs((y + self.height) - current_monitor['bottom']) < self.snap_threshold:
                    y = current_monitor['bottom'] - self.height
            
            # Apply final position
            self.root.geometry(f"+{x}+{y}")
            
            # Clean up
            del self.x
            del self.y

    def minimize_window(self, event=None):
        if not self.minimized:
            self.normal_geometry = self.root.geometry()
            screen_width = self.root.winfo_screenwidth()
            self.root.geometry(f'{self.width}x{self.height}-{screen_width+100}+0')
            self.minimized = True
            self.show_taskbar_icon()
        else:
            self.root.geometry(self.normal_geometry)
            self.minimized = False
            if hasattr(self, 'taskbar_icon'):
                self.taskbar_icon.destroy()

    def show_taskbar_icon(self):
        self.taskbar_icon = tk.Toplevel(self.root)
        self.taskbar_icon.title("Toastify")
        self.taskbar_icon.geometry('1x1+0+0')
        self.taskbar_icon.bind('<Button-1>', self.minimize_window)
        self.taskbar_icon.overrideredirect(False)
        self.taskbar_icon.attributes('-toolwindow', True)
        self.taskbar_icon.withdraw()
        self.taskbar_icon.iconify()

    def update_track_info(self):
        """Update track information with faster polling"""
        # Don't update if only settings UI is visible
        if not self.full_ui_initialized:
            return
            
        last_track_id = None
        while True:
            try:
                track_info = self.spotify_client.get_current_track()
                
                if track_info:
                    # Check if track has changed
                    current_track_id = track_info.get('track_id')
                    track_changed = current_track_id != last_track_id
                    
                    if track_changed:
                        # Full update for track change
                        self.full_title = track_info.get('title', 'Not playing')
                        self.scroll_offset = 0
                        self.scroll_paused = False
                        
                        if track_info.get('album_art_url'):
                            self.root.after(0, lambda url=track_info['album_art_url']: 
                                          self.update_album_art(url))
                        last_track_id = current_track_id
                    
                    # Always update playback state and progress
                    def update_ui():
                        try:
                            is_playing = track_info.get('is_playing', False)
                            # Update play button color based on state
                            self.playback_buttons[2].configure(
                                text='⏸' if is_playing else '⏯',
                                fg=self.text_color if is_playing else self.artist_color
                            )
                            
                            # Immediate playback state update
                            self.playback_buttons[2].configure(
                                text='⏸' if track_info.get('is_playing', False) else '⏯'
                            )
                            
                            # Update progress with interpolation
                            if track_info.get('is_playing', False):
                                progress = track_info.get('progress_ms', 0)
                                # Add elapsed time since last update
                                progress += int((time.time() - track_info.get('timestamp', time.time())) * 1000)
                                self.update_progress_bar(progress, track_info.get('duration_ms', 1))
                            
                            if track_changed:
                                # Update title and artist only on track change
                                title = self.full_title
                                if len(title) > 20:  # Changed from 35
                                    self.title_label.config(text=title[:32])  # Initial truncated view
                                else:
                                    self.title_label.config(text=title)
                                
                                if 'artist_list' in track_info and 'artist_uris' in track_info:
                                    self.update_artist_labels(track_info['artist_list'], 
                                                           track_info['artist_uris'])
                            
                            # Update shuffle and volume state
                            self.is_shuffled = track_info.get('is_shuffled', False)
                            self.playback_buttons[0].configure(
                                fg=self.text_color if self.is_shuffled else self.artist_color
                            )
                            
                            if 'volume' in track_info:
                                self.update_volume_bar(track_info['volume'])
                    
                except Exception as e:
                            print(f"Error updating UI: {e}")
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.reset_display())
                
            except Exception as e:
                print(f"Error in update_track_info: {e}")
                
            time.sleep(0.1)  # Poll every 100ms instead of 1s

    def reset_display(self):
        """Reset display when no track is playing"""
        # Only update UI elements if full UI is initialized
        if not self.full_ui_initialized:
            return
            
        self.title_label.config(text="Not playing", fg=self.text_color)
        self.clear_artist_labels()
        self.update_progress_bar(0, 1)

    def toggle_pin(self, event=None):
        """Handle pin button state"""
        self.is_pinned = not self.is_pinned
        self.root.wm_attributes('-topmost', self.is_pinned)
        # Update pin button color
        self.pin_button.configure(
            fg=self.text_color if self.is_pinned else self.artist_color
        )

    def on_progress_hover(self, event):
        self.progress_bar.configure(cursor='hand2')

    def on_progress_leave(self, event):
        self.progress_bar.configure(cursor='')

    def format_time(self, ms):
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def get_click_position(self, event):
        bar_width = self.progress_bar.winfo_width()
        click_x = event.x
        # Ensure click_x is within bounds
        click_x = max(0, min(click_x, bar_width))
        return click_x / bar_width

    def on_progress_click(self, event):
        """Handle progress bar click with immediate visual feedback"""
        self.seeking = True
        position = self.get_click_position(event)
        # Update visuals immediately
        self.update_progress_visual(position)
        # Then seek
        if hasattr(self, 'current_duration') and self.current_duration:
            seek_position = int(position * self.current_duration)
            self.spotify_client.seek_to_position(seek_position)

    def on_progress_drag(self, event):
        if hasattr(self, 'seeking') and self.seeking:
            position = self.get_click_position(event)
            self.update_progress_visual(position)

    def on_progress_release(self, event):
        if hasattr(self, 'seeking') and self.seeking:
            position = self.get_click_position(event)
            if hasattr(self, 'current_duration') and self.current_duration:
                seek_position = int(position * self.current_duration)
                self.spotify_client.seek_to_position(seek_position)
            self.seeking = False

    def update_progress_visual(self, position):
        """Update progress bar with current theme color"""
        bar_width = self.progress_bar.winfo_width()
        progress_width = bar_width * position
        
        # Update progress bar position and color
        self.progress_bar.coords(
            'progress_indicator',
            0, 0, progress_width, self.progress_bar.winfo_height()
        )
        self.progress_bar.itemconfig('progress_indicator', fill=self.text_color)

    def update_progress_bar(self, progress_ms, duration_ms):
        """Update progress bar with current theme color"""
        if duration_ms > 0 and hasattr(self, 'progress_bar'):
            position = progress_ms / duration_ms
            bar_width = self.progress_bar.winfo_width()
            progress_width = bar_width * position
            
            # Force dimensions to stay constant
            self.progress_frame.configure(height=12)  # Account for padding
            self.progress_bar.configure(height=4)
            
            # Update progress bar with fixed dimensions
            self.progress_bar.coords(
                self.progress_indicator,
                0, 0, progress_width, 4
            )
            self.progress_bar.itemconfig(self.progress_indicator, fill=self.text_color)
            
            # Update time labels
            self.current_time.config(text=self.format_time(progress_ms))
            self.total_time.config(text=self.format_time(duration_ms))
            
            # Store current duration
            self.current_duration = duration_ms
        else:
            # Reset progress bar
            self.update_progress_visual(0)
            self.current_time.config(text="0:00")
            self.total_time.config(text="0:00")

    def toggle_shuffle(self):
        """Handle shuffle with immediate feedback"""
        self.is_shuffled = not self.is_shuffled
        # Update UI instantly
        self.playback_buttons[0].configure(
            fg=self.text_color if self.is_shuffled else self.artist_color
        )
        # Then toggle shuffle
        self.spotify_client.toggle_shuffle()

    def toggle_volume(self):
        """Handle volume with immediate feedback"""
        self.is_muted = not self.is_muted
        # Update UI instantly
        self.playback_buttons[4].configure(text='🔈' if self.is_muted else '🔊')
        # Then toggle volume
        self.spotify_client.toggle_volume()

    def start_title_scroll(self, event=None):
        """Start scrolling the title text when hovering"""
        if len(self.full_title) > 10:
            self.title_scroll_index = 0
            self.title_scroll_active = True
            self.scroll_title_text()  # Start scrolling immediately

    def stop_title_scroll(self, event=None):
        """Stop scrolling and reset title text"""
        self.title_scroll_active = False  # Remove hasattr check
        if len(self.full_title) > 35:
            truncated = self.full_title[:32] + '...'
            self.title_label.config(text=truncated)

    def scroll_title_text(self):
        """Scroll the title text with smooth animation"""
        if self.title_scroll_active:
            # Add padding between repetitions
            text = self.full_title + '          ' + self.full_title
            
            # Smoother scrolling with smaller steps
            pixels_per_step = 1
            display_text = text[self.title_scroll_index:self.title_scroll_index + 35]
            self.title_label.config(text=display_text)
            
            # Reset index when reaching the end of first title
            if self.title_scroll_index >= len(self.full_title):
                self.title_scroll_index = 0
            else:
                self.title_scroll_index += pixels_per_step
            
            # Higher refresh rate for smoother scrolling
            self.root.after(40, self.scroll_title_text)  # 25fps

    def update_artist_labels(self, artists, uris):
        """Update artist labels for current track"""
        # Clear existing labels FIRST
        self.clear_artist_labels()
        self.artist_labels = []  # Reset the list
        self.artist_uris = []    # Reset URIs list
        
        # Create new labels for each artist
        for i, (artist, uri) in enumerate(zip(artists, uris)):
            if i > 0:  # Add separator
                separator = tk.Label(self.artist_frame,
                                  text=",",
                                  bg=self.bg_color,
                                  fg=self.artist_color,
                                  font=('Segoe UI', 9))
                separator.pack(side='left', padx=(0, 0))
                self.artist_labels.append(separator)
            
            label = tk.Label(self.artist_frame,
                           text=artist,
                           bg=self.bg_color,
                           fg=self.artist_color,
                           font=('Segoe UI', 9),
                           cursor='hand2')
            label.pack(side='left', padx=(0, 0))
            
            # Store URI in the label for direct access
            label.uri = uri
            
            # Simplified event bindings with direct URI access
            label.bind('<Enter>', lambda e, lbl=label: lbl.configure(
                fg='#FFFFFF', 
                font=('Segoe UI', 9, 'underline')
            ))
            label.bind('<Leave>', lambda e, lbl=label: lbl.configure(
                fg=self.artist_color, 
                font=('Segoe UI', 9)
            ))
            label.bind('<Button-1>', lambda e, uri=uri: 
                      self.spotify_client.open_artist_profile(uri))
            
            self.artist_labels.append(label)
            self.artist_uris.append(uri)

    def clear_artist_labels(self):
        """Clear all existing artist labels"""
        for label in self.artist_labels:
            label.destroy()
        self.artist_labels.clear()  # Use clear() instead of reassignment
        self.artist_uris.clear()

    def on_volume_hover(self, event):
        self.volume_bar.configure(cursor='hand2')

    def on_volume_leave(self, event):
        self.volume_bar.configure(cursor='')

    def get_volume_position(self, event):
        bar_width = self.volume_bar.winfo_width()
        click_x = event.x
        click_x = max(0, min(click_x, bar_width))
        return click_x / bar_width

    def on_volume_click(self, event):
        """Handle volume click with immediate visual feedback"""
        position = self.get_volume_position(event)
        volume = int(position * 100)
        # Update visuals immediately
        self.update_volume_bar(volume)
        # Then set volume
        self.spotify_client.set_volume(volume)

    def on_volume_drag(self, event):
        """Handle volume drag with immediate visual feedback"""
        position = self.get_volume_position(event)
        volume = int(position * 100)
        # Update visuals immediately
        self.update_volume_bar(volume)
        # Then set volume
        self.spotify_client.set_volume(volume)

    def update_volume_bar(self, volume):
        """Update volume bar with current theme color"""
        if not hasattr(self, 'last_volume'):
            self.last_volume = volume
        
        bar_width = self.volume_bar.winfo_width()
        volume_width = bar_width * (volume / 100)
        
        # Update volume indicator with current theme color
        self.volume_bar.delete('volume_indicator')
        self.volume_bar.create_rectangle(
            0, 0, volume_width, 3,
            fill=self.text_color,  # Use current theme color
            width=0,
            tags='volume_indicator'
        )
        
        self.last_volume = volume

    def toggle_playback(self):
        """Handle play/pause with immediate feedback"""
        # Update UI instantly
        is_playing = self.playback_buttons[2].cget('text') == '⏸'
        self.playback_buttons[2].configure(
            text='⏯' if is_playing else '⏸'
        )
        # Then toggle playback
        self.spotify_client.toggle_playback() 

    def update_colors(self, base_color):
        """Update UI colors based on dominant color"""
        # Convert hex to RGB
        if isinstance(base_color, str):
            # Remove '#' and convert to RGB
            r = int(base_color[1:3], 16)
            g = int(base_color[3:5], 16)
            b = int(base_color[5:7], 16)
            base_color = (r, g, b)
        
        # Calculate brightness
        brightness = (base_color[0] * 299 + base_color[1] * 587 + base_color[2] * 114) / 1000
        
        # Create color scheme
        self.bg_color = f'#{base_color[0]:02x}{base_color[1]:02x}{base_color[2]:02x}'
        self.text_color = '#FFFFFF' if brightness < 128 else '#000000'
        self.artist_color = '#B3B3B3' if brightness < 128 else '#666666'
        
        # Update UI elements
        self.update_ui_colors()

    def update_ui_colors(self):
        """Apply color scheme to UI elements"""
        # Update all interactive elements with new accent color
        
        # Update progress bar color
        self.progress_bar.itemconfig(self.progress_indicator, fill=self.text_color)
        self.progress_bar.itemconfig('progress_indicator', fill=self.text_color)
        
        # Update volume bar color
        self.volume_bar.delete('volume_indicator')
        self.volume_bar.create_rectangle(
            0, 0, 
            self.volume_bar.winfo_width() * (self.last_volume if hasattr(self, 'last_volume') else 100) / 100, 
            3,
            fill=self.text_color,
            width=0,
            tags='volume_indicator'
        )
        
        # Update album art border
        self.album_art_label.configure(
            highlightcolor=self.text_color,
            highlightbackground=self.text_color
        )
        
        # Update active states for buttons
        if self.is_pinned:
            self.pin_button.configure(fg=self.text_color)
        
        if self.is_shuffled:
            self.playback_buttons[0].configure(fg=self.text_color)
        
        # Update play button if playing
        if self.playback_buttons[2].cget('text') == '⏸':
            self.playback_buttons[2].configure(fg=self.text_color)
        
        # Update hover states
        for btn in self.playback_buttons:
            btn.bind('<Enter>', lambda e, b=btn: b.configure(fg=self.text_color))
            
        self.pin_button.bind('<Enter>', lambda e: self.pin_button.configure(fg=self.text_color))
        self.color_button.bind('<Enter>', lambda e: self.color_button.configure(fg=self.text_color))
        
        # Update settings button if settings are open
        if hasattr(self, 'settings_open') and self.settings_open:
            self.settings_button.configure(fg=self.text_color)
            
        # Update color picker button if panel is open
        if hasattr(self, 'color_panel'):
            self.color_button.configure(fg=self.text_color)

    def update_album_art(self, url):
        """Update album artwork display"""
        try:
            # Download and resize image
            response = requests.get(url)
            img = Image.open(io.BytesIO(response.content))
            img = img.resize((20, 20), Image.Resampling.LANCZOS)  # Small square size
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update label
            self.album_art_label.configure(image=photo)
            self.album_art_label.image = photo  # Keep reference
                    except Exception as e:
            print(f"Error updating album art: {e}")
            self.album_art_label.configure(image='')

    def show_loading_animation(self):
        """Show Spotify-style loading animation with triple dots"""
        # Create loading frame
        self.loading_frame = tk.Frame(self.root, bg=self.bg_color)
        self.loading_frame.pack(fill='both', expand=True)
        
        # Create frame for dots
        self.dots_frame = tk.Frame(self.loading_frame, bg=self.bg_color)
        self.dots_frame.pack(expand=True)
        
        # Create three dots
        self.dots = []
        for i in range(3):
            dot = tk.Label(
                self.dots_frame,
                text="•",
                font=('Segoe UI', 14),
                bg=self.bg_color,
                fg=self.text_color
            )
            dot.pack(side='left', padx=2)
            self.dots.append(dot)
            
        # Start animation
        self.animate_loading()

    def animate_loading(self):
        """Animate the dots with smoother fade effect"""
        if hasattr(self, 'dots'):
            def fade(step=0):
                if not hasattr(self, 'dots'):
                    return
                
                # Smoother sine-based fade for each dot
                import math
                for i, dot in enumerate(self.dots):
                    # Use sine wave for smoother transitions
                    phase = (step + i * 8) % 24  # Longer cycle
                    opacity = (math.sin(phase * math.pi / 12) + 1) / 2  # Smooth sine wave
                    
                    # Update dot color with opacity
                    r = int(int(self.text_color[1:3], 16) * opacity)
                    g = int(int(self.text_color[3:5], 16) * opacity)
                    b = int(int(self.text_color[5:7], 16) * opacity)
                    color = f'#{r:02x}{g:02x}{b:02x}'
                    
                    dot.configure(fg=color)
                
                # Faster refresh rate for smoother animation
                self.root.after(33, lambda: fade(step + 1))  # ~30fps
            
            fade()

    def create_main_ui(self):
        """Create main UI after loading"""
        # Hide the root window initially
        self.root.withdraw()
        
        # Create all UI elements
        self.create_ui()
        
        # Remove loading animation
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            delattr(self, 'loading_frame')
            delattr(self, 'dots')
        
        # Set background color
        self.root.configure(bg=self.bg_color)
        
        # Load last position if exists
        self.load_window_position()
        
        # Force update to ensure proper layout
        self.root.update_idletasks()
        
        # Show window with all elements properly sized
        def show_ui():
            self.root.deiconify()
            self.root.update_idletasks()
        
        # Slight delay to ensure smooth transition
        self.root.after(100, show_ui)

    def show_color_picker(self, event=None):
        """Show integrated color picker panel with smooth slide animation"""
        if hasattr(self, 'color_panel'):
            self.hide_color_picker()
            return
            
        # Store original height
        self.original_height = self.root.winfo_height()
        
        # Update color picker icon to current theme color
        self.color_button.configure(fg=self.text_color)
        
        # Create color panel frame - insert BEFORE the progress frame
        self.color_panel = tk.Frame(self.frame, bg=self.bg_color)
        self.color_panel.pack(after=self.playback_frame, before=self.progress_frame)
        
        # Create all the color picker contents
        self.create_color_picker_contents()
        
        # Get panel height
        self.root.update_idletasks()
        panel_height = self.color_panel.winfo_height()
        
        # Start with panel hidden below
        self.root.geometry(f'{self.width}x{self.original_height}')
        
        # Animate panel sliding up with easing
        def animate_slide(current_height, start_time):
            duration = 200  # Animation duration in milliseconds
            elapsed = time.time() * 1000 - start_time
            
            if elapsed < duration:
                # Easing function (ease-out)
                progress = elapsed / duration
                progress = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out
                
                new_height = self.original_height + (panel_height * progress)
                self.root.geometry(f'{self.width}x{int(new_height)}')
                
                # Force progress bar height to stay constant
                self.progress_bar.configure(height=4)
                self.progress_frame.configure(height=12)
                
                self.root.after(16, lambda: animate_slide(current_height, start_time))  # ~60fps
            else:
                # Ensure final height is exact
                final_height = self.original_height + panel_height
                self.root.geometry(f'{self.width}x{final_height}')
                
                # Force progress bar height one final time
                self.progress_bar.configure(height=4)
                self.progress_frame.configure(height=12)
        
        # Start animation
        animate_slide(0, time.time() * 1000)

    def hide_color_picker(self):
        """Hide color picker panel with smooth slide animation"""
        if hasattr(self, 'color_panel'):
            panel_height = self.color_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If settings panel is open, account for its height
            if hasattr(self, 'settings_panel') and self.settings_open:
                base_height += self.settings_panel.winfo_height()
            
            def animate_hide(start_time):
                duration = 200
                elapsed = time.time() * 1000 - start_time
                
                if elapsed < duration:
                    progress = elapsed / duration
                    progress = progress * progress  # Quadratic ease-in
                    
                    remaining_height = panel_height * (1 - progress)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    
                    # Keep progress bar dimensions
                    self.progress_bar.configure(height=4)
                    self.progress_frame.configure(height=12)
                    
                    self.root.after(16, lambda: animate_hide(start_time))
                else:
                    # Cleanup color panel specifically
                    self.color_panel.destroy()
                    delattr(self, 'color_panel')
                    self.color_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    
                    # Final progress bar adjustment
                    self.progress_bar.configure(height=4)
                    self.progress_frame.configure(height=12)

            animate_hide(time.time() * 1000)

    def hide_settings(self):
        """Hide settings panel with slide animation"""
        try:
            if not self.settings_open or not hasattr(self, 'settings_panel'):
                return
                
            panel_height = self.settings_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If color panel is open, account for its height
            if hasattr(self, 'color_panel'):
                base_height += self.color_panel.winfo_height()
            
            def animate_hide(progress):
                if progress <= 1.0:
                    ease = progress * progress
                    remaining_height = panel_height * (1 - ease)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    self.root.after(16, lambda: animate_hide(progress + 0.05))
                else:
                    # Clean up but maintain color panel height if open
                    if hasattr(self, 'settings_panel'):
                        self.settings_panel.destroy()
                    self.settings_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    self.settings_open = False
                    
            animate_hide(0.0)
            
        except Exception as e:
            print(f"Error hiding settings: {e}")
            traceback.print_exc()
        
    def create_color_picker_contents(self):
        """Create the contents of the color picker panel"""
        # Add separator line that extends full width
        separator = tk.Frame(self.color_panel, height=1, bg='#282828')
        separator.pack(fill='x', padx=0)
        
        # Create inner frame with left alignment
        inner_content = tk.Frame(self.color_panel, bg=self.bg_color)
        inner_content.pack(fill='x', padx=10, anchor='w')
        
        # Add title with left alignment
        title_label = tk.Label(inner_content, 
                             text="Theme", 
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.bg_color,
                             fg='#FFFFFF')
        title_label.pack(anchor='w', pady=(5, 5))
        
        # Create single row for all controls
        control_row = tk.Frame(inner_content, bg=self.bg_color)
        control_row.pack(fill='x', anchor='w', pady=(0, 5))
        
        # Left side: Color preview and hex input
        left_section = tk.Frame(control_row, bg=self.bg_color)
        left_section.pack(side='left')
        
        # Color preview
        self.color_preview = tk.Frame(left_section, 
                                        width=20, 
                                        height=20, 
                                        bg=self.text_color,
                                        highlightthickness=1,
                                        highlightbackground='#282828',
                                        cursor='hand2')
        self.color_preview.pack(side='left')
        self.color_preview.pack_propagate(False)
        self.color_preview.bind('<Button-1>', self.show_color_dialog)
        
        # Hex input
        self.hex_var = tk.StringVar(value=self.text_color)
        hex_entry = tk.Entry(left_section, 
                           textvariable=self.hex_var,
                           width=8,
                           bg='#282828',
                           fg='#FFFFFF',
                           insertbackground='#FFFFFF',
                           relief='flat',
                           font=('Segoe UI', 9, 'bold'),
                           justify='center')
        hex_entry.pack(side='left', padx=(5, 15))
        hex_entry.configure(highlightthickness=0)
        hex_entry.bind('<Return>', lambda e: self.apply_color())
        
        # Right side: Buttons
        button_style = {
            'font': ('Segoe UI', 9, 'bold'),
            'bg': '#282828',
            'fg': '#FFFFFF',
            'padx': 8,    # Reduced from 12
            'pady': 4,    # Reduced from 6
            'cursor': 'hand2',
            'width': 6    # Reduced from 8
        }
        
        # Create buttons
        for text, command in [
            ("Reset", self.reset_color),
            ("Apply", self.apply_color)
        ]:
            btn = tk.Label(
                control_row,
                text=text,
                **button_style
            )
            btn.pack(side='right', padx=2)
            btn.bind('<Button-1>', lambda e, cmd=command: cmd())
            
            # Hover effects
            btn.bind('<Enter>', 
                    lambda e, b=btn: b.configure(bg='#383838'))
            btn.bind('<Leave>', 
                    lambda e, b=btn: b.configure(bg='#282828'))

    def update_color_preview(self, *args):
        """Update color preview from RGB values"""
        try:
            r = self.rgb_vars[0].get()
            g = self.rgb_vars[1].get()
            b = self.rgb_vars[2].get()
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_preview.configure(bg=color)
            self.hex_var.set(color)
        except:
            pass

    def apply_color(self):
        """Apply selected color"""
        new_color = self.hex_var.get()
        self.text_color = new_color
        
        # Save color
        with open('.custom_color', 'w') as f:
            f.write(new_color)
        
        # Update all UI elements with new color
        self.update_ui_colors()
        
        # Update color button to match new color
        self.color_button.configure(fg=self.text_color)
        
        # Don't close the window, just update the preview
        self.color_preview.configure(bg=new_color)

    def reset_color(self):
        """Reset to Spotify green"""
        self.text_color = '#1DB954'
        
        # Update color preview and hex input if color picker is open
        if hasattr(self, 'color_preview'):
            self.color_preview.configure(bg=self.text_color)
            self.hex_var.set(self.text_color)
        
        self.update_ui_colors()
        
        # Save default color
        with open('.custom_color', 'w') as f:
            f.write(self.text_color)

    def show_color_dialog(self, event=None):
        """Show system color picker dialog"""
        # Get color picker box position
        x = self.root.winfo_x() + self.root.winfo_width() + 10
        y = self.root.winfo_y()
        
        # Use colorchooser directly instead of tk.call
        color = colorchooser.askcolor(
            color=self.text_color,
            title="Choose Color",
            parent=self.root
        )
        
        if (color[1]):  # If color was selected (not cancelled)
            # Update preview and hex
            self.color_preview.configure(bg=color[1])
            self.hex_var.set(color[1])
            
            # Apply the color immediately
            self.text_color = color[1]
            self.update_ui_colors()
            
            # Update color button to match new color
            self.color_button.configure(fg=color[1])
            
            # Save the color
            with open('.custom_color', 'w') as f:
                f.write(color[1])

    def bind_shortcuts(self):
        """Bind keyboard shortcuts for playback control"""
        # Play/Pause - Ctrl + Alt + Space
        self.root.bind('<Control-Alt-space>', lambda e: self.toggle_playback())
        
        # Previous Track - Ctrl + Alt + Left
        self.root.bind('<Control-Alt-Left>', lambda e: self.spotify_client.previous_track())
        
        # Next Track - Ctrl + Alt + Right
        self.root.bind('<Control-Alt-Right>', lambda e: self.spotify_client.next_track())
        
        # Volume Up - Ctrl + Alt + Up
        self.root.bind('<Control-Alt-Up>', lambda e: self.adjust_volume(10))
        
        """Adjust volume by delta percent"""
        def adjust_volume(delta):
            if hasattr(self, 'last_volume'):
                new_volume = max(0, min(100, self.last_volume + delta))
                # Update volume bar visually
                self.update_volume_bar(new_volume)
                # Update Spotify volume
                self.spotify_client.set_volume(new_volume)
                # Store new volume
                self.last_volume = new_volume

    def continuous_scroll(self):
        """Continuously scroll the title text"""
        if hasattr(self, 'full_title') and len(self.full_title) > 20:  # Changed from 35
            if not self.scroll_paused:
                # Create scrolling text with padding
                scroll_text = self.full_title + "     "  # Removed double text
                text_width = len(scroll_text)
                
                # Calculate display position
                start_pos = self.scroll_offset % text_width
                end_pos = start_pos + 32  # Show 32 characters at a time
                
                # Get display text with wrap-around
                if end_pos <= text_width:
                    display_text = scroll_text[start_pos:end_pos]
        else:
                    # Wrap around to the beginning
                    overflow = end_pos - text_width
                    display_text = scroll_text[start_pos:] + scroll_text[:overflow]
                
                # Update label
                self.title_label.config(text=display_text)
                
                # Increment scroll position
                self.scroll_offset += 1
                
                # Add pause at the beginning of each cycle
                if self.scroll_offset % text_width == 0:
                    self.scroll_paused = True
                    self.root.after(2000, self.resume_scroll)  # 2 second pause
                    
        # Continue scrolling
        self.root.after(125, self.continuous_scroll)  # Faster scroll speed (50ms)

    def resume_scroll(self):
        """Resume scrolling after pause"""
        self.scroll_paused = False

    def show_settings(self, event=None):
        """Show or hide settings panel with slide animation"""
        try:
            print("Attempting to toggle settings...")  # Debug print
            if not self.root.winfo_exists():
                print("Window doesn't exist")  # Debug print
                return
                
            if hasattr(self, 'settings_open') and self.settings_open:
                print("Closing settings panel")  # Debug print
                self.hide_settings()
                return
        
            # Force window to be visible first
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.update()
            
            # Create panel after ensuring window is visible
        self.settings_panel = tk.Frame(self.frame, bg=self.bg_color)
            self.settings_panel.pack(after=self.playback_frame, before=self.progress_frame)
            
            print("Creating settings contents...")  # Debug print
        self.create_settings_contents()
        
            # Force geometry update
            self.root.update_idletasks()
            
            # Get accurate panel height after contents are created
            panel_height = self.settings_panel.winfo_reqheight()
            
            # Mark settings as open and store original height
            self.settings_open = True
            self.original_height = self.root.winfo_height()
            
            # Update settings icon
            self.settings_button.configure(fg=self.text_color)
            
            def animate_slide(progress):
                if progress <= 1.0:
                    # Ease out animation
                    ease = 1 - (1 - progress) * (1 - progress)
                    new_height = self.original_height + (panel_height * ease)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    # Ensure contents are visible by updating canvas scrollregion
                    self.root.update_idletasks()
                    self.root.after(16, lambda: animate_slide(progress + 0.05))
                else:
                    # Finalize animation with exact height
                    self.root.geometry(f'{self.width}x{int(self.original_height + panel_height)}')
                    
            animate_slide(0.0)
                
        except Exception as e:
            print(f"Error showing settings: {e}")
            traceback.print_exc()

    def hide_settings(self):
        """Hide settings panel with slide animation"""
        try:
            if not self.settings_open or not hasattr(self, 'settings_panel'):
                return
                
            panel_height = self.settings_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If color panel is open, account for its height
            if hasattr(self, 'color_panel'):
                base_height += self.color_panel.winfo_height()
            
            def animate_hide(progress):
                if progress <= 1.0:
                    ease = progress * progress
                    remaining_height = panel_height * (1 - ease)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    self.root.after(16, lambda: animate_hide(progress + 0.05))
                else:
                    # Clean up but maintain color panel height if open
                    if hasattr(self, 'settings_panel'):
                        self.settings_panel.destroy()
                    self.settings_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    self.settings_open = False
                    
            animate_hide(0.0)
            
        except Exception as e:
            print(f"Error hiding settings: {e}")
            traceback.print_exc()

    def create_settings_contents(self):
        """Create the contents of the settings panel"""
        # Move settings panel before progress bar
        if hasattr(self, 'progress_frame'):
            self.settings_panel.pack(before=self.progress_frame)  # Fixed this line
        
        # Add separator line that extends full width
        separator = tk.Frame(self.settings_panel, height=1, bg='#282828')
        separator.pack(fill='x', padx=0)
        
        # Create inner frame
        inner_content = tk.Frame(self.settings_panel, bg=self.bg_color)
        inner_content.pack(fill='x', padx=10)
        
        # Add title
        title_label = tk.Label(inner_content, 
                             text="Settings", 
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.bg_color,
                             fg='#FFFFFF')
        title_label.pack(anchor='w', pady=(5, 5))
        
        # Add a message if credentials are missing
        if not self.spotify_client.has_valid_credentials():
            msg_label = tk.Label(inner_content,
                               text="Please enter your Spotify API credentials to continue",
                bg=self.bg_color,
                               fg='#FFFFFF',
                               font=('Segoe UI', 9))
            msg_label.pack(anchor='w', pady=(0, 10))
        
        # Create input fields
        input_style = {
            'bg': '#282828',
            'fg': '#FFFFFF',
            'insertbackground': '#FFFFFF',
            'relief': 'flat',
            'font': ('Segoe UI', 9),
            'width': 35
        }
        
        # Client ID input with placeholder
        tk.Label(inner_content, text="Client ID:", 
                bg=self.bg_color, fg='#FFFFFF',
                font=('Segoe UI', 9)).pack(anchor='w')
        self.client_id_var = tk.StringVar(value=self.spotify_client.auth_manager.client_id or "Enter your Spotify Client ID")
        self.client_id_entry = tk.Entry(inner_content, 
                                      textvariable=self.client_id_var,
                                      **input_style)
        if not self.spotify_client.auth_manager.client_id:
            self.client_id_entry.configure(fg='#666666')
            self.client_id_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(e, "Enter your Spotify Client ID"))
            self.client_id_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(e, "Enter your Spotify Client ID"))
        self.client_id_entry.pack(fill='x', pady=(0, 5))

        # Client Secret input with eye toggle
        tk.Label(inner_content, text="Client Secret:", 
                bg=self.bg_color, fg='#FFFFFF',
                font=('Segoe UI', 9)).pack(anchor='w')
                
        secret_frame = tk.Frame(inner_content, bg=self.bg_color)
        secret_frame.pack(fill='x', pady=(0, 10))
        
        self.client_secret_var = tk.StringVar(value=self.spotify_client.auth_manager.client_secret or "Enter your Spotify Client Secret")
        self.client_secret_entry = tk.Entry(secret_frame, 
                                          textvariable=self.client_secret_var,
                                          show='•',
                                          **input_style)
        self.client_secret_entry.pack(side='left', fill='x', expand=True)
        
        if not self.spotify_client.auth_manager.client_secret:
            self.client_secret_entry.configure(fg='#666666', show='')
            self.client_secret_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(e, "Enter your Spotify Client Secret"))
            self.client_secret_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(e, "Enter your Spotify Client Secret"))

        # Add eye toggle button
        self.eye_button = tk.Label(secret_frame, 
                                 text="👁", 
                                 bg=self.bg_color,
                                 fg=self.artist_color,
                cursor='hand2',
                                 padx=5)
        self.eye_button.pack(side='right')
        self.eye_button.bind('<Button-1>', self.toggle_secret_visibility)
        
        # Button row with consistent sizing
        button_row = tk.Frame(inner_content, bg=self.bg_color)
        button_row.pack(fill='x', pady=(0, 5))
        
        # Save button
        save_btn = tk.Label(
            button_row,
            text="Save",
            font=('Segoe UI', 9, 'bold'),
            bg='#282828',
            fg='#FFFFFF',
            padx=12,
            pady=6,
            cursor='hand2'
        )
        save_btn.pack(side='right', padx=5)
        save_btn.bind('<Button-1>', lambda e: self.save_settings())
        save_btn.bind('<Enter>', lambda e: save_btn.configure(bg='#383838'))
        save_btn.bind('<Leave>', lambda e: save_btn.configure(bg='#282828'))

    def save_settings(self):
        """Save client credentials and validate"""
        client_id = self.client_id_var.get().strip()
        client_secret = self.client_secret_var.get().strip()
        
        # Don't validate if they're placeholder texts
        if client_id == "Enter your Spotify Client ID" or client_secret == "Enter your Spotify Client Secret":
            self.show_message("Please enter valid credentials!", error=True)
            return
        
        # Validate credentials format
        if not self.validate_credentials(client_id, client_secret):
            self.show_message("Invalid credentials format!", error=True)
            return
            
        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:8888/callback'
        }
        
        try:
            # Test the credentials before saving
            test_client = SpotifyClient()
            test_client.auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri='http://localhost:8888/callback',
                scope='user-read-currently-playing user-modify-playback-state user-read-playback-state'
            )
            
            # Try to get a token
            token = test_client.auth_manager.get_access_token(as_dict=False)
            if not token:
                self.show_message("Invalid credentials! Unable to authenticate.", error=True)
                return
                
            # If we get here, credentials are valid - save them
            with open('spotify_config.json', 'w') as f:
                json.dump(config, f)
            
            self.show_message("Settings saved!\nRestarting app...", error=False)
            self.root.after(1500, self.restart_app)
            
        except Exception as e:
            print(f"Error validating credentials: {e}")
            self.show_message("Invalid credentials! Please check and try again.", error=True)

    def restart_app(self):
        """Restart the application"""
            self.root.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def validate_credentials(self, client_id, client_secret):
        """Validate credential format"""
        # Check if credentials are not empty
        if not client_id or not client_secret:
            return
            
        # Check if client_id is 32 characters long and alphanumeric
        if len(client_id) != 32 or not client_id.isalnum():
            return
            
        # Check if client_secret is 32 characters long and alphanumeric
        if len(client_secret) != 32 or not client_secret.isalnum():
            return
            
        return True

    def show_message(self, message, error=False):
        """Show a temporary message in the settings panel"""
        # Remove any existing message
        for widget in self.settings_panel.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget('text').startswith(('Settings saved', 'Error', 'Invalid')):
                widget.destroy()
        
        msg_label = tk.Label(self.settings_panel,
                           text=message,
                           bg=self.bg_color,
                           fg=self.text_color if not error else '#FF0000',
                           font=('Segoe UI', 9))
        msg_label.pack(pady=5)
        self.root.after(3000, msg_label.destroy)

    def load_saved_color(self):
        """Load saved color theme"""
        try:
            with open('.custom_color', 'r') as f:
                self.text_color = f.read().strip()
        except:
            self.text_color = '#1DB954'  # Default Spotify green

    def on_entry_focus_in(self, event, placeholder):
        """Handle entry field focus in"""
        if event.widget.get() == placeholder:
            event.widget.delete(0, 'end')
            event.widget.configure(fg='#FFFFFF')
            if event.widget == self.client_secret_entry:
                event.widget.configure(show='•')

    def on_entry_focus_out(self, event, placeholder):
        """Handle entry field focus out"""
        if event.widget.get() == '':
            event.widget.insert(0, placeholder)
            event.widget.configure(fg='#666666')
            if event.widget == self.client_secret_entry:
                event.widget.configure(show='')

    def toggle_secret_visibility(self, event):
        """Toggle client secret visibility"""
        if self.client_secret_entry.cget('show') == '•':
            self.client_secret_entry.configure(show='')
            self.eye_button.configure(fg=self.text_color)
        else:
            self.client_secret_entry.configure(show='•')
            self.eye_button.configure(fg=self.artist_color)
            self.eye_button.configure(fg=self.artist_color)

    def get_monitor_info(self):
        """Get information about all connected monitors"""
        monitors = []
        
        if os.name == 'nt':  # Windows
            try:
                callback = get_monitor_callback(monitors)
                # Use c_bool instead of BOOL for the callback
                callback_type = WINFUNCTYPE(c_bool, HMONITOR, HDC, POINTER(RECT), LPARAM)
                callback_function = callback_type(callback)
                windll.user32.EnumDisplayMonitors(None, None, callback_function, 0)
        except Exception as e:
                print(f"Error enumerating monitors: {e}")
                self._fallback_monitor(monitors)
        else:
            self._fallback_monitor(monitors)
        
        # Ensure we have at least one monitor
        if not monitors:
            self._fallback_monitor(monitors)
            
        return monitors

    def _fallback_monitor(self, monitors):
        """Add fallback monitor info using root window dimensions"""
        monitors.append({
            'left': 0,
            'top': 0,
            'right': self.root.winfo_screenwidth(),
            'bottom': self.root.winfo_screenheight(),
            'width': self.root.winfo_screenwidth(),
            'height': self.root.winfo_screenheight()
        })

    def show_hotkeys(self, event=None):
        """Show hotkey configuration panel with slide animation"""
        if hasattr(self, 'hotkey_panel'):
            self.hide_hotkeys()
            return
            
        # Store original height
        self.original_height = self.root.winfo_height()
        
        # Update hotkey icon to current theme color
        self.hotkey_button.configure(fg=self.text_color)
        
        # Create hotkey panel frame with a single border and padding
        self.hotkey_panel = tk.Frame(self.frame, bg=self.bg_color, bd=2, relief='groove', padx=5, pady=5)
        self.hotkey_panel.pack(after=self.playback_frame, before=self.progress_frame, fill='x')  # Ensure it fills horizontally
        
        # Create a canvas for scrolling
        self.hotkey_canvas = tk.Canvas(self.hotkey_panel, bg=self.bg_color, highlightthickness=0)  # Remove highlight border
        self.hotkey_canvas.pack(side='left', fill='both', expand=True)
        
        # Create a scrollbar
        scrollbar = tk.Scrollbar(self.hotkey_panel, orient='vertical', command=self.hotkey_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        
        # Create a frame inside the canvas
        self.hotkey_content_frame = tk.Frame(self.hotkey_canvas, bg=self.bg_color)
        self.hotkey_canvas.create_window((0, 0), window=self.hotkey_content_frame, anchor='nw')
        
        # Create all the hotkey contents
        self.create_hotkey_contents()
        
        # Configure scrollbar
        self.hotkey_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Update the scroll region
        self.hotkey_content_frame.bind("<Configure>", lambda e: self.hotkey_canvas.configure(scrollregion=self.hotkey_canvas.bbox("all")))
        
        # Force an update to ensure dimensions are calculated
        self.root.update_idletasks()
        
        # Set a fixed height for the hotkey panel (doubled)
        self.hotkey_panel.configure(height=88)  # Increased height to double
        
        # Check dimensions
        panel_height = self.hotkey_panel.winfo_height()
        content_height = self.hotkey_content_frame.winfo_height()
        print(f"Hotkey panel height: {panel_height}, Content height: {content_height}")  # Debugging output
        
        # Animate panel sliding up
        def animate_slide(start_time):
            duration = 200
            elapsed = time.time() * 1000 - start_time
            
            if elapsed < duration:
                progress = elapsed / duration
                progress = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out
                
                new_height = self.original_height + (panel_height * progress)
                self.root.geometry(f'{self.width}x{int(new_height)}')
                
                self.root.after(16, lambda: animate_slide(start_time))
            else:
                self.root.geometry(f'{self.width}x{int(self.original_height + panel_height)}')
        
        animate_slide(time.time() * 1000)

    def hide_hotkeys(self):
        """Hide hotkey panel with smooth slide animation"""
        if hasattr(self, 'hotkey_panel'):
            panel_height = self.hotkey_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height
            
            def animate_hide(start_time):
                duration = 200
                elapsed = time.time() * 1000 - start_time
                
                if elapsed < duration:
                    progress = elapsed / duration
                    progress = progress * progress  # Quadratic ease-in
                    
                    remaining_height = panel_height * (1 - progress)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    
                    self.root.after(16, lambda: animate_hide(start_time))
                else:
                    self.hotkey_panel.destroy()
                    delattr(self, 'hotkey_panel')
                    self.hotkey_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
        
        animate_hide(time.time() * 1000)

    def create_hotkey_contents(self):
        """Create Discord-style hotkey configuration panel"""
        # Define hotkey configurations
        self.hotkeys = [
            ("Play/Pause", "Ctrl + Alt + Space"),
            ("Previous Track", "Ctrl + Alt + ←"),
            ("Next Track", "Ctrl + Alt + →"),
            ("Volume Up", "Ctrl + Alt + ↑"),
            ("Volume Down", "Ctrl + Alt + ↓")
        ]
        
        # Create hotkey entries
        for action, keys in self.hotkeys:
            hotkey_row = tk.Frame(self.hotkey_content_frame, bg=self.bg_color, bd=1, relief='flat', padx=5, pady=5)  
            hotkey_row.pack(fill='x', pady=2)
            
            # Action label
            action_label = tk.Label(hotkey_row,
                              text=action,
                              font=('Segoe UI', 9),
                              bg=self.bg_color,
                              fg='#FFFFFF',
                              width=20,  
                              anchor='w')
            action_label.pack(side='left', padx=(0, 10))
            
            # Hotkey display label
            key_label = tk.Label(hotkey_row,
                               text=keys,
                               font=('Segoe UI', 9),
                               bg=self.bg_color,
                               fg='#B3B3B3',
                               padx=8)
            key_label.pack(side='left', fill='y', expand=True)  # Allow it to fill the height

            # Edit button/icon
            edit_button = tk.Button(hotkey_row, text='✎', command=lambda label=key_label: self.assign_hotkey(label), bg=self.bg_color, fg='#FFFFFF', borderwidth=0, font=('Symbola', 10))
            edit_button.pack(side='left', padx=(10, 0))

            # Bind click event to assign new hotkey
            hotkey_row.bind('<Button-1>', lambda e, label=key_label: self.assign_hotkey(label))

        print("Hotkey contents created successfully.")  # Debugging output

    def assign_hotkey(self, label):
        """Assign a new hotkey when the user presses a key"""
        self.current_keys = []  # List to store pressed keys

        def on_key_press(event):
            key = event.keysym  # Get the key symbol
            if key not in self.current_keys and len(self.current_keys) < 3:
                self.current_keys.append(key)  # Add key to the list
            label.config(text=' + '.join(self.current_keys))  # Update the label with the new key combination
            
            # Save combination after three keys
            if len(self.current_keys) == 3:
                # Update the hotkeys list
                for i, (action, _) in enumerate(self.hotkeys):
                    if label.cget("text") == _:
                        self.hotkeys[i] = (action, ' + '.join(self.current_keys))  # Update the hotkey
                        print(f"Updated {action} to {' + '.join(self.current_keys)}")  # Debugging output
                        break
                self.root.unbind('<KeyPress>')  # Unbind the key press event

        def on_key_release(event):
            # Clear the current keys when the user releases a key
            self.current_keys.clear()
            self.root.unbind('<KeyRelease>')  # Unbind the key release event

        self.root.bind('<KeyPress>', on_key_press)  # Bind key press event
        self.root.bind('<KeyRelease>', on_key_release)  # Bind key release event
        print("Press up to three keys to assign them as a hotkey.")  # Debugging output

    def load_hotkeys(self):
        """Load hotkeys from file"""
        try:
            with open('.hotkeys.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                ("Play/Pause", "Ctrl + Alt + Space"),
                ("Previous Track", "Ctrl + Alt + Left"),
                ("Next Track", "Ctrl + Alt + Right"),
            ]
        except Exception as e:
            print(f"Error loading hotkeys: {e}")
            return [
                ("Play/Pause", "Ctrl + Alt + Space"),
                ("Previous Track", "Ctrl + Alt + Left"),
                ("Next Track", "Ctrl + Alt + Right"),
            ]

    def save_hotkeys(self):
        """Save hotkeys to file"""
        try:
            with open('.hotkeys.json', 'w') as f:
                json.dump(self.hotkeys, f)
        except Exception as e:
            print(f"Error saving hotkeys: {e}")

    def create_ui(self):
        """Create all UI elements"""
        # Create main container
        self.container = tk.Frame(self.root, bg=self.bg_color)
        self.container.pack(fill='both', expand=True)
        
        # Add keyboard shortcuts
        self.bind_shortcuts()
        
        # Force initial size
        self.container.update_idletasks()
        
        # Create content frame
        self.frame = tk.Frame(self.container, bg=self.bg_color)
        self.frame.pack(fill='both', expand=True, padx=10, pady=8)
        
        # Create top row frame for title and controls
        self.top_row = tk.Frame(self.frame, bg=self.bg_color)
        self.top_row.pack(fill='x', expand=True)
        
        # Create album art label (after creating top_row)
        self.album_art_label = tk.Label(
            self.top_row,
            bg=self.bg_color,
            width=20,
            height=20,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=self.text_color,
            highlightbackground=self.text_color
        )
        self.album_art_label.pack(side='left', padx=(0, 8))
        
        # Create controls frame first (right side)
        self.controls = tk.Frame(self.top_row, bg=self.bg_color)
        self.controls.pack(side='right', padx=(0, 2))
        
        # Add vertical separator
        self.separator = tk.Frame(self.top_row, 
                                bg='#282828',  # Match color picker theme
                                width=1,
                                height=14)
        self.separator.pack(side='right', fill='y', padx=8, pady=6)
        
        # Create title label (after album art)
        self.title_label = tk.Label(self.top_row, 
                                  text="Not playing", 
                                  bg=self.bg_color,
                                  fg=self.title_color,
                                  font=('Segoe UI', 11, 'bold'),
                                  anchor='w')
        self.title_label.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Remove hover bindings since we want continuous scrolling
        # self.title_label.bind('<Enter>', self.start_title_scroll)
        # self.title_label.bind('<Leave>', self.stop_title_scroll)
        
        # Start continuous scrolling
        self.scroll_offset = 0
        self.scroll_paused = False
        self.continuous_scroll()
        
        # Create window control buttons
        button_style = {
            'bg': self.bg_color,
            'font': ('Segoe UI', 12),
            'width': 2,
            'pady': 3
        }
        
        # Add hotkey button before settings button
        self.hotkey_button = tk.Label(self.controls, 
                                   text="⌘",  # Command symbol
                                   fg=self.artist_color,
                                   bg=self.bg_color,
                                   font=('Segoe UI', 12),  # Adjusted font size
                                   width=2,
                                   pady=3)
        self.hotkey_button.pack(side='left', padx=(0, 1))
        self.hotkey_button.bind('<Button-1>', self.show_hotkeys)

        # Add hover effects like other buttons
        self.hotkey_button.bind('<Enter>', lambda e: self.hotkey_button.configure(fg=self.text_color))
        self.hotkey_button.bind('<Leave>', lambda e: self.hotkey_button.configure(
            fg=self.text_color if hasattr(self, 'hotkey_panel') else self.artist_color
        ))

        # Add tooltip
        self.add_tooltip(self.hotkey_button, "Hotkeys")

        # Add settings button with safer event binding
        self.settings_button = tk.Label(self.controls, 
                                      text="⚙",
                                      fg=self.artist_color,
                                      bg=self.bg_color,
                                      font=('Segoe UI', 12),
                                      width=2,
                                      pady=3)
        self.settings_button.pack(side='left', padx=(0, 1))
        self.settings_button.bind('<Button-1>', self.show_settings)
        
        # Add color picker button (before pin button, after separator)
        self.color_button = tk.Label(self.controls, 
                                   text="🎨",
                                   fg=self.artist_color,  # Start with gray
                                   bg=self.bg_color,
                                   font=('Segoe UI', 12),
                                   width=2,
                                   pady=3)
        self.color_button.pack(side='left', padx=(0, 1))
        self.color_button.bind('<Button-1>', self.show_color_picker)
        
        # Remove hover bindings - we'll handle color state directly
        # self.color_button.bind('<Enter>', lambda e: self.color_button.configure(fg=self.text_color))
        # self.color_button.bind('<Leave>', lambda e: self.color_button.configure(fg=self.artist_color))
        
        # Add pin button (after color button)
        self.pin_button = tk.Label(self.controls, 
                                text="⚲",
                                fg=self.text_color,
                                **button_style)
        self.pin_button.pack(side='left', padx=(0, 1))
        self.pin_button.bind('<Button-1>', self.toggle_pin)
        self.pin_button.bind('<Enter>', lambda e: self.pin_button.configure(fg=self.text_color))
        self.pin_button.bind('<Leave>', lambda e, b=self.pin_button: b.configure(
            fg=self.text_color if b.cget('text') == '⚲' else self.artist_color
        ))
        
        # Add minimize button
        self.minimize_button = tk.Label(self.controls, 
                                      text="−",
                                      fg=self.artist_color,
                                      **button_style)
        self.minimize_button.pack(side='left', padx=(0, 1))
        self.minimize_button.bind('<Button-1>', self.minimize_window)
        
        # Add close button
        self.close_button = tk.Label(self.controls, 
                                   text="×",
                                   fg=self.artist_color,
                                   **button_style)
        self.close_button.pack(side='left')
        self.close_button.bind('<Button-1>', lambda e: self.root.quit())
        
        # Add tooltips to buttons
        self.add_tooltip(self.settings_button, "Settings")
        self.add_tooltip(self.color_button, "Theme")
        self.add_tooltip(self.pin_button, "Pin Window")
        self.add_tooltip(self.minimize_button, "Minimize")
        self.add_tooltip(self.close_button, "Close")
        
        
        # Create artist frame
        self.artist_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.artist_frame.pack(fill='x', expand=True, pady=(2, 4))
        
        # Create playback frame
        self.playback_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.playback_frame.pack(fill='x', expand=True, pady=(2, 4))
        
        # Create progress frame and bar with fixed dimensions
        self.progress_frame = tk.Frame(self.frame, bg=self.bg_color, height=4)
        self.progress_frame.pack(fill='x', expand=True)
        self.progress_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.progress_bar = tk.Canvas(
            self.progress_frame,
            height=4,
            bg='#404040',
            highlightthickness=0,
            cursor='hand2'
        )
        self.progress_bar.pack(fill='x', pady=4)
        self.progress_bar.configure(height=4)  # Force height
        
        # Create progress indicator with fixed dimensions
        self.progress_indicator = self.progress_bar.create_rectangle(
            0, 0, 0, 4,
            fill=self.text_color,
            width=0,
            tags='progress_indicator'
        )
        
        # Force frame to maintain height
        self.progress_frame.configure(height=12)  # Account for padding
        self.progress_frame.pack_propagate(False)
        
        # Create time frame
        self.time_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.time_frame.pack(fill='x', expand=True)
        
        # Create time labels
        self.current_time = tk.Label(self.time_frame,
                                   text="0:00",
                                   bg=self.bg_color,
                                   fg=self.artist_color,
                                   font=('Segoe UI', 9))
        self.current_time.pack(side='left')
        
        self.total_time = tk.Label(self.time_frame,
                                 text="0:00",
                                 bg=self.bg_color,
                                 fg=self.artist_color,
                                 font=('Segoe UI', 9))
        self.total_time.pack(side='right')
        
        # Create playback buttons
        button_configs = [
            {'text': '🔀', 'command': self.toggle_shuffle, 'size': 11, 'tooltip': 'Toggle Shuffle'},
            {'text': '⏮', 'command': self.spotify_client.previous_track, 'size': 11, 'tooltip': 'Previous Track'},
            {'text': '⏯', 'command': self.toggle_playback, 'size': 11, 'tooltip': 'Play/Pause'},
            {'text': '⏭', 'command': self.spotify_client.next_track, 'size': 11, 'tooltip': 'Next Track'},
            {'text': '🔊', 'command': self.toggle_volume, 'size': 11, 'tooltip': 'Mute/Unmute'}
        ]
        
        # Center playback controls
        spacer_left = tk.Frame(self.playback_frame, bg=self.bg_color)
        spacer_left.pack(side='left', expand=True)
        
        # Create playback buttons
        self.playback_buttons = []
        for i, config in enumerate(button_configs):
            btn = tk.Label(
                self.playback_frame,
                text=config['text'],
                bg=self.bg_color,
                fg=self.artist_color,
                font=('Segoe UI', config['size']),
                padx=8
            )
            btn.pack(side='left')
            
            # Add volume bar after volume button
            if i == 4:  # After the volume button
                # Add volume control frame
                self.volume_frame = tk.Frame(self.playback_frame, bg=self.bg_color)
                self.volume_frame.pack(side='left', padx=(2, 8))
                
                self.volume_bar = tk.Canvas(
                    self.volume_frame,
                    height=4,
                    bg='#404040',
                    highlightthickness=0,
                    cursor='hand2',
                    width=60  # Smaller width to fit beside button
                )
                self.volume_bar.pack(side='left', pady=8)  # Align vertically with buttons
                
                # Add volume indicator
                self.volume_bar.create_rectangle(
                    0, 0, 60, 4,
                    fill=self.text_color,
                    width=0,
                    tags='volume_indicator'
                )
                
                # Bind volume bar events
                self.volume_bar.bind('<Button-1>', self.on_volume_click)
                self.volume_bar.bind('<B1-Motion>', self.on_volume_drag)
                self.volume_bar.bind('<Enter>', self.on_volume_hover)
                self.volume_bar.bind('<Leave>', self.on_volume_leave)
            
            # Create tooltip with fixed size and style
            tooltip_text = config['tooltip']
            def create_tooltip(widget=btn, text=tooltip_text):
                tooltip = tk.Toplevel(self.root)  # Make root the parent
                tooltip.wm_overrideredirect(True)
                tooltip.wm_attributes('-topmost', True)
                
                label = tk.Label(
                    tooltip,
                    text=text,
                    bg='#282828',
                    fg='#FFFFFF',
                    font=('Segoe UI', 9),
                    padx=5,
                    pady=2
                )
                label.pack()
                
                # Position tooltip below button
                x = widget.winfo_rootx()
                y = widget.winfo_rooty() + widget.winfo_height() + 2
                
                # Center horizontally
                tooltip.update_idletasks()  # Ensure tooltip size is calculated
                x = x + (widget.winfo_width() // 2) - (tooltip.winfo_width() // 2)
                
                tooltip.geometry(f"+{x}+{y}")
                return tooltip
            
            btn.bind('<Enter>', lambda e, b=btn: setattr(b, 'tooltip', create_tooltip(b)))
            btn.bind('<Leave>', lambda e, b=btn: b.tooltip.destroy() if hasattr(b, 'tooltip') else None)
            
            # Update hover colors
            btn.bind('<Enter>', lambda e, b=btn: b.configure(fg=self.text_color))
            btn.bind('<Leave>', lambda e, b=btn, i=i: b.configure(
                fg=self.text_color if (i == 0 and self.is_shuffled) else self.artist_color
            ))
            
            btn.bind('<Button-1>', lambda e, cmd=config['command']: cmd())
            self.playback_buttons.append(btn)
        
        # Remove the old volume bar from time frame
        if hasattr(self, 'volume_frame') and self.volume_frame in self.time_frame.winfo_children():
            self.volume_frame.destroy()
        
        # Create update thread
        self.update_thread = threading.Thread(target=self.update_track_info, daemon=True)
        self.update_thread.start()
        
        # Bind drag events to frame and all its children
        self.frame.bind('<Button-1>', self.start_move)
        self.frame.bind('<B1-Motion>', self.on_move)
        self.frame.bind('<ButtonRelease-1>', self.stop_move)
        
        # Also bind to top_row and title_label specifically
        self.top_row.bind('<Button-1>', self.start_move)
        self.top_row.bind('<B1-Motion>', self.on_move)
        self.top_row.bind('<ButtonRelease-1>', self.stop_move)
        
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        self.title_label.bind('<ButtonRelease-1>', self.stop_move)
        
        # Add progress bar bindings
        self.progress_bar.bind('<Button-1>', self.on_progress_click)
        self.progress_bar.bind('<B1-Motion>', self.on_progress_drag)
        self.progress_bar.bind('<ButtonRelease-1>', self.on_progress_release)
        self.progress_bar.bind('<Enter>', self.on_progress_hover)
        self.progress_bar.bind('<Leave>', self.on_progress_leave)

    def add_tooltip(self, widget, text):
        """Add tooltip to widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            
            # Ensure tooltip appears above other windows
            tooltip.lift()
            tooltip.wm_attributes('-topmost', True)
            
            # Create tooltip label
            label = tk.Label(
                tooltip,
                text=text,
                bg='#282828',
                fg='#FFFFFF',
                font=('Segoe UI', 9),
                padx=5,
                pady=2
            )
            label.pack()
            
            # Get widget's position relative to screen
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            
            # Center tooltip horizontally relative to widget
            tooltip_width = label.winfo_reqwidth()
            widget_width = widget.winfo_width()
            x_position = x + (widget_width - tooltip_width) // 2
            
            # Position tooltip below the widget with a small gap
            y_position = y + widget.winfo_height() + 2
            
            # Set tooltip position
            tooltip.wm_geometry(f"+{x_position}+{y_position}")
            
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def create_border(self):
        """Create rounded corners for the window"""
        border_color = '#282828'
        self.root.configure(bg=border_color)
        
        if hasattr(self.root, '_root'):  # Check if running on Windows
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                style = windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
                style = style | 0x00080000  # WS_EX_LAYERED
                DWMWCP_ROUND = 2  # Define DWMWCP_ROUND with the appropriate value
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    33,  # DWMWA_WINDOW_CORNER_PREFERENCE
                    byref(c_int(DWMWCP_ROUND)),
                    sizeof(c_int)
                )
            except:
                pass

    def position_window(self):
        """Position window with saved coordinates or default position"""
        try:
            # Try to load saved position
            with open('.window_position', 'r') as f:
                x, y = map(int, f.read().split(','))
        except:
            # Use default position if no saved position exists
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - self.width - 20
            y = screen_height - self.height - 40
        
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')

    def save_window_position(self):
        """Save current window position"""
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            with open('.window_position', 'w') as f:
                f.write(f'{x},{y}')
        except Exception as e:
            print(f"Error saving window position: {e}")

    def load_window_position(self):
        """Load and apply saved window position with multi-monitor support"""
        try:
            with open('.window_position', 'r') as f:
                pos = f.read().strip().split(',')
                if len(pos) == 2:
                    x, y = map(int, pos)
                    
                    # Validate position is within any monitor bounds
                    valid_position = False
                    for monitor in self.monitors:
                        if (monitor['left'] <= x <= monitor['right'] - self.width and
                            monitor['top'] <= y <= monitor['bottom'] - self.height):
                            valid_position = True
                            break
                    
                    if valid_position:
                        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
                        return
                        
            # If no valid saved position, center on primary monitor
            self.center_on_primary_monitor()
            
        except Exception as e:
            print(f"Error loading window position: {e}")
            self.center_on_primary_monitor()

    def center_on_primary_monitor(self):
        """Center the window on the primary monitor"""
        primary = self.monitors[0]  # Primary monitor is typically first
        x = primary['left'] + (primary['width'] - self.width) // 2
        y = primary['top'] + (primary['height'] - self.height) // 2
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')

    def start_move(self, event):
        """Start window drag"""
        self.x = event.x_root - self.root.winfo_x()
        self.y = event.y_root - self.root.winfo_y()

    def on_move(self, event):
        """Handle window drag with edge snapping for all monitors"""
        if hasattr(self, 'x'):
            # Calculate new position
            x = event.x_root - self.x
            y = event.y_root - self.y
            
            # Check each monitor for edge snapping
            snapped = False
            for monitor in self.monitors:
                # Check left edge
                if abs(x - monitor['left']) < self.snap_threshold:
                    x = monitor['left']
                    self.snap_positions['x'] = 'left'
                    snapped = True
                    break
                    
                # Check right edge
                elif abs((x + self.width) - monitor['right']) < self.snap_threshold:
                    x = monitor['right'] - self.width
                    self.snap_positions['x'] = 'right'
                    snapped = True
                    break
                    
            if not snapped:
                self.snap_positions['x'] = None
                
            # Check vertical snapping for current monitor
            current_monitor = self.get_current_monitor(x, y)
            if current_monitor:
                # Top edge
                if abs(y - current_monitor['top']) < self.snap_threshold:
                    y = current_monitor['top']
                    self.snap_positions['y'] = 'top'
                # Bottom edge
                elif abs((y + self.height) - current_monitor['bottom']) < self.snap_threshold:
                    y = current_monitor['bottom'] - self.height
                else:
                    self.snap_positions['y'] = None
                    
            # Update window position
            self.root.geometry(f"+{x}+{y}")

    def get_current_monitor(self, x, y):
        """Determine which monitor the window is currently on"""
        for monitor in self.monitors:
            if (monitor['left'] <= x <= monitor['right'] and 
                monitor['top'] <= y <= monitor['bottom']):
                return monitor
        return self.monitors[0]  # Default to primary monitor

    def stop_move(self, event):
        """Stop window drag and finalize snapping with multi-monitor support"""
        if hasattr(self, 'x'):
            # Get current position
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            
            # Get current monitor
            current_monitor = self.get_current_monitor(x, y)
            
            # Apply monitor-specific snapping
            if current_monitor:
                # Horizontal snapping
                if abs(x - current_monitor['left']) < self.snap_threshold:
                    x = current_monitor['left']
                elif abs((x + self.width) - current_monitor['right']) < self.snap_threshold:
                    x = current_monitor['right'] - self.width
                
                # Vertical snapping
                if abs(y - current_monitor['top']) < self.snap_threshold:
                    y = current_monitor['top']
                elif abs((y + self.height) - current_monitor['bottom']) < self.snap_threshold:
                    y = current_monitor['bottom'] - self.height
            
            # Apply final position
            self.root.geometry(f"+{x}+{y}")
            
            # Clean up
            del self.x
            del self.y

    def minimize_window(self, event=None):
        if not self.minimized:
            self.normal_geometry = self.root.geometry()
            screen_width = self.root.winfo_screenwidth()
            self.root.geometry(f'{self.width}x{self.height}-{screen_width+100}+0')
            self.minimized = True
            self.show_taskbar_icon()
        else:
            self.root.geometry(self.normal_geometry)
            self.minimized = False
            if hasattr(self, 'taskbar_icon'):
                self.taskbar_icon.destroy()

    def show_taskbar_icon(self):
        self.taskbar_icon = tk.Toplevel(self.root)
        self.taskbar_icon.title("Toastify")
        self.taskbar_icon.geometry('1x1+0+0')
        self.taskbar_icon.bind('<Button-1>', self.minimize_window)
        self.taskbar_icon.overrideredirect(False)
        self.taskbar_icon.attributes('-toolwindow', True)
        self.taskbar_icon.withdraw()
        self.taskbar_icon.iconify()

    def update_track_info(self):
        """Update track information with faster polling"""
        # Don't update if only settings UI is visible
        if not self.full_ui_initialized:
            return
            
        last_track_id = None
        while True:
            try:
                track_info = self.spotify_client.get_current_track()
                
                if track_info:
                    # Check if track has changed
                    current_track_id = track_info.get('track_id')
                    track_changed = current_track_id != last_track_id
                    
                    if track_changed:
                        # Full update for track change
                        self.full_title = track_info.get('title', 'Not playing')
                        self.scroll_offset = 0
                        self.scroll_paused = False
                        
                        if track_info.get('album_art_url'):
                            self.root.after(0, lambda url=track_info['album_art_url']: 
                                          self.update_album_art(url))
                        last_track_id = current_track_id
                    
                    # Always update playback state and progress
                    def update_ui():
                        try:
                            is_playing = track_info.get('is_playing', False)
                            # Update play button color based on state
                            self.playback_buttons[2].configure(
                                text='⏸' if is_playing else '⏯',
                                fg=self.text_color if is_playing else self.artist_color
                            )
                            
                            # Immediate playback state update
                            self.playback_buttons[2].configure(
                                text='⏸' if track_info.get('is_playing', False) else '⏯'
                            )
                            
                            # Update progress with interpolation
                            if track_info.get('is_playing', False):
                                progress = track_info.get('progress_ms', 0)
                                # Add elapsed time since last update
                                progress += int((time.time() - track_info.get('timestamp', time.time())) * 1000)
                                self.update_progress_bar(progress, track_info.get('duration_ms', 1))
                            
                            if track_changed:
                                # Update title and artist only on track change
                                title = self.full_title
                                if len(title) > 20:  # Changed from 35
                                    self.title_label.config(text=title[:32])  # Initial truncated view
                                else:
                                    self.title_label.config(text=title)
                                
                                if 'artist_list' in track_info and 'artist_uris' in track_info:
                                    self.update_artist_labels(track_info['artist_list'], 
                                                           track_info['artist_uris'])
                            
                            # Update shuffle and volume state
                            self.is_shuffled = track_info.get('is_shuffled', False)
                            self.playback_buttons[0].configure(
                                fg=self.text_color if self.is_shuffled else self.artist_color
                            )
                            
                            if 'volume' in track_info:
                                self.update_volume_bar(track_info['volume'])
                                
                        except Exception as e:
                            print(f"Error updating UI: {e}")
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.reset_display())
                
            except Exception as e:
                print(f"Error in update_track_info: {e}")
                
            time.sleep(0.1)  # Poll every 100ms instead of 1s

    def reset_display(self):
        """Reset display when no track is playing"""
        # Only update UI elements if full UI is initialized
        if not self.full_ui_initialized:
            return
            
        self.title_label.config(text="Not playing", fg=self.text_color)
        self.clear_artist_labels()
        self.update_progress_bar(0, 1)

    def toggle_pin(self, event=None):
        """Handle pin button state"""
        self.is_pinned = not self.is_pinned
        self.root.wm_attributes('-topmost', self.is_pinned)
        # Update pin button color
        self.pin_button.configure(
            fg=self.text_color if self.is_pinned else self.artist_color
        )

    def on_progress_hover(self, event):
        self.progress_bar.configure(cursor='hand2')

    def on_progress_leave(self, event):
        self.progress_bar.configure(cursor='')

    def format_time(self, ms):
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def get_click_position(self, event):
        bar_width = self.progress_bar.winfo_width()
        click_x = event.x
        # Ensure click_x is within bounds
        click_x = max(0, min(click_x, bar_width))
        return click_x / bar_width

    def on_progress_click(self, event):
        """Handle progress bar click with immediate visual feedback"""
        self.seeking = True
        position = self.get_click_position(event)
        # Update visuals immediately
        self.update_progress_visual(position)
        # Then seek
        if hasattr(self, 'current_duration') and self.current_duration:
            seek_position = int(position * self.current_duration)
            self.spotify_client.seek_to_position(seek_position)

    def on_progress_drag(self, event):
        if hasattr(self, 'seeking') and self.seeking:
            position = self.get_click_position(event)
            self.update_progress_visual(position)

    def on_progress_release(self, event):
        if hasattr(self, 'seeking') and self.seeking:
            position = self.get_click_position(event)
            if hasattr(self, 'current_duration') and self.current_duration:
                seek_position = int(position * self.current_duration)
                self.spotify_client.seek_to_position(seek_position)
            self.seeking = False

    def update_progress_visual(self, position):
        """Update progress bar with current theme color"""
        bar_width = self.progress_bar.winfo_width()
        progress_width = bar_width * position
        
        # Update progress bar position and color
        self.progress_bar.coords(
            'progress_indicator',
            0, 0, progress_width, self.progress_bar.winfo_height()
        )
        self.progress_bar.itemconfig('progress_indicator', fill=self.text_color)

    def update_progress_bar(self, progress_ms, duration_ms):
        """Update progress bar with current theme color"""
        if duration_ms > 0 and hasattr(self, 'progress_bar'):
            position = progress_ms / duration_ms
            bar_width = self.progress_bar.winfo_width()
            progress_width = bar_width * position
            
            # Force dimensions to stay constant
            self.progress_frame.configure(height=12)  # Account for padding
            self.progress_bar.configure(height=4)
            
            # Update progress bar with fixed dimensions
            self.progress_bar.coords(
                self.progress_indicator,
                0, 0, progress_width, 4
            )
            self.progress_bar.itemconfig(self.progress_indicator, fill=self.text_color)
            
            # Update time labels
            self.current_time.config(text=self.format_time(progress_ms))
            self.total_time.config(text=self.format_time(duration_ms))
            
            # Store current duration
            self.current_duration = duration_ms
        else:
            # Reset progress bar
            self.update_progress_visual(0)
            self.current_time.config(text="0:00")
            self.total_time.config(text="0:00")

    def toggle_shuffle(self):
        """Handle shuffle with immediate feedback"""
        self.is_shuffled = not self.is_shuffled
        # Update UI instantly
        self.playback_buttons[0].configure(
            fg=self.text_color if self.is_shuffled else self.artist_color
        )
        # Then toggle shuffle
        self.spotify_client.toggle_shuffle()

    def toggle_volume(self):
        """Handle volume with immediate feedback"""
        self.is_muted = not self.is_muted
        # Update UI instantly
        self.playback_buttons[4].configure(text='🔈' if self.is_muted else '🔊')
        # Then toggle volume
        self.spotify_client.toggle_volume()

    def start_title_scroll(self, event=None):
        """Start scrolling the title text when hovering"""
        if len(self.full_title) > 10:
            self.title_scroll_index = 0
            self.title_scroll_active = True
            self.scroll_title_text()  # Start scrolling immediately

    def stop_title_scroll(self, event=None):
        """Stop scrolling and reset title text"""
        self.title_scroll_active = False  # Remove hasattr check
        if len(self.full_title) > 35:
            truncated = self.full_title[:32] + '...'
            self.title_label.config(text=truncated)

    def scroll_title_text(self):
        """Scroll the title text with smooth animation"""
        if self.title_scroll_active:
            # Add padding between repetitions
            text = self.full_title + '          ' + self.full_title
            
            # Smoother scrolling with smaller steps
            pixels_per_step = 1
            display_text = text[self.title_scroll_index:self.title_scroll_index + 35]
            self.title_label.config(text=display_text)
            
            # Reset index when reaching the end of first title
            if self.title_scroll_index >= len(self.full_title):
                self.title_scroll_index = 0
            else:
                self.title_scroll_index += pixels_per_step
            
            # Higher refresh rate for smoother scrolling
            self.root.after(40, self.scroll_title_text)  # 25fps

    def update_artist_labels(self, artists, uris):
        """Update artist labels for current track"""
        # Clear existing labels FIRST
        self.clear_artist_labels()
        self.artist_labels = []  # Reset the list
        self.artist_uris = []    # Reset URIs list
        
        # Create new labels for each artist
        for i, (artist, uri) in enumerate(zip(artists, uris)):
            if i > 0:  # Add separator
                separator = tk.Label(self.artist_frame,
                                  text=",",
                                  bg=self.bg_color,
                                  fg=self.artist_color,
                                  font=('Segoe UI', 9))
                separator.pack(side='left', padx=(0, 0))
                self.artist_labels.append(separator)
            
            label = tk.Label(self.artist_frame,
                           text=artist,
                           bg=self.bg_color,
                           fg=self.artist_color,
                           font=('Segoe UI', 9),
                           cursor='hand2')
            label.pack(side='left', padx=(0, 0))
            
            # Store URI in the label for direct access
            label.uri = uri
            
            # Simplified event bindings with direct URI access
            label.bind('<Enter>', lambda e, lbl=label: lbl.configure(
                fg='#FFFFFF', 
                font=('Segoe UI', 9, 'underline')
            ))
            label.bind('<Leave>', lambda e, lbl=label: lbl.configure(
                fg=self.artist_color, 
                font=('Segoe UI', 9)
            ))
            label.bind('<Button-1>', lambda e, uri=uri: 
                      self.spotify_client.open_artist_profile(uri))
            
            self.artist_labels.append(label)
            self.artist_uris.append(uri)

    def clear_artist_labels(self):
        """Clear all existing artist labels"""
        for label in self.artist_labels:
            label.destroy()
        self.artist_labels.clear()  # Use clear() instead of reassignment
        self.artist_uris.clear()

    def on_volume_hover(self, event):
        self.volume_bar.configure(cursor='hand2')

    def on_volume_leave(self, event):
        self.volume_bar.configure(cursor='')

    def get_volume_position(self, event):
        bar_width = self.volume_bar.winfo_width()
        click_x = event.x
        click_x = max(0, min(click_x, bar_width))
        return click_x / bar_width

    def on_volume_click(self, event):
        """Handle volume click with immediate visual feedback"""
        position = self.get_volume_position(event)
        volume = int(position * 100)
        # Update visuals immediately
        self.update_volume_bar(volume)
        # Then set volume
        self.spotify_client.set_volume(volume)

    def on_volume_drag(self, event):
        """Handle volume drag with immediate visual feedback"""
        position = self.get_volume_position(event)
        volume = int(position * 100)
        # Update visuals immediately
        self.update_volume_bar(volume)
        # Then set volume
        self.spotify_client.set_volume(volume)

    def update_volume_bar(self, volume):
        """Update volume bar with current theme color"""
        if not hasattr(self, 'last_volume'):
            self.last_volume = volume
        
        bar_width = self.volume_bar.winfo_width()
        volume_width = bar_width * (volume / 100)
        
        # Update volume indicator with current theme color
        self.volume_bar.delete('volume_indicator')
        self.volume_bar.create_rectangle(
            0, 0, volume_width, 3,
            fill=self.text_color,  # Use current theme color
            width=0,
            tags='volume_indicator'
        )
        
        self.last_volume = volume

    def toggle_playback(self):
        """Handle play/pause with immediate feedback"""
        # Update UI instantly
        is_playing = self.playback_buttons[2].cget('text') == '⏸'
        self.playback_buttons[2].configure(
            text='⏯' if is_playing else '⏸'
        )
        # Then toggle playback
        self.spotify_client.toggle_playback() 

    def update_colors(self, base_color):
        """Update UI colors based on dominant color"""
        # Convert hex to RGB
        if isinstance(base_color, str):
            # Remove '#' and convert to RGB
            r = int(base_color[1:3], 16)
            g = int(base_color[3:5], 16)
            b = int(base_color[5:7], 16)
            base_color = (r, g, b)
        
        # Calculate brightness
        brightness = (base_color[0] * 299 + base_color[1] * 587 + base_color[2] * 114) / 1000
        
        # Create color scheme
        self.bg_color = f'#{base_color[0]:02x}{base_color[1]:02x}{base_color[2]:02x}'
        self.text_color = '#FFFFFF' if brightness < 128 else '#000000'
        self.artist_color = '#B3B3B3' if brightness < 128 else '#666666'
        
        # Update UI elements
        self.update_ui_colors()

    def update_ui_colors(self):
        """Apply color scheme to UI elements"""
        # Update all interactive elements with new accent color
        
        # Update progress bar color
        self.progress_bar.itemconfig(self.progress_indicator, fill=self.text_color)
        self.progress_bar.itemconfig('progress_indicator', fill=self.text_color)
        
        # Update volume bar color
        self.volume_bar.delete('volume_indicator')
        self.volume_bar.create_rectangle(
            0, 0, 
            self.volume_bar.winfo_width() * (self.last_volume if hasattr(self, 'last_volume') else 100) / 100, 
            3,
            fill=self.text_color,
            width=0,
            tags='volume_indicator'
        )
        
        # Update album art border
        self.album_art_label.configure(
            highlightcolor=self.text_color,
            highlightbackground=self.text_color
        )
        
        # Update active states for buttons
        if self.is_pinned:
            self.pin_button.configure(fg=self.text_color)
        
        if self.is_shuffled:
            self.playback_buttons[0].configure(fg=self.text_color)
        
        # Update play button if playing
        if self.playback_buttons[2].cget('text') == '⏸':
            self.playback_buttons[2].configure(fg=self.text_color)
        
        # Update hover states
        for btn in self.playback_buttons:
            btn.bind('<Enter>', lambda e, b=btn: b.configure(fg=self.text_color))
            
        self.pin_button.bind('<Enter>', lambda e: self.pin_button.configure(fg=self.text_color))
        self.color_button.bind('<Enter>', lambda e: self.color_button.configure(fg=self.text_color))
        
        # Update settings button if settings are open
        if hasattr(self, 'settings_open') and self.settings_open:
            self.settings_button.configure(fg=self.text_color)
            
        # Update color picker button if panel is open
        if hasattr(self, 'color_panel'):
            self.color_button.configure(fg=self.text_color)

    def update_album_art(self, url):
        """Update album artwork display"""
        try:
            # Download and resize image
            response = requests.get(url)
            img = Image.open(io.BytesIO(response.content))
            img = img.resize((20, 20), Image.Resampling.LANCZOS)  # Small square size
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update label
            self.album_art_label.configure(image=photo)
            self.album_art_label.image = photo  # Keep reference
        except Exception as e:
            print(f"Error updating album art: {e}")
            self.album_art_label.configure(image='')

    def show_loading_animation(self):
        """Show Spotify-style loading animation with triple dots"""
        # Create loading frame
        self.loading_frame = tk.Frame(self.root, bg=self.bg_color)
        self.loading_frame.pack(fill='both', expand=True)
        
        # Create frame for dots
        self.dots_frame = tk.Frame(self.loading_frame, bg=self.bg_color)
        self.dots_frame.pack(expand=True)
        
        # Create three dots
        self.dots = []
        for i in range(3):
            dot = tk.Label(
                self.dots_frame,
                text="•",
                font=('Segoe UI', 14),
                bg=self.bg_color,
                fg=self.text_color
            )
            dot.pack(side='left', padx=2)
            self.dots.append(dot)
            
        # Start animation
        self.animate_loading()

    def animate_loading(self):
        """Animate the dots with smoother fade effect"""
        if hasattr(self, 'dots'):
            def fade(step=0):
                if not hasattr(self, 'dots'):
                    return
                
                # Smoother sine-based fade for each dot
                import math
                for i, dot in enumerate(self.dots):
                    # Use sine wave for smoother transitions
                    phase = (step + i * 8) % 24  # Longer cycle
                    opacity = (math.sin(phase * math.pi / 12) + 1) / 2  # Smooth sine wave
                    
                    # Update dot color with opacity
                    r = int(int(self.text_color[1:3], 16) * opacity)
                    g = int(int(self.text_color[3:5], 16) * opacity)
                    b = int(int(self.text_color[5:7], 16) * opacity)
                    color = f'#{r:02x}{g:02x}{b:02x}'
                    
                    dot.configure(fg=color)
                
                # Faster refresh rate for smoother animation
                self.root.after(33, lambda: fade(step + 1))  # ~30fps
            
            fade()

    def create_main_ui(self):
        """Create main UI after loading"""
        # Hide the root window initially
        self.root.withdraw()
        
        # Create all UI elements
        self.create_ui()
        
        # Remove loading animation
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            delattr(self, 'loading_frame')
            delattr(self, 'dots')
        
        # Set background color
        self.root.configure(bg=self.bg_color)
        
        # Load last position if exists
        self.load_window_position()
        
        # Force update to ensure proper layout
        self.root.update_idletasks()
        
        # Show window with all elements properly sized
        def show_ui():
            self.root.deiconify()
            self.root.update_idletasks()
        
        # Slight delay to ensure smooth transition
        self.root.after(100, show_ui)

    def show_color_picker(self, event=None):
        """Show integrated color picker panel with smooth slide animation"""
        if hasattr(self, 'color_panel'):
            self.hide_color_picker()
            return
            
        # Store original height
        self.original_height = self.root.winfo_height()
        
        # Update color picker icon to current theme color
        self.color_button.configure(fg=self.text_color)
        
        # Create color panel frame - insert BEFORE the progress frame
        self.color_panel = tk.Frame(self.frame, bg=self.bg_color)
        self.color_panel.pack(after=self.playback_frame, before=self.progress_frame)
        
        # Create all the color picker contents
        self.create_color_picker_contents()
        
        # Get panel height
        self.root.update_idletasks()
        panel_height = self.color_panel.winfo_height()
        
        # Start with panel hidden below
        self.root.geometry(f'{self.width}x{self.original_height}')
        
        # Animate panel sliding up with easing
        def animate_slide(current_height, start_time):
            duration = 200  # Animation duration in milliseconds
            elapsed = time.time() * 1000 - start_time
            
            if elapsed < duration:
                # Easing function (ease-out)
                progress = elapsed / duration
                progress = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out
                
                new_height = self.original_height + (panel_height * progress)
                self.root.geometry(f'{self.width}x{int(new_height)}')
                
                # Force progress bar height to stay constant
                self.progress_bar.configure(height=4)
                self.progress_frame.configure(height=12)
                
                self.root.after(16, lambda: animate_slide(current_height, start_time))  # ~60fps
            else:
                # Ensure final height is exact
                final_height = self.original_height + panel_height
                self.root.geometry(f'{self.width}x{final_height}')
                
                # Force progress bar height one final time
                self.progress_bar.configure(height=4)
                self.progress_frame.configure(height=12)
        
        # Start animation
        animate_slide(0, time.time() * 1000)

    def hide_color_picker(self):
        """Hide color picker panel with smooth slide animation"""
        if hasattr(self, 'color_panel'):
            panel_height = self.color_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If settings panel is open, account for its height
            if hasattr(self, 'settings_panel') and self.settings_open:
                base_height += self.settings_panel.winfo_height()
            
            def animate_hide(start_time):
                duration = 200
                elapsed = time.time() * 1000 - start_time
                
                if elapsed < duration:
                    progress = elapsed / duration
                    progress = progress * progress  # Quadratic ease-in
                    
                    remaining_height = panel_height * (1 - progress)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    
                    # Keep progress bar dimensions
                    self.progress_bar.configure(height=4)
                    self.progress_frame.configure(height=12)
                    
                    self.root.after(16, lambda: animate_hide(start_time))
                else:
                    # Cleanup color panel specifically
                    self.color_panel.destroy()
                    delattr(self, 'color_panel')
                    self.color_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    
                    # Final progress bar adjustment
                    self.progress_bar.configure(height=4)
                    self.progress_frame.configure(height=12)

            animate_hide(time.time() * 1000)

    def hide_settings(self):
        """Hide settings panel with slide animation"""
        try:
            if not self.settings_open or not hasattr(self, 'settings_panel'):
                return
                
            panel_height = self.settings_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If color panel is open, account for its height
            if hasattr(self, 'color_panel'):
                base_height += self.color_panel.winfo_height()
            
            def animate_hide(progress):
                if progress <= 1.0:
                    ease = progress * progress
                    remaining_height = panel_height * (1 - ease)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    self.root.after(16, lambda: animate_hide(progress + 0.05))
                else:
                    # Clean up but maintain color panel height if open
                    if hasattr(self, 'settings_panel'):
                        self.settings_panel.destroy()
                    self.settings_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    self.settings_open = False
                    
            animate_hide(0.0)
            
        except Exception as e:
            print(f"Error hiding settings: {e}")
            traceback.print_exc()

    def create_color_picker_contents(self):
        """Create the contents of the color picker panel"""
        # Add separator line that extends full width
        separator = tk.Frame(self.color_panel, height=1, bg='#282828')
        separator.pack(fill='x', padx=0)
        
        # Create inner frame with left alignment
        inner_content = tk.Frame(self.color_panel, bg=self.bg_color)
        inner_content.pack(fill='x', padx=10, anchor='w')
        
        # Add title with left alignment
        title_label = tk.Label(inner_content, 
                             text="Theme", 
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.bg_color,
                             fg='#FFFFFF')
        title_label.pack(anchor='w', pady=(5, 5))
        
        # Create single row for all controls
        control_row = tk.Frame(inner_content, bg=self.bg_color)
        control_row.pack(fill='x', anchor='w', pady=(0, 5))
        
        # Left side: Color preview and hex input
        left_section = tk.Frame(control_row, bg=self.bg_color)
        left_section.pack(side='left')
        
        # Color preview
        self.color_preview = tk.Frame(left_section, 
                                        width=20, 
                                        height=20, 
                                        bg=self.text_color,
                                        highlightthickness=1,
                                        highlightbackground='#282828',
                                        cursor='hand2')
        self.color_preview.pack(side='left')
        self.color_preview.pack_propagate(False)
        self.color_preview.bind('<Button-1>', self.show_color_dialog)
        
        # Hex input
        self.hex_var = tk.StringVar(value=self.text_color)
        hex_entry = tk.Entry(left_section, 
                           textvariable=self.hex_var,
                           width=8,
                           bg='#282828',
                           fg='#FFFFFF',
                           insertbackground='#FFFFFF',
                           relief='flat',
                           font=('Segoe UI', 9, 'bold'),
                           justify='center')
        hex_entry.pack(side='left', padx=(5, 15))
        hex_entry.configure(highlightthickness=0)
        hex_entry.bind('<Return>', lambda e: self.apply_color())
        
        # Right side: Buttons
        button_style = {
            'font': ('Segoe UI', 9, 'bold'),
            'bg': '#282828',
            'fg': '#FFFFFF',
            'padx': 8,    # Reduced from 12
            'pady': 4,    # Reduced from 6
            'cursor': 'hand2',
            'width': 6    # Reduced from 8
        }
        
        # Create buttons
        for text, command in [
            ("Reset", self.reset_color),
            ("Apply", self.apply_color)
        ]:
            btn = tk.Label(
                control_row,
                text=text,
                **button_style
            )
            btn.pack(side='right', padx=2)
            btn.bind('<Button-1>', lambda e, cmd=command: cmd())
            
            # Hover effects
            btn.bind('<Enter>', 
                    lambda e, b=btn: b.configure(bg='#383838'))
            btn.bind('<Leave>', 
                    lambda e, b=btn: b.configure(bg='#282828'))

    def update_color_preview(self, *args):
        """Update color preview from RGB values"""
        try:
            r = self.rgb_vars[0].get()
            g = self.rgb_vars[1].get()
            b = self.rgb_vars[2].get()
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_preview.configure(bg=color)
            self.hex_var.set(color)
        except:
            pass

    def apply_color(self):
        """Apply selected color"""
        new_color = self.hex_var.get()
        self.text_color = new_color
        
        # Save color
        with open('.custom_color', 'w') as f:
            f.write(new_color)
        
        # Update all UI elements with new color
        self.update_ui_colors()
        
        # Update color button to match new color
        self.color_button.configure(fg=self.text_color)
        
        # Don't close the window, just update the preview
        self.color_preview.configure(bg=new_color)

    def reset_color(self):
        """Reset to Spotify green"""
        self.text_color = '#1DB954'
        
        # Update color preview and hex input if color picker is open
        if hasattr(self, 'color_preview'):
            self.color_preview.configure(bg=self.text_color)
            self.hex_var.set(self.text_color)
        
        self.update_ui_colors()
        
        # Save default color
        with open('.custom_color', 'w') as f:
            f.write(self.text_color)

    def show_color_dialog(self, event=None):
        """Show system color picker dialog"""
        # Get color picker box position
        x = self.root.winfo_x() + self.root.winfo_width() + 10
        y = self.root.winfo_y()
        
        # Use colorchooser directly instead of tk.call
        color = colorchooser.askcolor(
            color=self.text_color,
            title="Choose Color",
            parent=self.root
        )
        
        if (color[1]):  # If color was selected (not cancelled)
            # Update preview and hex
            self.color_preview.configure(bg=color[1])
            self.hex_var.set(color[1])
            
            # Apply the color immediately
            self.text_color = color[1]
            self.update_ui_colors()
            
            # Update color button to match new color
            self.color_button.configure(fg=color[1])
            
            # Save the color
            with open('.custom_color', 'w') as f:
                f.write(color[1])

    def bind_shortcuts(self):
        """Bind keyboard shortcuts for playback control"""
        # Play/Pause - Ctrl + Alt + Space
        self.root.bind('<Control-Alt-space>', lambda e: self.toggle_playback())
        
        # Previous Track - Ctrl + Alt + Left
        self.root.bind('<Control-Alt-Left>', lambda e: self.spotify_client.previous_track())
        
        # Next Track - Ctrl + Alt + Right
        self.root.bind('<Control-Alt-Right>', lambda e: self.spotify_client.next_track())
        
        # Volume Up - Ctrl + Alt + Up
        self.root.bind('<Control-Alt-Up>', lambda e: self.adjust_volume(10))
        
        """Adjust volume by delta percent"""
        def adjust_volume(delta):
            if hasattr(self, 'last_volume'):
                new_volume = max(0, min(100, self.last_volume + delta))
                # Update volume bar visually
                self.update_volume_bar(new_volume)
                # Update Spotify volume
                self.spotify_client.set_volume(new_volume)
                # Store new volume
                self.last_volume = new_volume

    def continuous_scroll(self):
        """Continuously scroll the title text"""
        if hasattr(self, 'full_title') and len(self.full_title) > 20:  # Changed from 35
            if not self.scroll_paused:
                # Create scrolling text with padding
                scroll_text = self.full_title + "     "  # Removed double text
                text_width = len(scroll_text)
                
                # Calculate display position
                start_pos = self.scroll_offset % text_width
                end_pos = start_pos + 32  # Show 32 characters at a time
                
                # Get display text with wrap-around
                if end_pos <= text_width:
                    display_text = scroll_text[start_pos:end_pos]
                else:
                    # Wrap around to the beginning
                    overflow = end_pos - text_width
                    display_text = scroll_text[start_pos:] + scroll_text[:overflow]
                
                # Update label
                self.title_label.config(text=display_text)
                
                # Increment scroll position
                self.scroll_offset += 1
                
                # Add pause at the beginning of each cycle
                if self.scroll_offset % text_width == 0:
                    self.scroll_paused = True
                    self.root.after(2000, self.resume_scroll)  # 2 second pause
                    
        # Continue scrolling
        self.root.after(125, self.continuous_scroll)  # Faster scroll speed (50ms)

    def resume_scroll(self):
        """Resume scrolling after pause"""
        self.scroll_paused = False

    def show_settings(self, event=None):
        """Show or hide settings panel with slide animation"""
        try:
            print("Attempting to toggle settings...")  # Debug print
            if not self.root.winfo_exists():
                print("Window doesn't exist")  # Debug print
                return
                
            if hasattr(self, 'settings_open') and self.settings_open:
                print("Closing settings panel")  # Debug print
                self.hide_settings()
                return
        
            # Force window to be visible first
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.update()
            
            # Create panel after ensuring window is visible
            self.settings_panel = tk.Frame(self.frame, bg=self.bg_color)
            self.settings_panel.pack(after=self.playback_frame, before=self.progress_frame)
            
            print("Creating settings contents...")  # Debug print
            self.create_settings_contents()
            
            # Force geometry update
            self.root.update_idletasks()
            
            # Get accurate panel height after contents are created
            panel_height = self.settings_panel.winfo_reqheight()
            
            # Mark settings as open and store original height
            self.settings_open = True
            self.original_height = self.root.winfo_height()
            
            # Update settings icon
            self.settings_button.configure(fg=self.text_color)
            
            def animate_slide(progress):
                if progress <= 1.0:
                    # Ease out animation
                    ease = 1 - (1 - progress) * (1 - progress)
                    new_height = self.original_height + (panel_height * ease)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    # Ensure contents are visible by updating canvas scrollregion
                    self.root.update_idletasks()
                    self.root.after(16, lambda: animate_slide(progress + 0.05))
                else:
                    # Finalize animation with exact height
                    self.root.geometry(f'{self.width}x{int(self.original_height + panel_height)}')
                    
            animate_slide(0.0)
                
        except Exception as e:
            print(f"Error showing settings: {e}")
            traceback.print_exc()

    def hide_settings(self):
        """Hide settings panel with slide animation"""
        try:
            if not self.settings_open or not hasattr(self, 'settings_panel'):
                return
                
            panel_height = self.settings_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If color panel is open, account for its height
            if hasattr(self, 'color_panel'):
                base_height += self.color_panel.winfo_height()
            
            def animate_hide(progress):
                if progress <= 1.0:
                    ease = progress * progress
                    remaining_height = panel_height * (1 - ease)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    self.root.after(16, lambda: animate_hide(progress + 0.05))
                else:
                    # Clean up but maintain color panel height if open
                    if hasattr(self, 'settings_panel'):
                        self.settings_panel.destroy()
                    self.settings_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    self.settings_open = False
                    
            animate_hide(0.0)
            
        except Exception as e:
            print(f"Error hiding settings: {e}")
            traceback.print_exc()

    def create_settings_contents(self):
        """Create the contents of the settings panel"""
        # Move settings panel before progress bar
        if hasattr(self, 'progress_frame'):
            self.settings_panel.pack(before=self.progress_frame)  # Fixed this line
        
        # Add separator line that extends full width
        separator = tk.Frame(self.settings_panel, height=1, bg='#282828')
        separator.pack(fill='x', padx=0)
        
        # Create inner frame
        inner_content = tk.Frame(self.settings_panel, bg=self.bg_color)
        inner_content.pack(fill='x', padx=10)
        
        # Add title
        title_label = tk.Label(inner_content, 
                             text="Settings", 
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.bg_color,
                             fg='#FFFFFF')
        title_label.pack(anchor='w', pady=(5, 5))
        
        # Add a message if credentials are missing
        if not self.spotify_client.has_valid_credentials():
            msg_label = tk.Label(inner_content,
                               text="Please enter your Spotify API credentials to continue",
                               bg=self.bg_color,
                               fg='#FFFFFF',
                               font=('Segoe UI', 9))
            msg_label.pack(anchor='w', pady=(0, 10))
        
        # Create input fields
        input_style = {
            'bg': '#282828',
            'fg': '#FFFFFF',
            'insertbackground': '#FFFFFF',
            'relief': 'flat',
            'font': ('Segoe UI', 9),
            'width': 35
        }
        
        # Client ID input with placeholder
        tk.Label(inner_content, text="Client ID:", 
                bg=self.bg_color, fg='#FFFFFF',
                font=('Segoe UI', 9)).pack(anchor='w')
        self.client_id_var = tk.StringVar(value=self.spotify_client.auth_manager.client_id or "Enter your Spotify Client ID")
        self.client_id_entry = tk.Entry(inner_content, 
                                      textvariable=self.client_id_var,
                                      **input_style)
        if not self.spotify_client.auth_manager.client_id:
            self.client_id_entry.configure(fg='#666666')
            self.client_id_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(e, "Enter your Spotify Client ID"))
            self.client_id_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(e, "Enter your Spotify Client ID"))
        self.client_id_entry.pack(fill='x', pady=(0, 5))

        # Client Secret input with eye toggle
        tk.Label(inner_content, text="Client Secret:", 
                bg=self.bg_color, fg='#FFFFFF',
                font=('Segoe UI', 9)).pack(anchor='w')
                
        secret_frame = tk.Frame(inner_content, bg=self.bg_color)
        secret_frame.pack(fill='x', pady=(0, 10))
        
        self.client_secret_var = tk.StringVar(value=self.spotify_client.auth_manager.client_secret or "Enter your Spotify Client Secret")
        self.client_secret_entry = tk.Entry(secret_frame, 
                                          textvariable=self.client_secret_var,
                                          show='•',
                                          **input_style)
        self.client_secret_entry.pack(side='left', fill='x', expand=True)
        
        if not self.spotify_client.auth_manager.client_secret:
            self.client_secret_entry.configure(fg='#666666', show='')
            self.client_secret_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(e, "Enter your Spotify Client Secret"))
            self.client_secret_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(e, "Enter your Spotify Client Secret"))

        # Add eye toggle button
        self.eye_button = tk.Label(secret_frame, 
                                 text="👁", 
                                 bg=self.bg_color,
                                 fg=self.artist_color,
                                 cursor='hand2',
                                 padx=5)
        self.eye_button.pack(side='right')
        self.eye_button.bind('<Button-1>', self.toggle_secret_visibility)
        
        # Button row with consistent sizing
        button_row = tk.Frame(inner_content, bg=self.bg_color)
        button_row.pack(fill='x', pady=(0, 5))
        
        # Save button
        save_btn = tk.Label(
            button_row,
            text="Save",
            font=('Segoe UI', 9, 'bold'),
            bg='#282828',
            fg='#FFFFFF',
            padx=12,
            pady=6,
            cursor='hand2'
        )
        save_btn.pack(side='right', padx=5)
        save_btn.bind('<Button-1>', lambda e: self.save_settings())
        save_btn.bind('<Enter>', lambda e: save_btn.configure(bg='#383838'))
        save_btn.bind('<Leave>', lambda e: save_btn.configure(bg='#282828'))

    def save_settings(self):
        """Save client credentials and validate"""
        client_id = self.client_id_var.get().strip()
        client_secret = self.client_secret_var.get().strip()
        
        # Don't validate if they're placeholder texts
        if client_id == "Enter your Spotify Client ID" or client_secret == "Enter your Spotify Client Secret":
            self.show_message("Please enter valid credentials!", error=True)
            return
        
        # Validate credentials format
        if not self.validate_credentials(client_id, client_secret):
            self.show_message("Invalid credentials format!", error=True)
            return
            
        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:8888/callback'
        }
        
        try:
            # Test the credentials before saving
            test_client = SpotifyClient()
            test_client.auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri='http://localhost:8888/callback',
                scope='user-read-currently-playing user-modify-playback-state user-read-playback-state'
            )
            
            # Try to get a token
            token = test_client.auth_manager.get_access_token(as_dict=False)
            if not token:
                self.show_message("Invalid credentials! Unable to authenticate.", error=True)
                return
                
            # If we get here, credentials are valid - save them
            with open('spotify_config.json', 'w') as f:
                json.dump(config, f)
            
            self.show_message("Settings saved!\nRestarting app...", error=False)
            self.root.after(1500, self.restart_app)
            
        except Exception as e:
            print(f"Error validating credentials: {e}")
            self.show_message("Invalid credentials! Please check and try again.", error=True)

    def restart_app(self):
        """Restart the application"""
        self.root.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def validate_credentials(self, client_id, client_secret):
        """Validate credential format"""
        # Check if credentials are not empty
        if not client_id or not client_secret:
            return
            
        # Check if client_id is 32 characters long and alphanumeric
        if len(client_id) != 32 or not client_id.isalnum():
            return
            
        # Check if client_secret is 32 characters long and alphanumeric
        if len(client_secret) != 32 or not client_secret.isalnum():
            return
            
        return True

    def show_message(self, message, error=False):
        """Show a temporary message in the settings panel"""
        # Remove any existing message
        for widget in self.settings_panel.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget('text').startswith(('Settings saved', 'Error', 'Invalid')):
                widget.destroy()
        
        msg_label = tk.Label(self.settings_panel,
                           text=message,
                           bg=self.bg_color,
                           fg=self.text_color if not error else '#FF0000',
                           font=('Segoe UI', 9))
        msg_label.pack(pady=5)
        self.root.after(3000, msg_label.destroy)

    def load_saved_color(self):
        """Load saved color theme"""
        try:
            with open('.custom_color', 'r') as f:
                self.text_color = f.read().strip()
        except:
            self.text_color = '#1DB954'  # Default Spotify green

    def on_entry_focus_in(self, event, placeholder):
        """Handle entry field focus in"""
        if event.widget.get() == placeholder:
            event.widget.delete(0, 'end')
            event.widget.configure(fg='#FFFFFF')
            if event.widget == self.client_secret_entry:
                event.widget.configure(show='•')

    def on_entry_focus_out(self, event, placeholder):
        """Handle entry field focus out"""
        if event.widget.get() == '':
            event.widget.insert(0, placeholder)
            event.widget.configure(fg='#666666')
            if event.widget == self.client_secret_entry:
                event.widget.configure(show='')

    def toggle_secret_visibility(self, event):
        """Toggle client secret visibility"""
        if self.client_secret_entry.cget('show') == '•':
            self.client_secret_entry.configure(show='')
            self.eye_button.configure(fg=self.text_color)
        else:
            self.client_secret_entry.configure(show='•')
            self.eye_button.configure(fg=self.artist_color)
            self.eye_button.configure(fg=self.artist_color)

    def get_monitor_info(self):
        """Get information about all connected monitors"""
        monitors = []
        
        if os.name == 'nt':  # Windows
            try:
                callback = get_monitor_callback(monitors)
                # Use c_bool instead of BOOL for the callback
                callback_type = WINFUNCTYPE(c_bool, HMONITOR, HDC, POINTER(RECT), LPARAM)
                callback_function = callback_type(callback)
                windll.user32.EnumDisplayMonitors(None, None, callback_function, 0)
            except Exception as e:
                print(f"Error enumerating monitors: {e}")
                self._fallback_monitor(monitors)
        else:
            self._fallback_monitor(monitors)
        
        # Ensure we have at least one monitor
        if not monitors:
            self._fallback_monitor(monitors)
            
        return monitors

    def _fallback_monitor(self, monitors):
        """Add fallback monitor info using root window dimensions"""
        monitors.append({
            'left': 0,
            'top': 0,
            'right': self.root.winfo_screenwidth(),
            'bottom': self.root.winfo_screenheight(),
            'width': self.root.winfo_screenwidth(),
            'height': self.root.winfo_screenheight()
        })

    def show_hotkeys(self, event=None):
        """Show hotkey configuration panel with slide animation"""
        if hasattr(self, 'hotkey_panel'):
            self.hide_hotkeys()
            return
            
        # Store original height
        self.original_height = self.root.winfo_height()
        
        # Update hotkey icon to current theme color
        self.hotkey_button.configure(fg=self.text_color)
        
        # Create hotkey panel frame with a single border and padding
        self.hotkey_panel = tk.Frame(self.frame, bg=self.bg_color, bd=2, relief='groove', padx=5, pady=5)
        self.hotkey_panel.pack(after=self.playback_frame, before=self.progress_frame, fill='x')  # Ensure it fills horizontally
        
        # Create a canvas for scrolling
        self.hotkey_canvas = tk.Canvas(self.hotkey_panel, bg=self.bg_color, highlightthickness=0)  # Remove highlight border
        self.hotkey_canvas.pack(side='left', fill='both', expand=True)
        
        # Create a scrollbar
        scrollbar = tk.Scrollbar(self.hotkey_panel, orient='vertical', command=self.hotkey_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        
        # Create a frame inside the canvas
        self.hotkey_content_frame = tk.Frame(self.hotkey_canvas, bg=self.bg_color)
        self.hotkey_canvas.create_window((0, 0), window=self.hotkey_content_frame, anchor='nw')
        
        # Create all the hotkey contents
        self.create_hotkey_contents()
        
        # Configure scrollbar
        self.hotkey_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Update the scroll region
        self.hotkey_content_frame.bind("<Configure>", lambda e: self.hotkey_canvas.configure(scrollregion=self.hotkey_canvas.bbox("all")))
        
        # Force an update to ensure dimensions are calculated
        self.root.update_idletasks()
        
        # Set a fixed height for the hotkey panel (doubled)
        self.hotkey_panel.configure(height=88)  # Increased height to double
        
        # Check dimensions
        panel_height = self.hotkey_panel.winfo_height()
        content_height = self.hotkey_content_frame.winfo_height()
        print(f"Hotkey panel height: {panel_height}, Content height: {content_height}")  # Debugging output
        
        # Animate panel sliding up
        def animate_slide(start_time):
            duration = 200
            elapsed = time.time() * 1000 - start_time
            
            if elapsed < duration:
                progress = elapsed / duration
                progress = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out
                
                new_height = self.original_height + (panel_height * progress)
                self.root.geometry(f'{self.width}x{int(new_height)}')
                
                self.root.after(16, lambda: animate_slide(start_time))
            else:
                self.root.geometry(f'{self.width}x{int(self.original_height + panel_height)}')
        
        animate_slide(time.time() * 1000)

    def hide_hotkeys(self):
        """Hide hotkey panel with smooth slide animation"""
        if hasattr(self, 'hotkey_panel'):
            panel_height = self.hotkey_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height
            
            def animate_hide(start_time):
                duration = 200
                elapsed = time.time() * 1000 - start_time
                
                if elapsed < duration:
                    progress = elapsed / duration
                    progress = progress * progress  # Quadratic ease-in
                    
                    remaining_height = panel_height * (1 - progress)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    
                    self.root.after(16, lambda: animate_hide(start_time))
                else:
                    self.hotkey_panel.destroy()
                    delattr(self, 'hotkey_panel')
                    self.hotkey_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
        
        animate_hide(time.time() * 1000)

    def create_hotkey_contents(self):
        """Create Discord-style hotkey configuration panel"""
        # Define hotkey configurations
        self.hotkeys = [
            ("Play/Pause", "Ctrl + Alt + Space"),
            ("Previous Track", "Ctrl + Alt + ←"),
            ("Next Track", "Ctrl + Alt + →"),
            ("Volume Up", "Ctrl + Alt + ↑"),
            ("Volume Down", "Ctrl + Alt + ↓")
        ]
        
        # Create hotkey entries
        for action, keys in self.hotkeys:
            hotkey_row = tk.Frame(self.hotkey_content_frame, bg=self.bg_color, bd=1, relief='flat', padx=5, pady=5)  
            hotkey_row.pack(fill='x', pady=2)
            
            # Action label
            action_label = tk.Label(hotkey_row,
                              text=action,
                              font=('Segoe UI', 9),
                              bg=self.bg_color,
                              fg='#FFFFFF',
                              width=20,  
                              anchor='w')
            action_label.pack(side='left', padx=(0, 10))
            
            # Hotkey display label
            key_label = tk.Label(hotkey_row,
                               text=keys,
                               font=('Segoe UI', 9),
                               bg=self.bg_color,
                               fg='#B3B3B3',
                               padx=8)
            key_label.pack(side='left', fill='y', expand=True)  # Allow it to fill the height

            # Edit button/icon
            edit_button = tk.Button(hotkey_row, text='✎', command=lambda label=key_label: self.assign_hotkey(label), bg=self.bg_color, fg='#FFFFFF', borderwidth=0, font=('Symbola', 10))
            edit_button.pack(side='left', padx=(10, 0))

            # Bind click event to assign new hotkey
            hotkey_row.bind('<Button-1>', lambda e, label=key_label: self.assign_hotkey(label))

        print("Hotkey contents created successfully.")  # Debugging output

    def assign_hotkey(self, label):
        """Assign a new hotkey when the user presses a key"""
        self.current_keys = []  # List to store pressed keys

        def on_key_press(event):
            key = event.keysym  # Get the key symbol
            if key not in self.current_keys and len(self.current_keys) < 3:
                self.current_keys.append(key)  # Add key to the list
            label.config(text=' + '.join(self.current_keys))  # Update the label with the new key combination
            
            # Save combination after three keys
            if len(self.current_keys) == 3:
                # Update the hotkeys list
                for i, (action, _) in enumerate(self.hotkeys):
                    if label.cget("text") == _:
                        self.hotkeys[i] = (action, ' + '.join(self.current_keys))  # Update the hotkey
                        print(f"Updated {action} to {' + '.join(self.current_keys)}")  # Debugging output
                        break
                self.root.unbind('<KeyPress>')  # Unbind the key press event

        def on_key_release(event):
            # Clear the current keys when the user releases a key
            self.current_keys.clear()
            self.root.unbind('<KeyRelease>')  # Unbind the key release event

        self.root.bind('<KeyPress>', on_key_press)  # Bind key press event
        self.root.bind('<KeyRelease>', on_key_release)  # Bind key release event
        print("Press up to three keys to assign them as a hotkey.")  # Debugging output

    def load_hotkeys(self):
        """Load hotkeys from file"""
        try:
            with open('.hotkeys.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                ("Play/Pause", "Ctrl + Alt + Space"),
                ("Previous Track", "Ctrl + Alt + Left"),
                ("Next Track", "Ctrl + Alt + Right"),
            ]
        except Exception as e:
            print(f"Error loading hotkeys: {e}")
            return [
                ("Play/Pause", "Ctrl + Alt + Space"),
                ("Previous Track", "Ctrl + Alt + Left"),
                ("Next Track", "Ctrl + Alt + Right"),
            ]

    def save_hotkeys(self):
        """Save hotkeys to file"""
        try:
            with open('.hotkeys.json', 'w') as f:
                json.dump(self.hotkeys, f)
        except Exception as e:
            print(f"Error saving hotkeys: {e}")

    def create_ui(self):
        """Create all UI elements"""
        # Create main container
        self.container = tk.Frame(self.root, bg=self.bg_color)
        self.container.pack(fill='both', expand=True)
        
        # Add keyboard shortcuts
        self.bind_shortcuts()
        
        # Force initial size
        self.container.update_idletasks()
        
        # Create content frame
        self.frame = tk.Frame(self.container, bg=self.bg_color)
        self.frame.pack(fill='both', expand=True, padx=10, pady=8)
        
        # Create top row frame for title and controls
        self.top_row = tk.Frame(self.frame, bg=self.bg_color)
        self.top_row.pack(fill='x', expand=True)
        
        # Create album art label (after creating top_row)
        self.album_art_label = tk.Label(
            self.top_row,
            bg=self.bg_color,
            width=20,
            height=20,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=self.text_color,
            highlightbackground=self.text_color
        )
        self.album_art_label.pack(side='left', padx=(0, 8))
        
        # Create controls frame first (right side)
        self.controls = tk.Frame(self.top_row, bg=self.bg_color)
        self.controls.pack(side='right', padx=(0, 2))
        
        # Add vertical separator
        self.separator = tk.Frame(self.top_row, 
                                bg='#282828',  # Match color picker theme
                                width=1,
                                height=14)
        self.separator.pack(side='right', fill='y', padx=8, pady=6)
        
        # Create title label (after album art)
        self.title_label = tk.Label(self.top_row, 
                                  text="Not playing", 
                                  bg=self.bg_color,
                                  fg=self.title_color,
                                  font=('Segoe UI', 11, 'bold'),
                                  anchor='w')
        self.title_label.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Remove hover bindings since we want continuous scrolling
        # self.title_label.bind('<Enter>', self.start_title_scroll)
        # self.title_label.bind('<Leave>', self.stop_title_scroll)
        
        # Start continuous scrolling
        self.scroll_offset = 0
        self.scroll_paused = False
        self.continuous_scroll()
        
        # Create window control buttons
        button_style = {
            'bg': self.bg_color,
            'font': ('Segoe UI', 12),
            'width': 2,
            'pady': 3
        }
        
        # Add hotkey button before settings button
        self.hotkey_button = tk.Label(self.controls, 
                                   text="⌘",  # Command symbol
                                   fg=self.artist_color,
                                   bg=self.bg_color,
                                   font=('Segoe UI', 12),  # Adjusted font size
                                   width=2,
                                   pady=3)
        self.hotkey_button.pack(side='left', padx=(0, 1))
        self.hotkey_button.bind('<Button-1>', self.show_hotkeys)

        # Add hover effects like other buttons
        self.hotkey_button.bind('<Enter>', lambda e: self.hotkey_button.configure(fg=self.text_color))
        self.hotkey_button.bind('<Leave>', lambda e: self.hotkey_button.configure(
            fg=self.text_color if hasattr(self, 'hotkey_panel') else self.artist_color
        ))

        # Add tooltip
        self.add_tooltip(self.hotkey_button, "Hotkeys")

        # Add settings button with safer event binding
        self.settings_button = tk.Label(self.controls, 
                                      text="⚙",
                                      fg=self.artist_color,
                                      bg=self.bg_color,
                                      font=('Segoe UI', 12),
                                      width=2,
                                      pady=3)
        self.settings_button.pack(side='left', padx=(0, 1))
        self.settings_button.bind('<Button-1>', self.show_settings)
        
        # Add color picker button (before pin button, after separator)
        self.color_button = tk.Label(self.controls, 
                                   text="🎨",
                                   fg=self.artist_color,  # Start with gray
                                   bg=self.bg_color,
                                   font=('Segoe UI', 12),
                                   width=2,
                                   pady=3)
        self.color_button.pack(side='left', padx=(0, 1))
        self.color_button.bind('<Button-1>', self.show_color_picker)
        
        # Remove hover bindings - we'll handle color state directly
        # self.color_button.bind('<Enter>', lambda e: self.color_button.configure(fg=self.text_color))
        # self.color_button.bind('<Leave>', lambda e: self.color_button.configure(fg=self.artist_color))
        
        # Add pin button (after color button)
        self.pin_button = tk.Label(self.controls, 
                                text="⚲",
                                fg=self.text_color,
                                **button_style)
        self.pin_button.pack(side='left', padx=(0, 1))
        self.pin_button.bind('<Button-1>', self.toggle_pin)
        self.pin_button.bind('<Enter>', lambda e: self.pin_button.configure(fg=self.text_color))
        self.pin_button.bind('<Leave>', lambda e, b=self.pin_button: b.configure(
            fg=self.text_color if b.cget('text') == '⚲' else self.artist_color
        ))
        
        # Add minimize button
        self.minimize_button = tk.Label(self.controls, 
                                      text="−",
                                      fg=self.artist_color,
                                      **button_style)
        self.minimize_button.pack(side='left', padx=(0, 1))
        self.minimize_button.bind('<Button-1>', self.minimize_window)
        
        # Add close button
        self.close_button = tk.Label(self.controls, 
                                   text="×",
                                   fg=self.artist_color,
                                   **button_style)
        self.close_button.pack(side='left')
        self.close_button.bind('<Button-1>', lambda e: self.root.quit())
        
        # Add tooltips to buttons
        self.add_tooltip(self.settings_button, "Settings")
        self.add_tooltip(self.color_button, "Theme")
        self.add_tooltip(self.pin_button, "Pin Window")
        self.add_tooltip(self.minimize_button, "Minimize")
        self.add_tooltip(self.close_button, "Close")
        
        
        # Create artist frame
        self.artist_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.artist_frame.pack(fill='x', expand=True, pady=(2, 4))
        
        # Create playback frame
        self.playback_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.playback_frame.pack(fill='x', expand=True, pady=(2, 4))
        
        # Create progress frame and bar with fixed dimensions
        self.progress_frame = tk.Frame(self.frame, bg=self.bg_color, height=4)
        self.progress_frame.pack(fill='x', expand=True)
        self.progress_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.progress_bar = tk.Canvas(
            self.progress_frame,
            height=4,
            bg='#404040',
            highlightthickness=0,
            cursor='hand2'
        )
        self.progress_bar.pack(fill='x', pady=4)
        self.progress_bar.configure(height=4)  # Force height
        
        # Create progress indicator with fixed dimensions
        self.progress_indicator = self.progress_bar.create_rectangle(
            0, 0, 0, 4,
            fill=self.text_color,
            width=0,
            tags='progress_indicator'
        )
        
        # Force frame to maintain height
        self.progress_frame.configure(height=12)  # Account for padding
        self.progress_frame.pack_propagate(False)
        
        # Create time frame
        self.time_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.time_frame.pack(fill='x', expand=True)
        
        # Create time labels
        self.current_time = tk.Label(self.time_frame,
                                   text="0:00",
                                   bg=self.bg_color,
                                   fg=self.artist_color,
                                   font=('Segoe UI', 9))
        self.current_time.pack(side='left')
        
        self.total_time = tk.Label(self.time_frame,
                                 text="0:00",
                                 bg=self.bg_color,
                                 fg=self.artist_color,
                                 font=('Segoe UI', 9))
        self.total_time.pack(side='right')
        
        # Create playback buttons
        button_configs = [
            {'text': '🔀', 'command': self.toggle_shuffle, 'size': 11, 'tooltip': 'Toggle Shuffle'},
            {'text': '⏮', 'command': self.spotify_client.previous_track, 'size': 11, 'tooltip': 'Previous Track'},
            {'text': '⏯', 'command': self.toggle_playback, 'size': 11, 'tooltip': 'Play/Pause'},
            {'text': '⏭', 'command': self.spotify_client.next_track, 'size': 11, 'tooltip': 'Next Track'},
            {'text': '🔊', 'command': self.toggle_volume, 'size': 11, 'tooltip': 'Mute/Unmute'}
        ]
        
        # Center playback controls
        spacer_left = tk.Frame(self.playback_frame, bg=self.bg_color)
        spacer_left.pack(side='left', expand=True)
        
        # Create playback buttons
        self.playback_buttons = []
        for i, config in enumerate(button_configs):
            btn = tk.Label(
                self.playback_frame,
                text=config['text'],
                bg=self.bg_color,
                fg=self.artist_color,
                font=('Segoe UI', config['size']),
                padx=8
            )
            btn.pack(side='left')
            
            # Add volume bar after volume button
            if i == 4:  # After the volume button
                # Add volume control frame
                self.volume_frame = tk.Frame(self.playback_frame, bg=self.bg_color)
                self.volume_frame.pack(side='left', padx=(2, 8))
                
                self.volume_bar = tk.Canvas(
                    self.volume_frame,
                    height=4,
                    bg='#404040',
                    highlightthickness=0,
                    cursor='hand2',
                    width=60  # Smaller width to fit beside button
                )
                self.volume_bar.pack(side='left', pady=8)  # Align vertically with buttons
                
                # Add volume indicator
                self.volume_bar.create_rectangle(
                    0, 0, 60, 4,
                    fill=self.text_color,
                    width=0,
                    tags='volume_indicator'
                )
                
                # Bind volume bar events
                self.volume_bar.bind('<Button-1>', self.on_volume_click)
                self.volume_bar.bind('<B1-Motion>', self.on_volume_drag)
                self.volume_bar.bind('<Enter>', self.on_volume_hover)
                self.volume_bar.bind('<Leave>', self.on_volume_leave)
            
            # Create tooltip with fixed size and style
            tooltip_text = config['tooltip']
            def create_tooltip(widget=btn, text=tooltip_text):
                tooltip = tk.Toplevel(self.root)  # Make root the parent
                tooltip.wm_overrideredirect(True)
                tooltip.wm_attributes('-topmost', True)
                
                label = tk.Label(
                    tooltip,
                    text=text,
                    bg='#282828',
                    fg='#FFFFFF',
                    font=('Segoe UI', 9),
                    padx=5,
                    pady=2
                )
                label.pack()
                
                # Position tooltip below button
                x = widget.winfo_rootx()
                y = widget.winfo_rooty() + widget.winfo_height() + 2
                
                # Center horizontally
                tooltip.update_idletasks()  # Ensure tooltip size is calculated
                x = x + (widget.winfo_width() // 2) - (tooltip.winfo_width() // 2)
                
                tooltip.geometry(f"+{x}+{y}")
                return tooltip
            
            btn.bind('<Enter>', lambda e, b=btn: setattr(b, 'tooltip', create_tooltip(b)))
            btn.bind('<Leave>', lambda e, b=btn: b.tooltip.destroy() if hasattr(b, 'tooltip') else None)
            
            # Update hover colors
            btn.bind('<Enter>', lambda e, b=btn: b.configure(fg=self.text_color))
            btn.bind('<Leave>', lambda e, b=btn, i=i: b.configure(
                fg=self.text_color if (i == 0 and self.is_shuffled) else self.artist_color
            ))
            
            btn.bind('<Button-1>', lambda e, cmd=config['command']: cmd())
            self.playback_buttons.append(btn)
        
        # Remove the old volume bar from time frame
        if hasattr(self, 'volume_frame') and self.volume_frame in self.time_frame.winfo_children():
            self.volume_frame.destroy()
        
        # Create update thread
        self.update_thread = threading.Thread(target=self.update_track_info, daemon=True)
        self.update_thread.start()
        
        # Bind drag events to frame and all its children
        self.frame.bind('<Button-1>', self.start_move)
        self.frame.bind('<B1-Motion>', self.on_move)
        self.frame.bind('<ButtonRelease-1>', self.stop_move)
        
        # Also bind to top_row and title_label specifically
        self.top_row.bind('<Button-1>', self.start_move)
        self.top_row.bind('<B1-Motion>', self.on_move)
        self.top_row.bind('<ButtonRelease-1>', self.stop_move)
        
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        self.title_label.bind('<ButtonRelease-1>', self.stop_move)
        
        # Add progress bar bindings
        self.progress_bar.bind('<Button-1>', self.on_progress_click)
        self.progress_bar.bind('<B1-Motion>', self.on_progress_drag)
        self.progress_bar.bind('<ButtonRelease-1>', self.on_progress_release)
        self.progress_bar.bind('<Enter>', self.on_progress_hover)
        self.progress_bar.bind('<Leave>', self.on_progress_leave)

    def add_tooltip(self, widget, text):
        """Add tooltip to widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            
            # Ensure tooltip appears above other windows
            tooltip.lift()
            tooltip.wm_attributes('-topmost', True)
            
            # Create tooltip label
            label = tk.Label(
                tooltip,
                text=text,
                bg='#282828',
                fg='#FFFFFF',
                font=('Segoe UI', 9),
                padx=5,
                pady=2
            )
            label.pack()
            
            # Get widget's position relative to screen
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            
            # Center tooltip horizontally relative to widget
            tooltip_width = label.winfo_reqwidth()
            widget_width = widget.winfo_width()
            x_position = x + (widget_width - tooltip_width) // 2
            
            # Position tooltip below the widget with a small gap
            y_position = y + widget.winfo_height() + 2
            
            # Set tooltip position
            tooltip.wm_geometry(f"+{x_position}+{y_position}")
            
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def create_border(self):
        """Create rounded corners for the window"""
        border_color = '#282828'
        self.root.configure(bg=border_color)
        
        if hasattr(self.root, '_root'):  # Check if running on Windows
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                style = windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
                style = style | 0x00080000  # WS_EX_LAYERED
                DWMWCP_ROUND = 2  # Define DWMWCP_ROUND with the appropriate value
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    33,  # DWMWA_WINDOW_CORNER_PREFERENCE
                    byref(c_int(DWMWCP_ROUND)),
                    sizeof(c_int)
                )
            except:
                pass

    def position_window(self):
        """Position window with saved coordinates or default position"""
        try:
            # Try to load saved position
            with open('.window_position', 'r') as f:
                x, y = map(int, f.read().split(','))
        except:
            # Use default position if no saved position exists
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - self.width - 20
            y = screen_height - self.height - 40
        
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')

    def save_window_position(self):
        """Save current window position"""
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            with open('.window_position', 'w') as f:
                f.write(f'{x},{y}')
        except Exception as e:
            print(f"Error saving window position: {e}")

    def load_window_position(self):
        """Load and apply saved window position with multi-monitor support"""
        try:
            with open('.window_position', 'r') as f:
                pos = f.read().strip().split(',')
                if len(pos) == 2:
                    x, y = map(int, pos)
                    
                    # Validate position is within any monitor bounds
                    valid_position = False
                    for monitor in self.monitors:
                        if (monitor['left'] <= x <= monitor['right'] - self.width and
                            monitor['top'] <= y <= monitor['bottom'] - self.height):
                            valid_position = True
                            break
                    
                    if valid_position:
                        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
                        return
                        
            # If no valid saved position, center on primary monitor
            self.center_on_primary_monitor()
            
        except Exception as e:
            print(f"Error loading window position: {e}")
            self.center_on_primary_monitor()

    def center_on_primary_monitor(self):
        """Center the window on the primary monitor"""
        primary = self.monitors[0]  # Primary monitor is typically first
        x = primary['left'] + (primary['width'] - self.width) // 2
        y = primary['top'] + (primary['height'] - self.height) // 2
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')

    def start_move(self, event):
        """Start window drag"""
        self.x = event.x_root - self.root.winfo_x()
        self.y = event.y_root - self.root.winfo_y()

    def on_move(self, event):
        """Handle window drag with edge snapping for all monitors"""
        if hasattr(self, 'x'):
            # Calculate new position
            x = event.x_root - self.x
            y = event.y_root - self.y
            
            # Check each monitor for edge snapping
            snapped = False
            for monitor in self.monitors:
                # Check left edge
                if abs(x - monitor['left']) < self.snap_threshold:
                    x = monitor['left']
                    self.snap_positions['x'] = 'left'
                    snapped = True
                    break
                    
                # Check right edge
                elif abs((x + self.width) - monitor['right']) < self.snap_threshold:
                    x = monitor['right'] - self.width
                    self.snap_positions['x'] = 'right'
                    snapped = True
                    break
                    
            if not snapped:
                self.snap_positions['x'] = None
                
            # Check vertical snapping for current monitor
            current_monitor = self.get_current_monitor(x, y)
            if current_monitor:
                # Top edge
                if abs(y - current_monitor['top']) < self.snap_threshold:
                    y = current_monitor['top']
                    self.snap_positions['y'] = 'top'
                # Bottom edge
                elif abs((y + self.height) - current_monitor['bottom']) < self.snap_threshold:
                    y = current_monitor['bottom'] - self.height
                else:
                    self.snap_positions['y'] = None
                    
            # Update window position
            self.root.geometry(f"+{x}+{y}")

    def get_current_monitor(self, x, y):
        """Determine which monitor the window is currently on"""
        for monitor in self.monitors:
            if (monitor['left'] <= x <= monitor['right'] and 
                monitor['top'] <= y <= monitor['bottom']):
                return monitor
        return self.monitors[0]  # Default to primary monitor

    def stop_move(self, event):
        """Stop window drag and finalize snapping with multi-monitor support"""
        if hasattr(self, 'x'):
            # Get current position
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            
            # Get current monitor
            current_monitor = self.get_current_monitor(x, y)
            
            # Apply monitor-specific snapping
            if current_monitor:
                # Horizontal snapping
                if abs(x - current_monitor['left']) < self.snap_threshold:
                    x = current_monitor['left']
                elif abs((x + self.width) - current_monitor['right']) < self.snap_threshold:
                    x = current_monitor['right'] - self.width
                
                # Vertical snapping
                if abs(y - current_monitor['top']) < self.snap_threshold:
                    y = current_monitor['top']
                elif abs((y + self.height) - current_monitor['bottom']) < self.snap_threshold:
                    y = current_monitor['bottom'] - self.height
            
            # Apply final position
            self.root.geometry(f"+{x}+{y}")
            
            # Clean up
            del self.x
            del self.y

    def minimize_window(self, event=None):
        if not self.minimized:
            self.normal_geometry = self.root.geometry()
            screen_width = self.root.winfo_screenwidth()
            self.root.geometry(f'{self.width}x{self.height}-{screen_width+100}+0')
            self.minimized = True
            self.show_taskbar_icon()
        else:
            self.root.geometry(self.normal_geometry)
            self.minimized = False
            if hasattr(self, 'taskbar_icon'):
                self.taskbar_icon.destroy()

    def show_taskbar_icon(self):
        self.taskbar_icon = tk.Toplevel(self.root)
        self.taskbar_icon.title("Toastify")
        self.taskbar_icon.geometry('1x1+0+0')
        self.taskbar_icon.bind('<Button-1>', self.minimize_window)
        self.taskbar_icon.overrideredirect(False)
        self.taskbar_icon.attributes('-toolwindow', True)
        self.taskbar_icon.withdraw()
        self.taskbar_icon.iconify()

    def update_track_info(self):
        """Update track information with faster polling"""
        # Don't update if only settings UI is visible
        if not self.full_ui_initialized:
            return
            
        last_track_id = None
        while True:
            try:
                track_info = self.spotify_client.get_current_track()
                
                if track_info:
                    # Check if track has changed
                    current_track_id = track_info.get('track_id')
                    track_changed = current_track_id != last_track_id
                    
                    if track_changed:
                        # Full update for track change
                        self.full_title = track_info.get('title', 'Not playing')
                        self.scroll_offset = 0
                        self.scroll_paused = False
                        
                        if track_info.get('album_art_url'):
                            self.root.after(0, lambda url=track_info['album_art_url']: 
                                          self.update_album_art(url))
                        last_track_id = current_track_id
                    
                    # Always update playback state and progress
                    def update_ui():
                        try:
                            is_playing = track_info.get('is_playing', False)
                            # Update play button color based on state
                            self.playback_buttons[2].configure(
                                text='⏸' if is_playing else '⏯',
                                fg=self.text_color if is_playing else self.artist_color
                            )
                            
                            # Immediate playback state update
                            self.playback_buttons[2].configure(
                                text='⏸' if track_info.get('is_playing', False) else '⏯'
                            )
                            
                            # Update progress with interpolation
                            if track_info.get('is_playing', False):
                                progress = track_info.get('progress_ms', 0)
                                # Add elapsed time since last update
                                progress += int((time.time() - track_info.get('timestamp', time.time())) * 1000)
                                self.update_progress_bar(progress, track_info.get('duration_ms', 1))
                            
                            if track_changed:
                                # Update title and artist only on track change
                                title = self.full_title
                                if len(title) > 20:  # Changed from 35
                                    self.title_label.config(text=title[:32])  # Initial truncated view
                                else:
                                    self.title_label.config(text=title)
                                
                                if 'artist_list' in track_info and 'artist_uris' in track_info:
                                    self.update_artist_labels(track_info['artist_list'], 
                                                           track_info['artist_uris'])
                            
                            # Update shuffle and volume state
                            self.is_shuffled = track_info.get('is_shuffled', False)
                            self.playback_buttons[0].configure(
                                fg=self.text_color if self.is_shuffled else self.artist_color
                            )
                            
                            if 'volume' in track_info:
                                self.update_volume_bar(track_info['volume'])
                                
                        except Exception as e:
                            print(f"Error updating UI: {e}")
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.reset_display())
                
            except Exception as e:
                print(f"Error in update_track_info: {e}")
                
            time.sleep(0.1)  # Poll every 100ms instead of 1s

    def reset_display(self):
        """Reset display when no track is playing"""
        # Only update UI elements if full UI is initialized
        if not self.full_ui_initialized:
            return
            
        self.title_label.config(text="Not playing", fg=self.text_color)
        self.clear_artist_labels()
        self.update_progress_bar(0, 1)

    def toggle_pin(self, event=None):
        """Handle pin button state"""
        self.is_pinned = not self.is_pinned
        self.root.wm_attributes('-topmost', self.is_pinned)
        # Update pin button color
        self.pin_button.configure(
            fg=self.text_color if self.is_pinned else self.artist_color
        )

    def on_progress_hover(self, event):
        self.progress_bar.configure(cursor='hand2')

    def on_progress_leave(self, event):
        self.progress_bar.configure(cursor='')

    def format_time(self, ms):
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def get_click_position(self, event):
        bar_width = self.progress_bar.winfo_width()
        click_x = event.x
        # Ensure click_x is within bounds
        click_x = max(0, min(click_x, bar_width))
        return click_x / bar_width

    def on_progress_click(self, event):
        """Handle progress bar click with immediate visual feedback"""
        self.seeking = True
        position = self.get_click_position(event)
        # Update visuals immediately
        self.update_progress_visual(position)
        # Then seek
        if hasattr(self, 'current_duration') and self.current_duration:
            seek_position = int(position * self.current_duration)
            self.spotify_client.seek_to_position(seek_position)

    def on_progress_drag(self, event):
        if hasattr(self, 'seeking') and self.seeking:
            position = self.get_click_position(event)
            self.update_progress_visual(position)

    def on_progress_release(self, event):
        if hasattr(self, 'seeking') and self.seeking:
            position = self.get_click_position(event)
            if hasattr(self, 'current_duration') and self.current_duration:
                seek_position = int(position * self.current_duration)
                self.spotify_client.seek_to_position(seek_position)
            self.seeking = False

    def update_progress_visual(self, position):
        """Update progress bar with current theme color"""
        bar_width = self.progress_bar.winfo_width()
        progress_width = bar_width * position
        
        # Update progress bar position and color
        self.progress_bar.coords(
            'progress_indicator',
            0, 0, progress_width, self.progress_bar.winfo_height()
        )
        self.progress_bar.itemconfig('progress_indicator', fill=self.text_color)

    def update_progress_bar(self, progress_ms, duration_ms):
        """Update progress bar with current theme color"""
        if duration_ms > 0 and hasattr(self, 'progress_bar'):
            position = progress_ms / duration_ms
            bar_width = self.progress_bar.winfo_width()
            progress_width = bar_width * position
            
            # Force dimensions to stay constant
            self.progress_frame.configure(height=12)  # Account for padding
            self.progress_bar.configure(height=4)
            
            # Update progress bar with fixed dimensions
            self.progress_bar.coords(
                self.progress_indicator,
                0, 0, progress_width, 4
            )
            self.progress_bar.itemconfig(self.progress_indicator, fill=self.text_color)
            
            # Update time labels
            self.current_time.config(text=self.format_time(progress_ms))
            self.total_time.config(text=self.format_time(duration_ms))
            
            # Store current duration
            self.current_duration = duration_ms
        else:
            # Reset progress bar
            self.update_progress_visual(0)
            self.current_time.config(text="0:00")
            self.total_time.config(text="0:00")

    def toggle_shuffle(self):
        """Handle shuffle with immediate feedback"""
        self.is_shuffled = not self.is_shuffled
        # Update UI instantly
        self.playback_buttons[0].configure(
            fg=self.text_color if self.is_shuffled else self.artist_color
        )
        # Then toggle shuffle
        self.spotify_client.toggle_shuffle()

    def toggle_volume(self):
        """Handle volume with immediate feedback"""
        self.is_muted = not self.is_muted
        # Update UI instantly
        self.playback_buttons[4].configure(text='🔈' if self.is_muted else '🔊')
        # Then toggle volume
        self.spotify_client.toggle_volume()

    def start_title_scroll(self, event=None):
        """Start scrolling the title text when hovering"""
        if len(self.full_title) > 10:
            self.title_scroll_index = 0
            self.title_scroll_active = True
            self.scroll_title_text()  # Start scrolling immediately

    def stop_title_scroll(self, event=None):
        """Stop scrolling and reset title text"""
        self.title_scroll_active = False  # Remove hasattr check
        if len(self.full_title) > 35:
            truncated = self.full_title[:32] + '...'
            self.title_label.config(text=truncated)

    def scroll_title_text(self):
        """Scroll the title text with smooth animation"""
        if self.title_scroll_active:
            # Add padding between repetitions
            text = self.full_title + '          ' + self.full_title
            
            # Smoother scrolling with smaller steps
            pixels_per_step = 1
            display_text = text[self.title_scroll_index:self.title_scroll_index + 35]
            self.title_label.config(text=display_text)
            
            # Reset index when reaching the end of first title
            if self.title_scroll_index >= len(self.full_title):
                self.title_scroll_index = 0
            else:
                self.title_scroll_index += pixels_per_step
            
            # Higher refresh rate for smoother scrolling
            self.root.after(40, self.scroll_title_text)  # 25fps

    def update_artist_labels(self, artists, uris):
        """Update artist labels for current track"""
        # Clear existing labels FIRST
        self.clear_artist_labels()
        self.artist_labels = []  # Reset the list
        self.artist_uris = []    # Reset URIs list
        
        # Create new labels for each artist
        for i, (artist, uri) in enumerate(zip(artists, uris)):
            if i > 0:  # Add separator
                separator = tk.Label(self.artist_frame,
                                  text=",",
                                  bg=self.bg_color,
                                  fg=self.artist_color,
                                  font=('Segoe UI', 9))
                separator.pack(side='left', padx=(0, 0))
                self.artist_labels.append(separator)
            
            label = tk.Label(self.artist_frame,
                           text=artist,
                           bg=self.bg_color,
                           fg=self.artist_color,
                           font=('Segoe UI', 9),
                           cursor='hand2')
            label.pack(side='left', padx=(0, 0))
            
            # Store URI in the label for direct access
            label.uri = uri
            
            # Simplified event bindings with direct URI access
            label.bind('<Enter>', lambda e, lbl=label: lbl.configure(
                fg='#FFFFFF', 
                font=('Segoe UI', 9, 'underline')
            ))
            label.bind('<Leave>', lambda e, lbl=label: lbl.configure(
                fg=self.artist_color, 
                font=('Segoe UI', 9)
            ))
            label.bind('<Button-1>', lambda e, uri=uri: 
                      self.spotify_client.open_artist_profile(uri))
            
            self.artist_labels.append(label)
            self.artist_uris.append(uri)

    def clear_artist_labels(self):
        """Clear all existing artist labels"""
        for label in self.artist_labels:
            label.destroy()
        self.artist_labels.clear()  # Use clear() instead of reassignment
        self.artist_uris.clear()

    def on_volume_hover(self, event):
        self.volume_bar.configure(cursor='hand2')

    def on_volume_leave(self, event):
        self.volume_bar.configure(cursor='')

    def get_volume_position(self, event):
        bar_width = self.volume_bar.winfo_width()
        click_x = event.x
        click_x = max(0, min(click_x, bar_width))
        return click_x / bar_width

    def on_volume_click(self, event):
        """Handle volume click with immediate visual feedback"""
        position = self.get_volume_position(event)
        volume = int(position * 100)
        # Update visuals immediately
        self.update_volume_bar(volume)
        # Then set volume
        self.spotify_client.set_volume(volume)

    def on_volume_drag(self, event):
        """Handle volume drag with immediate visual feedback"""
        position = self.get_volume_position(event)
        volume = int(position * 100)
        # Update visuals immediately
        self.update_volume_bar(volume)
        # Then set volume
        self.spotify_client.set_volume(volume)

    def update_volume_bar(self, volume):
        """Update volume bar with current theme color"""
        if not hasattr(self, 'last_volume'):
            self.last_volume = volume
        
        bar_width = self.volume_bar.winfo_width()
        volume_width = bar_width * (volume / 100)
        
        # Update volume indicator with current theme color
        self.volume_bar.delete('volume_indicator')
        self.volume_bar.create_rectangle(
            0, 0, volume_width, 3,
            fill=self.text_color,  # Use current theme color
            width=0,
            tags='volume_indicator'
        )
        
        self.last_volume = volume

    def toggle_playback(self):
        """Handle play/pause with immediate feedback"""
        # Update UI instantly
        is_playing = self.playback_buttons[2].cget('text') == '⏸'
        self.playback_buttons[2].configure(
            text='⏯' if is_playing else '⏸'
        )
        # Then toggle playback
        self.spotify_client.toggle_playback() 

    def update_colors(self, base_color):
        """Update UI colors based on dominant color"""
        # Convert hex to RGB
        if isinstance(base_color, str):
            # Remove '#' and convert to RGB
            r = int(base_color[1:3], 16)
            g = int(base_color[3:5], 16)
            b = int(base_color[5:7], 16)
            base_color = (r, g, b)
        
        # Calculate brightness
        brightness = (base_color[0] * 299 + base_color[1] * 587 + base_color[2] * 114) / 1000
        
        # Create color scheme
        self.bg_color = f'#{base_color[0]:02x}{base_color[1]:02x}{base_color[2]:02x}'
        self.text_color = '#FFFFFF' if brightness < 128 else '#000000'
        self.artist_color = '#B3B3B3' if brightness < 128 else '#666666'
        
        # Update UI elements
        self.update_ui_colors()

    def update_ui_colors(self):
        """Apply color scheme to UI elements"""
        # Update all interactive elements with new accent color
        
        # Update progress bar color
        self.progress_bar.itemconfig(self.progress_indicator, fill=self.text_color)
        self.progress_bar.itemconfig('progress_indicator', fill=self.text_color)
        
        # Update volume bar color
        self.volume_bar.delete('volume_indicator')
        self.volume_bar.create_rectangle(
            0, 0, 
            self.volume_bar.winfo_width() * (self.last_volume if hasattr(self, 'last_volume') else 100) / 100, 
            3,
            fill=self.text_color,
            width=0,
            tags='volume_indicator'
        )
        
        # Update album art border
        self.album_art_label.configure(
            highlightcolor=self.text_color,
            highlightbackground=self.text_color
        )
        
        # Update active states for buttons
        if self.is_pinned:
            self.pin_button.configure(fg=self.text_color)
        
        if self.is_shuffled:
            self.playback_buttons[0].configure(fg=self.text_color)
        
        # Update play button if playing
        if self.playback_buttons[2].cget('text') == '⏸':
            self.playback_buttons[2].configure(fg=self.text_color)
        
        # Update hover states
        for btn in self.playback_buttons:
            btn.bind('<Enter>', lambda e, b=btn: b.configure(fg=self.text_color))
            
        self.pin_button.bind('<Enter>', lambda e: self.pin_button.configure(fg=self.text_color))
        self.color_button.bind('<Enter>', lambda e: self.color_button.configure(fg=self.text_color))
        
        # Update settings button if settings are open
        if hasattr(self, 'settings_open') and self.settings_open:
            self.settings_button.configure(fg=self.text_color)
            
        # Update color picker button if panel is open
        if hasattr(self, 'color_panel'):
            self.color_button.configure(fg=self.text_color)

    def update_album_art(self, url):
        """Update album artwork display"""
        try:
            # Download and resize image
            response = requests.get(url)
            img = Image.open(io.BytesIO(response.content))
            img = img.resize((20, 20), Image.Resampling.LANCZOS)  # Small square size
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update label
            self.album_art_label.configure(image=photo)
            self.album_art_label.image = photo  # Keep reference
        except Exception as e:
            print(f"Error updating album art: {e}")
            self.album_art_label.configure(image='')

    def show_loading_animation(self):
        """Show Spotify-style loading animation with triple dots"""
        # Create loading frame
        self.loading_frame = tk.Frame(self.root, bg=self.bg_color)
        self.loading_frame.pack(fill='both', expand=True)
        
        # Create frame for dots
        self.dots_frame = tk.Frame(self.loading_frame, bg=self.bg_color)
        self.dots_frame.pack(expand=True)
        
        # Create three dots
        self.dots = []
        for i in range(3):
            dot = tk.Label(
                self.dots_frame,
                text="•",
                font=('Segoe UI', 14),
                bg=self.bg_color,
                fg=self.text_color
            )
            dot.pack(side='left', padx=2)
            self.dots.append(dot)
            
        # Start animation
        self.animate_loading()

    def animate_loading(self):
        """Animate the dots with smoother fade effect"""
        if hasattr(self, 'dots'):
            def fade(step=0):
                if not hasattr(self, 'dots'):
                    return
                
                # Smoother sine-based fade for each dot
                import math
                for i, dot in enumerate(self.dots):
                    # Use sine wave for smoother transitions
                    phase = (step + i * 8) % 24  # Longer cycle
                    opacity = (math.sin(phase * math.pi / 12) + 1) / 2  # Smooth sine wave
                    
                    # Update dot color with opacity
                    r = int(int(self.text_color[1:3], 16) * opacity)
                    g = int(int(self.text_color[3:5], 16) * opacity)
                    b = int(int(self.text_color[5:7], 16) * opacity)
                    color = f'#{r:02x}{g:02x}{b:02x}'
                    
                    dot.configure(fg=color)
                
                # Faster refresh rate for smoother animation
                self.root.after(33, lambda: fade(step + 1))  # ~30fps
            
            fade()

    def create_main_ui(self):
        """Create main UI after loading"""
        # Hide the root window initially
        self.root.withdraw()
        
        # Create all UI elements
        self.create_ui()
        
        # Remove loading animation
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            delattr(self, 'loading_frame')
            delattr(self, 'dots')
        
        # Set background color
        self.root.configure(bg=self.bg_color)
        
        # Load last position if exists
        self.load_window_position()
        
        # Force update to ensure proper layout
        self.root.update_idletasks()
        
        # Show window with all elements properly sized
        def show_ui():
            self.root.deiconify()
            self.root.update_idletasks()
        
        # Slight delay to ensure smooth transition
        self.root.after(100, show_ui)

    def show_color_picker(self, event=None):
        """Show integrated color picker panel with smooth slide animation"""
        if hasattr(self, 'color_panel'):
            self.hide_color_picker()
            return
            
        # Store original height
        self.original_height = self.root.winfo_height()
        
        # Update color picker icon to current theme color
        self.color_button.configure(fg=self.text_color)
        
        # Create color panel frame - insert BEFORE the progress frame
        self.color_panel = tk.Frame(self.frame, bg=self.bg_color)
        self.color_panel.pack(after=self.playback_frame, before=self.progress_frame)
        
        # Create all the color picker contents
        self.create_color_picker_contents()
        
        # Get panel height
        self.root.update_idletasks()
        panel_height = self.color_panel.winfo_height()
        
        # Start with panel hidden below
        self.root.geometry(f'{self.width}x{self.original_height}')
        
        # Animate panel sliding up with easing
        def animate_slide(current_height, start_time):
            duration = 200  # Animation duration in milliseconds
            elapsed = time.time() * 1000 - start_time
            
            if elapsed < duration:
                # Easing function (ease-out)
                progress = elapsed / duration
                progress = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out
                
                new_height = self.original_height + (panel_height * progress)
                self.root.geometry(f'{self.width}x{int(new_height)}')
                
                # Force progress bar height to stay constant
                self.progress_bar.configure(height=4)
                self.progress_frame.configure(height=12)
                
                self.root.after(16, lambda: animate_slide(current_height, start_time))  # ~60fps
            else:
                # Ensure final height is exact
                final_height = self.original_height + panel_height
                self.root.geometry(f'{self.width}x{final_height}')
                
                # Force progress bar height one final time
                self.progress_bar.configure(height=4)
                self.progress_frame.configure(height=12)
        
        # Start animation
        animate_slide(0, time.time() * 1000)

    def hide_color_picker(self):
        """Hide color picker panel with smooth slide animation"""
        if hasattr(self, 'color_panel'):
            panel_height = self.color_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If settings panel is open, account for its height
            if hasattr(self, 'settings_panel') and self.settings_open:
                base_height += self.settings_panel.winfo_height()
            
            def animate_hide(start_time):
                duration = 200
                elapsed = time.time() * 1000 - start_time
                
                if elapsed < duration:
                    progress = elapsed / duration
                    progress = progress * progress  # Quadratic ease-in
                    
                    remaining_height = panel_height * (1 - progress)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    
                    # Keep progress bar dimensions
                    self.progress_bar.configure(height=4)
                    self.progress_frame.configure(height=12)
                    
                    self.root.after(16, lambda: animate_hide(start_time))
                else:
                    # Cleanup color panel specifically
                    self.color_panel.destroy()
                    delattr(self, 'color_panel')
                    self.color_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    
                    # Final progress bar adjustment
                    self.progress_bar.configure(height=4)
                    self.progress_frame.configure(height=12)

            animate_hide(time.time() * 1000)

    def hide_settings(self):
        """Hide settings panel with slide animation"""
        try:
            if not self.settings_open or not hasattr(self, 'settings_panel'):
                return
                
            panel_height = self.settings_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If color panel is open, account for its height
            if hasattr(self, 'color_panel'):
                base_height += self.color_panel.winfo_height()
            
            def animate_hide(progress):
                if progress <= 1.0:
                    ease = progress * progress
                    remaining_height = panel_height * (1 - ease)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    self.root.after(16, lambda: animate_hide(progress + 0.05))
                else:
                    # Clean up but maintain color panel height if open
                    if hasattr(self, 'settings_panel'):
                        self.settings_panel.destroy()
                    self.settings_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    self.settings_open = False
                    
            animate_hide(0.0)
            
        except Exception as e:
            print(f"Error hiding settings: {e}")
            traceback.print_exc()

    def create_color_picker_contents(self):
        """Create the contents of the color picker panel"""
        # Add separator line that extends full width
        separator = tk.Frame(self.color_panel, height=1, bg='#282828')
        separator.pack(fill='x', padx=0)
        
        # Create inner frame with left alignment
        inner_content = tk.Frame(self.color_panel, bg=self.bg_color)
        inner_content.pack(fill='x', padx=10, anchor='w')
        
        # Add title with left alignment
        title_label = tk.Label(inner_content, 
                             text="Theme", 
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.bg_color,
                             fg='#FFFFFF')
        title_label.pack(anchor='w', pady=(5, 5))
        
        # Create single row for all controls
        control_row = tk.Frame(inner_content, bg=self.bg_color)
        control_row.pack(fill='x', anchor='w', pady=(0, 5))
        
        # Left side: Color preview and hex input
        left_section = tk.Frame(control_row, bg=self.bg_color)
        left_section.pack(side='left')
        
        # Color preview
        self.color_preview = tk.Frame(left_section, 
                                        width=20, 
                                        height=20, 
                                        bg=self.text_color,
                                        highlightthickness=1,
                                        highlightbackground='#282828',
                                        cursor='hand2')
        self.color_preview.pack(side='left')
        self.color_preview.pack_propagate(False)
        self.color_preview.bind('<Button-1>', self.show_color_dialog)
        
        # Hex input
        self.hex_var = tk.StringVar(value=self.text_color)
        hex_entry = tk.Entry(left_section, 
                           textvariable=self.hex_var,
                           width=8,
                           bg='#282828',
                           fg='#FFFFFF',
                           insertbackground='#FFFFFF',
                           relief='flat',
                           font=('Segoe UI', 9, 'bold'),
                           justify='center')
        hex_entry.pack(side='left', padx=(5, 15))
        hex_entry.configure(highlightthickness=0)
        hex_entry.bind('<Return>', lambda e: self.apply_color())
        
        # Right side: Buttons
        button_style = {
            'font': ('Segoe UI', 9, 'bold'),
            'bg': '#282828',
            'fg': '#FFFFFF',
            'padx': 8,    # Reduced from 12
            'pady': 4,    # Reduced from 6
            'cursor': 'hand2',
            'width': 6    # Reduced from 8
        }
        
        # Create buttons
        for text, command in [
            ("Reset", self.reset_color),
            ("Apply", self.apply_color)
        ]:
            btn = tk.Label(
                control_row,
                text=text,
                **button_style
            )
            btn.pack(side='right', padx=2)
            btn.bind('<Button-1>', lambda e, cmd=command: cmd())
            
            # Hover effects
            btn.bind('<Enter>', 
                    lambda e, b=btn: b.configure(bg='#383838'))
            btn.bind('<Leave>', 
                    lambda e, b=btn: b.configure(bg='#282828'))

    def update_color_preview(self, *args):
        """Update color preview from RGB values"""
        try:
            r = self.rgb_vars[0].get()
            g = self.rgb_vars[1].get()
            b = self.rgb_vars[2].get()
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_preview.configure(bg=color)
            self.hex_var.set(color)
        except:
            pass

    def apply_color(self):
        """Apply selected color"""
        new_color = self.hex_var.get()
        self.text_color = new_color
        
        # Save color
        with open('.custom_color', 'w') as f:
            f.write(new_color)
        
        # Update all UI elements with new color
        self.update_ui_colors()
        
        # Update color button to match new color
        self.color_button.configure(fg=self.text_color)
        
        # Don't close the window, just update the preview
        self.color_preview.configure(bg=new_color)

    def reset_color(self):
        """Reset to Spotify green"""
        self.text_color = '#1DB954'
        
        # Update color preview and hex input if color picker is open
        if hasattr(self, 'color_preview'):
            self.color_preview.configure(bg=self.text_color)
            self.hex_var.set(self.text_color)
        
        self.update_ui_colors()
        
        # Save default color
        with open('.custom_color', 'w') as f:
            f.write(self.text_color)

    def show_color_dialog(self, event=None):
        """Show system color picker dialog"""
        # Get color picker box position
        x = self.root.winfo_x() + self.root.winfo_width() + 10
        y = self.root.winfo_y()
        
        # Use colorchooser directly instead of tk.call
        color = colorchooser.askcolor(
            color=self.text_color,
            title="Choose Color",
            parent=self.root
        )
        
        if (color[1]):  # If color was selected (not cancelled)
            # Update preview and hex
            self.color_preview.configure(bg=color[1])
            self.hex_var.set(color[1])
            
            # Apply the color immediately
            self.text_color = color[1]
            self.update_ui_colors()
            
            # Update color button to match new color
            self.color_button.configure(fg=color[1])
            
            # Save the color
            with open('.custom_color', 'w') as f:
                f.write(color[1])

    def bind_shortcuts(self):
        """Bind keyboard shortcuts for playback control"""
        # Play/Pause - Ctrl + Alt + Space
        self.root.bind('<Control-Alt-space>', lambda e: self.toggle_playback())
        
        # Previous Track - Ctrl + Alt + Left
        self.root.bind('<Control-Alt-Left>', lambda e: self.spotify_client.previous_track())
        
        # Next Track - Ctrl + Alt + Right
        self.root.bind('<Control-Alt-Right>', lambda e: self.spotify_client.next_track())
        
        # Volume Up - Ctrl + Alt + Up
        self.root.bind('<Control-Alt-Up>', lambda e: self.adjust_volume(10))
        
        """Adjust volume by delta percent"""
        def adjust_volume(delta):
            if hasattr(self, 'last_volume'):
                new_volume = max(0, min(100, self.last_volume + delta))
                # Update volume bar visually
                self.update_volume_bar(new_volume)
                # Update Spotify volume
                self.spotify_client.set_volume(new_volume)
                # Store new volume
                self.last_volume = new_volume

    def continuous_scroll(self):
        """Continuously scroll the title text"""
        if hasattr(self, 'full_title') and len(self.full_title) > 20:  # Changed from 35
            if not self.scroll_paused:
                # Create scrolling text with padding
                scroll_text = self.full_title + "     "  # Removed double text
                text_width = len(scroll_text)
                
                # Calculate display position
                start_pos = self.scroll_offset % text_width
                end_pos = start_pos + 32  # Show 32 characters at a time
                
                # Get display text with wrap-around
                if end_pos <= text_width:
                    display_text = scroll_text[start_pos:end_pos]
                else:
                    # Wrap around to the beginning
                    overflow = end_pos - text_width
                    display_text = scroll_text[start_pos:] + scroll_text[:overflow]
                
                # Update label
                self.title_label.config(text=display_text)
                
                # Increment scroll position
                self.scroll_offset += 1
                
                # Add pause at the beginning of each cycle
                if self.scroll_offset % text_width == 0:
                    self.scroll_paused = True
                    self.root.after(2000, self.resume_scroll)  # 2 second pause
                    
        # Continue scrolling
        self.root.after(125, self.continuous_scroll)  # Faster scroll speed (50ms)

    def resume_scroll(self):
        """Resume scrolling after pause"""
        self.scroll_paused = False

    def show_settings(self, event=None):
        """Show or hide settings panel with slide animation"""
        try:
            print("Attempting to toggle settings...")  # Debug print
            if not self.root.winfo_exists():
                print("Window doesn't exist")  # Debug print
                return
                
            if hasattr(self, 'settings_open') and self.settings_open:
                print("Closing settings panel")  # Debug print
                self.hide_settings()
                return
        
            # Force window to be visible first
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.update()
            
            # Create panel after ensuring window is visible
            self.settings_panel = tk.Frame(self.frame, bg=self.bg_color)
            self.settings_panel.pack(after=self.playback_frame, before=self.progress_frame)
            
            print("Creating settings contents...")  # Debug print
            self.create_settings_contents()
            
            # Force geometry update
            self.root.update_idletasks()
            
            # Get accurate panel height after contents are created
            panel_height = self.settings_panel.winfo_reqheight()
            
            # Mark settings as open and store original height
            self.settings_open = True
            self.original_height = self.root.winfo_height()
            
            # Update settings icon
            self.settings_button.configure(fg=self.text_color)
            
            def animate_slide(progress):
                if progress <= 1.0:
                    # Ease out animation
                    ease = 1 - (1 - progress) * (1 - progress)
                    new_height = self.original_height + (panel_height * ease)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    # Ensure contents are visible by updating canvas scrollregion
                    self.root.update_idletasks()
                    self.root.after(16, lambda: animate_slide(progress + 0.05))
                else:
                    # Finalize animation with exact height
                    self.root.geometry(f'{self.width}x{int(self.original_height + panel_height)}')
                    
            animate_slide(0.0)
                
        except Exception as e:
            print(f"Error showing settings: {e}")
            traceback.print_exc()

    def hide_settings(self):
        """Hide settings panel with slide animation"""
        try:
            if not self.settings_open or not hasattr(self, 'settings_panel'):
                return
                
            panel_height = self.settings_panel.winfo_height()
            current_height = self.root.winfo_height()
            base_height = self.height  # Base window height
            
            # If color panel is open, account for its height
            if hasattr(self, 'color_panel'):
                base_height += self.color_panel.winfo_height()
            
            def animate_hide(progress):
                if progress <= 1.0:
                    ease = progress * progress
                    remaining_height = panel_height * (1 - ease)
                    new_height = current_height - (panel_height - remaining_height)
                    self.root.geometry(f'{self.width}x{int(new_height)}')
                    self.root.after(16, lambda: animate_hide(progress + 0.05))
                else:
                    # Clean up but maintain color panel height if open
                    if hasattr(self, 'settings_panel'):
                        self.settings_panel.destroy()
                    self.settings_button.configure(fg=self.artist_color)
                    self.root.geometry(f'{self.width}x{base_height}')
                    self.settings_open = False
                    
            animate_hide(0.0)
            
        except Exception as e:
            print(f"Error hiding settings: {e}")
            traceback.print_exc()

    def create_settings_contents(self):
        """Create the contents of the settings panel"""
        # Move settings panel before progress bar
        if hasattr(self, 'progress_frame'):
            self.settings_panel.pack(before=self.progress_frame)  # Fixed this line
        
        # Add separator line that extends full width
        separator = tk.Frame(self.settings_panel, height=1, bg='#282828')
        separator.pack(fill='x', padx=0)
        
        # Create inner frame
        inner_content = tk.Frame(self.settings_panel, bg=self.bg_color)
        inner_content.pack(fill='x', padx=10)
        
        # Add title
        title_label = tk.Label(inner_content, 
                             text="Settings", 
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.bg_color,
                             fg='#FFFFFF')
        title_label.pack(anchor='w', pady=(5, 5))
        
        # Add a message if credentials are missing
        if not self.spotify_client.has_valid_credentials():
            msg_label = tk.Label(inner_content,
                               text="Please enter your Spotify API credentials to continue",
                               bg=self.bg_color,
                               fg='#FFFFFF',
                               font=('Segoe UI', 9))
            msg_label.pack(anchor='w', pady=(0, 10))
        
        # Create input fields
        input_style = {
            'bg': '#282828',
            'fg': '#FFFFFF',
            'insertbackground': '#FFFFFF',
            'relief': 'flat',
            'font': ('Segoe UI', 9),
            'width': 35
        }
        
        # Client ID input with placeholder
        tk.Label(inner_content, text="Client ID:", 
                bg=self.bg_color, fg='#FFFFFF',
                font=('Segoe UI', 9)).pack(anchor='w')
        self.client_id_var = tk.StringVar(value=self.spotify_client.auth_manager.client_id or "Enter your Spotify Client ID")
        self.client_id_entry = tk.Entry(inner_content, 
                                      textvariable=self.client_id_var,
                                      **input_style)
        if not self.spotify_client.auth_manager.client_id:
            self.client_id_entry.configure(fg='#666666')
            self.client_id_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(e, "Enter your Spotify Client ID"))
            self.client_id_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(e, "Enter your Spotify Client ID"))
        self.client_id_entry.pack(fill='x', pady=(0, 5))

        # Client Secret input with eye toggle
        tk.Label(inner_content, text="Client Secret:", 
                bg=self.bg_color, fg='#FFFFFF',
                font=('Segoe UI', 9)).pack(anchor='w')
                
        secret_frame = tk.Frame(inner_content, bg=self.bg_color)
        secret_frame.pack(fill='x', pady=(0, 10))
        
        self.client_secret_var = tk.StringVar(value=self.spotify_client.auth_manager.client_secret or "Enter your Spotify Client Secret")
        self.client_secret_entry = tk.Entry(secret_frame, 
                                          textvariable=self.client_secret_var,
                                          show='•',
                                          **input_style)
        self.client_secret_entry.pack(side='left', fill='x', expand=True)
        
        if not self.spotify_client.auth_manager.client_secret:
            self.client_secret_entry.configure(fg='#666666', show='')
            self.client_secret_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(e, "Enter your Spotify Client Secret"))
            self.client_secret_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(e, "Enter your Spotify Client Secret"))

        # Add eye toggle button
        self.eye_button = tk.Label(secret_frame, 
                                 text="👁", 
                                 bg=self.bg_color,
                                 fg=self.artist_color,
                                 cursor='hand2',
                                 padx=5)
        self.eye_button.pack(side='right')
        self.eye_button.bind('<Button-1>', self.toggle_secret_visibility)
        
        # Button row with consistent sizing
        button_row = tk.Frame(inner_content, bg=self.bg_color)
        button_row.pack(fill='x', pady=(0, 5))
        
        # Save button
        save_btn = tk.Label(
            button_row,
            text="Save",
            font=('Segoe UI', 9, 'bold'),
            bg='#282828',
            fg='#FFFFFF',
            padx=12,
            pady=6,
            cursor='hand2'
        )
        save_btn.pack(side='right', padx=5)
        save_btn.bind('<Button-1>', lambda e: self.save_settings())
        save_btn.bind('<Enter>', lambda e: save_btn.configure(bg='#383838'))
        save_btn.bind('<Leave>', lambda e: save_btn.configure(bg='#282828'))

    def save_settings(self):
        """Save client credentials and validate"""
        client_id = self.client_id_var.get().strip()
        client_secret = self.client_secret_var.get().strip()
        
        # Don't validate if they're placeholder texts
        if client_id == "Enter your Spotify Client ID" or client_secret == "Enter your Spotify Client Secret":
            self.show_message("Please enter valid credentials!", error=True)
            return
        
        # Validate credentials format
        if not self.validate_credentials(client_id, client_secret):
            self.show_message("Invalid credentials format!", error=True)
            return
            
        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:8888/callback'
        }
        
        try:
            # Test the credentials before saving
            test_client = SpotifyClient()
            test_client.auth_manager = SpotifyOAuth(