#!/usr/bin/env python3
"""
LIA CLI - Command Line Interface for Local Intelligent Agent
Use LIA from the terminal!
"""

import asyncio
import sys
import argparse
from pathlib import Path
from ollama_service import OllamaService
from command_executor import CommandExecutor
from models import CommandIntent
import json


class LIACLI:
    """CLI Interface for LIA"""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        self.command_executor = CommandExecutor()
        self.colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'blue': '\033[94m',
            'yellow': '\033[93m',
            'cyan': '\033[96m',
            'reset': '\033[0m',
            'bold': '\033[1m',
        }
    
    def print_colored(self, text, color='reset'):
        """Print colored text"""
        print(f"{self.colors.get(color, '')}{text}{self.colors['reset']}")
    
    def print_banner(self):
        """Print LIA banner"""
        banner = """
╔══════════════════════════════════════════════════════════╗
║                  LIA - Local Intelligent Agent          ║
║                     Command Line Interface              ║
╚══════════════════════════════════════════════════════════╝
"""
        self.print_colored(banner, 'cyan')
    
    async def execute_command(self, message, verbose=False):
        """Execute a single command"""
        try:
            # Parse intent
            if verbose:
                self.print_colored(f"\n🤖 Processing: {message}", 'blue')
            
            intent = await self.ollama_service.parse_user_intent(message)
            
            if verbose:
                self.print_colored(f"📋 Command Type: {intent.command_type}", 'yellow')
                self.print_colored(f"⚙️  Parameters: {intent.parameters}", 'yellow')
            
            # Execute
            result = await self.command_executor.execute(intent)
            
            # Display result
            if result.success:
                self.print_colored(f"\n✅ {result.message}", 'green')
            else:
                self.print_colored(f"\n❌ {result.message}", 'red')
            
            # Display data if available
            if result.data and verbose:
                self.print_colored("\n📊 Result Data:", 'cyan')
                print(json.dumps(result.data, indent=2))
            elif result.data:
                # Show condensed data
                if "files" in result.data:
                    files = result.data["files"]
                    self.print_colored(f"\n   Found {len(files)} file(s):", 'cyan')
                    for f in files[:10]:  # Show first 10
                        size_kb = f['size'] / 1024
                        print(f"   • {f['name']} ({size_kb:.1f} KB)")
                    if len(files) > 10:
                        self.print_colored(f"   ... and {len(files) - 10} more", 'yellow')
                elif "stdout" in result.data:
                    self.print_colored("\n   Command Output:", 'cyan')
                    print(result.data["stdout"])
                elif "content" in result.data:
                    self.print_colored("\n   Content:", 'cyan')
                    content = result.data["content"]
                    if len(content) > 200:
                        print(content[:200] + "...")
                    else:
                        print(content)
            
            return result.success
            
        except Exception as e:
            self.print_colored(f"\n❌ Error: {str(e)}", 'red')
            return False
    
    async def interactive_mode(self):
        """Run LIA in interactive mode"""
        self.print_banner()
        self.print_colored("Type your commands or 'help' for examples. Press Ctrl+C to exit.\n", 'yellow')
        
        while True:
            try:
                # Get user input
                self.print_colored("LIA> ", 'bold', end='')
                message = input().strip()
                
                if not message:
                    continue
                
                # Handle special commands
                if message.lower() in ['exit', 'quit', 'q']:
                    self.print_colored("\n👋 Goodbye!", 'cyan')
                    break
                
                if message.lower() == 'help':
                    self.show_help()
                    continue
                
                if message.lower() == 'clear':
                    print("\033[2J\033[H")  # Clear screen
                    self.print_banner()
                    continue
                
                # Execute command
                await self.execute_command(message, verbose=False)
                
            except KeyboardInterrupt:
                self.print_colored("\n\n👋 Goodbye!", 'cyan')
                break
            except EOFError:
                break
            except Exception as e:
                self.print_colored(f"\n❌ Error: {str(e)}", 'red')
    
    def show_help(self):
        """Show help information"""
        help_text = """
╔══════════════════════════════════════════════════════════╗
║                     LIA Command Examples                 ║
╚══════════════════════════════════════════════════════════╝

📁 File Operations:
   • "Open the Pictures folder"
   • "Open image.jpg"
   • "List all PDF files in Downloads"
   • "Create a file named notes.txt"
   • "Delete old.txt"
   
📋 File Management:
   • "Copy file.txt to backup.txt"
   • "Move document.pdf to Documents"
   • "Rename old.txt to new.txt"
   • "Get info about file.txt"

🔍 Search & Info:
   • "Search for Python files"
   • "Show me my system information"
   • "List all images in Pictures"

⚡ Shell Commands (safe list):
   • "Run ls"
   • "Run pwd"
   • "Run date"

💡 Special Commands:
   • help    - Show this help
   • clear   - Clear screen
   • exit    - Exit LIA CLI

Type any natural language command and LIA will understand it!
"""
        self.print_colored(help_text, 'cyan')


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LIA CLI - Local Intelligent Agent Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  lia "Open the Pictures folder"
  lia "List all PDF files in Downloads"
  lia --interactive
  lia -v "Create a file named test.txt"
        '''
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        help='Command to execute (use quotes for multi-word commands)'
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (show detailed information)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    cli = LIACLI()
    
    # Interactive mode
    if args.interactive or not args.command:
        await cli.interactive_mode()
    else:
        # Single command mode
        if not sys.stdout.isatty():
            # Running in pipe/non-interactive, no colors
            cli.colors = {k: '' for k in cli.colors}
        
        success = await cli.execute_command(args.command, verbose=args.verbose)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)

