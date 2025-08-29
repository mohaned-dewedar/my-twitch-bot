#!/usr/bin/env python3
"""
CherryBott Automated Launcher

Streamlines the setup process by automating:
- Environment initialization 
- Twitch token generation
- Chrome profile management
- .env file updates
- Bot startup
"""

import os
import sys
import subprocess
import time
import re
import json
from pathlib import Path
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class CherryBottLauncher:
    """Automated launcher for CherryBott Twitch bot."""
    
    def __init__(self):
        """Initialize launcher with project paths."""
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.chrome_profiles = self._detect_chrome_profiles()
        
    def print_header(self):
        """Print application header."""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║           🍒 CherryBott Launcher       ║")
        print("║         Twitch Trivia Bot Setup       ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
    
    def main_menu(self):
        """Display main launcher menu."""
        while True:
            self.print_header()
            print(f"\n{Colors.OKBLUE}Select an option:{Colors.ENDC}")
            print(f"  {Colors.OKGREEN}1.{Colors.ENDC} 🚀 Quick Start (Full automated setup)")
            print(f"  {Colors.OKGREEN}2.{Colors.ENDC} 🔧 Manual Setup (Step by step)")
            print(f"  {Colors.OKGREEN}3.{Colors.ENDC} 🔑 Generate New Token Only")
            print(f"  {Colors.OKGREEN}4.{Colors.ENDC} ▶️  Start Bot (Skip setup)")
            print(f"  {Colors.OKGREEN}5.{Colors.ENDC} 🔍 Check Status")
            print(f"  {Colors.OKGREEN}6.{Colors.ENDC} ❌ Exit")
            
            try:
                choice = input(f"\n{Colors.OKCYAN}Enter your choice (1-6): {Colors.ENDC}").strip()
                
                if choice == "1":
                    self.quick_start()
                elif choice == "2":
                    self.manual_setup()
                elif choice == "3":
                    self.generate_token_only()
                elif choice == "4":
                    self.start_bot()
                elif choice == "5":
                    self.check_status()
                elif choice == "6":
                    print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
                    break
                else:
                    print(f"{Colors.WARNING}Invalid choice. Please try again.{Colors.ENDC}")
                    input("Press Enter to continue...")
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
                break
            except Exception as e:
                print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
                input("Press Enter to continue...")
    
    def quick_start(self):
        """Fully automated setup process."""
        print(f"\n{Colors.HEADER}🚀 Quick Start - Automated Setup{Colors.ENDC}")
        print("This will automatically set up everything you need!\n")
        
        # Step 1: Environment check
        print(f"{Colors.OKBLUE}Step 1: Checking environment...{Colors.ENDC}")
        if not self.check_environment():
            return
        
        # Step 2: Initialize environment  
        print(f"\n{Colors.OKBLUE}Step 2: Initializing uv environment...{Colors.ENDC}")
        if not self.initialize_environment():
            return
            
        # Step 3: Chrome profile selection
        print(f"\n{Colors.OKBLUE}Step 3: Chrome profile setup...{Colors.ENDC}")
        chrome_profile = self.select_chrome_profile()
        if not chrome_profile:
            return
            
        # Step 4: Generate token
        print(f"\n{Colors.OKBLUE}Step 4: Generating Twitch token...{Colors.ENDC}")
        token = self.generate_twitch_token(chrome_profile)
        if not token:
            return
            
        # Step 5: Update .env
        print(f"\n{Colors.OKBLUE}Step 5: Updating configuration...{Colors.ENDC}")
        if not self.update_env_file(token):
            return
            
        # Step 6: Database setup
        print(f"\n{Colors.OKBLUE}Step 6: Setting up database...{Colors.ENDC}")
        if not self.setup_database():
            return
            
        # Step 7: Start bot
        print(f"\n{Colors.OKGREEN}✅ Setup complete! Starting CherryBott...{Colors.ENDC}")
        self.start_bot()
    
    def manual_setup(self):
        """Step-by-step manual setup."""
        print(f"\n{Colors.HEADER}🔧 Manual Setup{Colors.ENDC}")
        
        steps = [
            ("Environment Check", self.check_environment),
            ("Initialize Environment", self.initialize_environment), 
            ("Chrome Profile", lambda: self.select_chrome_profile() is not None),
            ("Generate Token", lambda: self.generate_twitch_token() is not None),
            ("Update .env", lambda: self.update_env_file() is not None),
            ("Setup Database", self.setup_database),
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            print(f"\n{Colors.OKBLUE}Step {i}: {step_name}{Colors.ENDC}")
            input("Press Enter to continue...")
            
            if not step_func():
                print(f"{Colors.FAIL}❌ Step failed. Setup incomplete.{Colors.ENDC}")
                return
                
        print(f"\n{Colors.OKGREEN}✅ Manual setup complete!{Colors.ENDC}")
        
        start = input("Start bot now? (y/N): ").strip().lower()
        if start == 'y':
            self.start_bot()
    
    def generate_token_only(self):
        """Generate only a new Twitch token."""
        print(f"\n{Colors.HEADER}🔑 Generate New Twitch Token{Colors.ENDC}")
        
        chrome_profile = self.select_chrome_profile()
        if not chrome_profile:
            return
            
        token = self.generate_twitch_token(chrome_profile)
        if token:
            self.update_env_file(token)
            print(f"\n{Colors.OKGREEN}✅ Token updated successfully!{Colors.ENDC}")
        
        input("Press Enter to return to menu...")
    
    def check_environment(self) -> bool:
        """Check if required tools are available."""
        print("Checking required tools...")
        
        # Check uv
        if not self._command_exists("uv"):
            print(f"{Colors.FAIL}❌ uv not found. Please install: https://astral.sh/uv/install.sh{Colors.ENDC}")
            return False
        print(f"{Colors.OKGREEN}✅ uv found{Colors.ENDC}")
        
        # Check if Twitch CLI exists
        has_twitch_cli = self._command_exists("twitch")
        if not has_twitch_cli:
            print(f"{Colors.WARNING}⚠️  Twitch CLI not found - will provide manual instructions{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✅ Twitch CLI found{Colors.ENDC}")
            
        # Check Chrome
        chrome_cmd = self._find_chrome_command()
        if not chrome_cmd:
            print(f"{Colors.WARNING}⚠️  Chrome not found - manual token generation required{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✅ Chrome found: {chrome_cmd}{Colors.ENDC}")
            
        return True
    
    def initialize_environment(self) -> bool:
        """Initialize uv environment and dependencies."""
        try:
            print("Running uv sync...")
            result = subprocess.run(["uv", "sync"], cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}✅ Environment initialized{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}❌ uv sync failed: {result.stderr}{Colors.ENDC}")
                return False
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to initialize environment: {e}{Colors.ENDC}")
            return False
    
    def _detect_chrome_profiles(self) -> list:
        """Detect available Chrome profiles with enhanced details."""
        profiles = []
        
        # Common Chrome profile locations
        chrome_dirs = [
            "~/.config/google-chrome",
            "~/.config/chromium", 
            "~/Library/Application Support/Google/Chrome",
            "~/AppData/Local/Google/Chrome/User Data"
        ]
        
        # WSL-specific Chrome paths (Windows Chrome accessed from WSL)
        if self._is_wsl():
            chrome_dirs.extend([
                "/mnt/c/Users/*/AppData/Local/Google/Chrome/User Data",
                "/mnt/c/Users/*/AppData/Roaming/Google/Chrome/User Data"
            ])
        
        for chrome_dir in chrome_dirs:
            # Handle glob patterns for WSL (e.g., /mnt/c/Users/*/AppData/...)
            if '*' in chrome_dir:
                from glob import glob
                matching_dirs = glob(chrome_dir)
                for match_dir in matching_dirs:
                    expanded_dir = Path(match_dir)
                    if expanded_dir.exists():
                        for item in expanded_dir.iterdir():
                            if item.is_dir() and (item.name == "Default" or item.name.startswith("Profile")):
                                profile_info = self._get_profile_info(item)
                                profiles.append(profile_info)
            else:
                expanded_dir = Path(chrome_dir).expanduser()
                if expanded_dir.exists():
                    for item in expanded_dir.iterdir():
                        if item.is_dir() and (item.name == "Default" or item.name.startswith("Profile")):
                            # Try to get profile name from preferences
                            profile_info = self._get_profile_info(item)
                            profiles.append(profile_info)
                        
        return profiles
    
    def _is_wsl(self) -> bool:
        """Check if running in WSL environment."""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
        except FileNotFoundError:
            return False
    
    def _get_profile_info(self, profile_path: Path) -> dict:
        """Get profile information including display name."""
        profile_info = {
            'path': str(profile_path),
            'name': profile_path.name,
            'display_name': profile_path.name
        }
        
        # Try to read profile name from Preferences file
        try:
            prefs_file = profile_path / "Preferences"
            if prefs_file.exists():
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    import json
                    prefs = json.load(f)
                    if 'profile' in prefs and 'name' in prefs['profile']:
                        profile_info['display_name'] = prefs['profile']['name']
                    elif 'account_info' in prefs:
                        # Try to get account info
                        for account in prefs['account_info']:
                            if 'full_name' in account:
                                profile_info['display_name'] = f"{profile_path.name} ({account['full_name']})"
                                break
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            pass  # Use default name if preferences can't be read
            
        return profile_info
    
    def select_chrome_profile(self) -> Optional[str]:
        """Let user select Chrome profile for bot account."""
        print("\n📁 Available Chrome profiles:")
        
        if not self.chrome_profiles:
            print(f"{Colors.WARNING}No Chrome profiles detected.{Colors.ENDC}")
            print("You'll need to manually open Chrome with your bot account.")
            return "manual"
        
        # Check for saved default profile
        default_profile = self._get_default_profile()
        
        for i, profile_info in enumerate(self.chrome_profiles, 1):
            is_default = (default_profile and profile_info['path'] == default_profile)
            default_marker = " (DEFAULT)" if is_default else ""
            print(f"  {i}. {profile_info['display_name']}{default_marker}")
            
        print(f"  {len(self.chrome_profiles) + 1}. Manual (I'll open Chrome myself)")
        print(f"  {len(self.chrome_profiles) + 2}. Set default profile")
        
        # Auto-select default if available
        if default_profile:
            print(f"\n{Colors.OKCYAN}Press Enter to use default, or choose a number:{Colors.ENDC}")
            user_input = input(f"{Colors.OKCYAN}Choice (1-{len(self.chrome_profiles) + 2}, or Enter for default): {Colors.ENDC}").strip()
            
            if not user_input:  # User pressed Enter for default
                for profile_info in self.chrome_profiles:
                    if profile_info['path'] == default_profile:
                        print(f"{Colors.OKGREEN}Using default profile: {profile_info['display_name']}{Colors.ENDC}")
                        return profile_info['path']
        else:
            user_input = input(f"\n{Colors.OKCYAN}Select profile (1-{len(self.chrome_profiles) + 2}): {Colors.ENDC}").strip()
        
        try:
            choice = int(user_input)
            
            if 1 <= choice <= len(self.chrome_profiles):
                selected_profile = self.chrome_profiles[choice - 1]['path']
                return selected_profile
            elif choice == len(self.chrome_profiles) + 1:
                return "manual"
            elif choice == len(self.chrome_profiles) + 2:
                return self._set_default_profile()
            else:
                print(f"{Colors.FAIL}Invalid choice{Colors.ENDC}")
                return None
                
        except ValueError:
            print(f"{Colors.FAIL}Invalid input{Colors.ENDC}")
            return None
    
    def _get_default_profile(self) -> Optional[str]:
        """Get saved default Chrome profile."""
        config_file = self.project_root / ".launcher_config"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('default_chrome_profile')
            except (json.JSONDecodeError, KeyError):
                pass
        return None
    
    def _save_default_profile(self, profile_path: str) -> None:
        """Save default Chrome profile choice."""
        config_file = self.project_root / ".launcher_config"
        config = {}
        
        # Load existing config if it exists
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, KeyError):
                config = {}
        
        config['default_chrome_profile'] = profile_path
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"{Colors.OKGREEN}✅ Default profile saved{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  Could not save default profile: {e}{Colors.ENDC}")
    
    def _set_default_profile(self) -> Optional[str]:
        """Let user set a default Chrome profile."""
        print("\n🔧 Set Default Chrome Profile:")
        
        for i, profile_info in enumerate(self.chrome_profiles, 1):
            print(f"  {i}. {profile_info['display_name']}")
        
        try:
            choice = int(input(f"\n{Colors.OKCYAN}Select profile to set as default (1-{len(self.chrome_profiles)}): {Colors.ENDC}"))
            
            if 1 <= choice <= len(self.chrome_profiles):
                selected_profile = self.chrome_profiles[choice - 1]
                self._save_default_profile(selected_profile['path'])
                print(f"{Colors.OKGREEN}Default set to: {selected_profile['display_name']}{Colors.ENDC}")
                return selected_profile['path']
            else:
                print(f"{Colors.FAIL}Invalid choice{Colors.ENDC}")
                return None
                
        except ValueError:
            print(f"{Colors.FAIL}Invalid input{Colors.ENDC}")
            return None
    
    def generate_twitch_token(self, chrome_profile: Optional[str] = None) -> Optional[str]:
        """Generate Twitch OAuth token."""
        
        # Check if Twitch CLI is available
        if self._command_exists("twitch"):
            return self._generate_token_with_cli()
        else:
            return self._generate_token_manual(chrome_profile)
    
    def _generate_token_with_cli(self) -> Optional[str]:
        """Generate token using Twitch CLI."""
        print("Using Twitch CLI to generate token...")
        
        try:
            # Run twitch token command interactively
            cmd = ["twitch", "token", "-u", "--scopes", "chat:read chat:edit user:write:chat"]
            print(f"Running: {' '.join(cmd)}")
            print(f"{Colors.OKCYAN}This will open your browser for Twitch authorization...{Colors.ENDC}")
            
            # Run interactively and capture output
            import tempfile
            import os
            
            # Create a temporary file to capture output
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as temp_file:
                temp_path = temp_file.name
            
            try:
                # Run the command and redirect output to temp file
                full_cmd = f"twitch token -u --scopes 'chat:read chat:edit user:write:chat' 2>&1 | tee {temp_path}"
                result = subprocess.run(full_cmd, shell=True, text=True)
                
                # Read the captured output
                with open(temp_path, 'r') as f:
                    output = f.read()
                
                if result.returncode == 0:
                    # Extract token from output
                    token_match = re.search(r'User Access Token:\s*(\S+)', output)
                    scopes_match = re.search(r'Scopes:\s*\[(.*?)\]', output)
                    
                    if token_match:
                        token = token_match.group(1)
                        
                        # Check if we got the required scopes
                        if scopes_match:
                            granted_scopes = scopes_match.group(1)
                            required_scopes = ["chat:read", "chat:edit", "user:write:chat"]
                            
                            print(f"\\n{Colors.OKGREEN}Granted scopes: {granted_scopes}{Colors.ENDC}")
                            if not all(scope in granted_scopes for scope in required_scopes):
                                print(f"{Colors.WARNING}⚠️  Missing required scopes. Got: {granted_scopes}{Colors.ENDC}")
                                print(f"{Colors.WARNING}Required: {', '.join(required_scopes)}{Colors.ENDC}")
                                print(f"{Colors.WARNING}This might cause bot functionality issues.{Colors.ENDC}")
                        
                        print(f"{Colors.OKGREEN}✅ Token generated successfully{Colors.ENDC}")
                        return f"oauth:{token}" if not token.startswith("oauth:") else token
                    else:
                        print(f"{Colors.FAIL}❌ Could not extract token from CLI output{Colors.ENDC}")
                        print(f"Full output: {output}")
                        return None
                else:
                    print(f"{Colors.FAIL}❌ Twitch CLI failed{Colors.ENDC}")
                    return None
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error running Twitch CLI: {e}{Colors.ENDC}")
            return None
    
    def _generate_token_manual(self, chrome_profile: Optional[str] = None) -> Optional[str]:
        """Manual token generation process."""
        print(f"\n{Colors.WARNING}📋 Manual Token Generation Required{Colors.ENDC}")
        
        if chrome_profile and chrome_profile != "manual":
            # Try to open Chrome with specific profile
            chrome_cmd = self._find_chrome_command()
            if chrome_cmd:
                profile_arg = f"--profile-directory={Path(chrome_profile).name}"
                try:
                    subprocess.Popen([chrome_cmd, profile_arg, "https://dev.twitch.tv/console"])
                    print(f"{Colors.OKGREEN}✅ Opened Chrome with bot profile{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.WARNING}⚠️  Could not open Chrome: {e}{Colors.ENDC}")
        
        print(f"\n{Colors.OKBLUE}Follow these steps:{Colors.ENDC}")
        print("1. Open Chrome with your bot account profile")
        print("2. Go to: https://dev.twitch.tv/console")
        print("3. Create or select your application")
        print("4. Run this command in terminal:")
        print(f"{Colors.OKCYAN}   twitch token -u --scopes \"chat:read chat:edit user:write:chat\"{Colors.ENDC}")
        print("5. Copy the 'User Access Token' from the output")
        
        token = input(f"\n{Colors.OKCYAN}Paste your token here (with or without 'oauth:'): {Colors.ENDC}").strip()
        
        if token:
            # Add oauth: prefix if not present
            if not token.startswith("oauth:"):
                token = f"oauth:{token}"
            print(f"{Colors.OKGREEN}✅ Token received{Colors.ENDC}")
            return token
        else:
            print(f"{Colors.FAIL}❌ No token provided{Colors.ENDC}")
            return None
    
    def update_env_file(self, token: Optional[str] = None) -> bool:
        """Update .env file with new token."""
        if not token:
            print(f"{Colors.FAIL}❌ No token to update{Colors.ENDC}")
            return False
            
        try:
            # Read existing .env or create new
            env_content = {}
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_content[key] = value
            
            # Update token
            env_content['TWITCH_OAUTH_TOKEN'] = token
            
            # Ensure other required vars exist
            if 'TWITCH_BOT_NAME' not in env_content:
                bot_name = input(f"{Colors.OKCYAN}Enter bot username: {Colors.ENDC}").strip()
                env_content['TWITCH_BOT_NAME'] = bot_name
                
            if 'TWITCH_CHANNEL' not in env_content:
                channel = input(f"{Colors.OKCYAN}Enter channel name: {Colors.ENDC}").strip()
                env_content['TWITCH_CHANNEL'] = channel
                
            if 'DATABASE_URL' not in env_content:
                env_content['DATABASE_URL'] = "postgresql://trivia:trivia-password@localhost:5432/trivia"
            
            # Write .env file
            with open(self.env_file, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
                    
            print(f"{Colors.OKGREEN}✅ .env file updated{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to update .env: {e}{Colors.ENDC}")
            return False
    
    def setup_database(self) -> bool:
        """Setup database and load questions."""
        try:
            print("Starting database services...")
            
            # Start Docker services
            result = subprocess.run(["docker", "compose", "up", "-d"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"{Colors.FAIL}❌ Failed to start database: {result.stderr}{Colors.ENDC}")
                return False
                
            print(f"{Colors.OKGREEN}✅ Database started{Colors.ENDC}")
            
            # Wait a moment for database to be ready
            print("Waiting for database to initialize...")
            time.sleep(3)
            
            # Run migrations
            print("Running database migrations...")
            result = subprocess.run(["uv", "run", "alembic", "upgrade", "head"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"{Colors.WARNING}⚠️  Migration warning: {result.stderr}{Colors.ENDC}")
                # Continue anyway, migrations might already be applied
            
            # Load questions if needed
            print("Loading trivia questions...")
            result = subprocess.run(["uv", "run", "python", "-m", "scripts.load_questions"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}✅ Questions loaded{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  Question loading completed with warnings{Colors.ENDC}")
                
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}❌ Database setup failed: {e}{Colors.ENDC}")
            return False
    
    def start_bot(self):
        """Start the CherryBott."""
        print(f"\n{Colors.HEADER}🚀 Starting CherryBott...{Colors.ENDC}")
        
        if not self.env_file.exists():
            print(f"{Colors.FAIL}❌ .env file not found. Please run setup first.{Colors.ENDC}")
            return
            
        try:
            # Start the bot
            subprocess.run(["uv", "run", "python", "chat_listener.py"], cwd=self.project_root)
        except KeyboardInterrupt:
            print(f"\n{Colors.OKGREEN}🛑 Bot stopped by user{Colors.ENDC}")
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Bot error: {e}{Colors.ENDC}")
    
    def check_status(self):
        """Check system status."""
        print(f"\n{Colors.HEADER}🔍 System Status{Colors.ENDC}")
        
        # Check .env
        if self.env_file.exists():
            print(f"{Colors.OKGREEN}✅ .env file exists{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ .env file missing{Colors.ENDC}")
            
        # Check database
        try:
            result = subprocess.run(["docker", "compose", "ps"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if "Up" in result.stdout:
                print(f"{Colors.OKGREEN}✅ Database running{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  Database not running{Colors.ENDC}")
        except:
            print(f"{Colors.FAIL}❌ Could not check database status{Colors.ENDC}")
            
        # Check questions
        try:
            result = subprocess.run(["uv", "run", "python", "-m", "scripts.inspect_database"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if "questions" in result.stdout.lower():
                print(f"{Colors.OKGREEN}✅ Questions loaded{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  Questions might not be loaded{Colors.ENDC}")
        except:
            print(f"{Colors.WARNING}⚠️  Could not check questions{Colors.ENDC}")
            
        input("Press Enter to return to menu...")
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False
    
    def _find_chrome_command(self) -> Optional[str]:
        """Find Chrome executable."""
        possible_commands = [
            "google-chrome", "google-chrome-stable", "chromium", 
            "chromium-browser", "/usr/bin/google-chrome"
        ]
        
        # WSL: Try Windows Chrome via cmd.exe
        if self._is_wsl():
            wsl_chrome_commands = [
                "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
                "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
            ]
            for cmd in wsl_chrome_commands:
                if Path(cmd).exists():
                    return cmd
        
        for cmd in possible_commands:
            if self._command_exists(cmd):
                return cmd
        return None


if __name__ == "__main__":
    launcher = CherryBottLauncher()
    launcher.main_menu()