"""Utilities for generating human-readable diffs and user confirmation."""

import difflib
from typing import Optional


# ANSI color codes for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def generate_diff(
    old_content: str,
    new_content: str,
    file_path: str,
    context_lines: int = 3,
) -> str:
    """Generate a human-readable unified diff between old and new content.

    Args:
        old_content: The original file content
        new_content: The new content after changes
        file_path: Path to the file (for display)
        context_lines: Number of context lines around changes

    Returns:
        A formatted diff string with colors
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    # Ensure files end with newline for proper diff display
    if old_lines and not old_lines[-1].endswith('\n'):
        old_lines[-1] += '\n'
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=context_lines,
    )

    return colorize_diff(list(diff))


def colorize_diff(diff_lines: list[str]) -> str:
    """Add ANSI colors to diff output for better readability.

    Args:
        diff_lines: List of diff lines from unified_diff

    Returns:
        Colorized diff string
    """
    colored_lines = []

    for line in diff_lines:
        if line.startswith('---') or line.startswith('+++'):
            # File headers
            colored_lines.append(f"{Colors.BOLD}{Colors.BLUE}{line}{Colors.RESET}")
        elif line.startswith('@@'):
            # Hunk headers
            colored_lines.append(f"{Colors.CYAN}{line}{Colors.RESET}")
        elif line.startswith('-'):
            # Removed lines
            colored_lines.append(f"{Colors.RED}{line}{Colors.RESET}")
        elif line.startswith('+'):
            # Added lines
            colored_lines.append(f"{Colors.GREEN}{line}{Colors.RESET}")
        else:
            # Context lines
            colored_lines.append(line)

    return ''.join(colored_lines)


def generate_new_file_preview(content: str, file_path: str, max_lines: int = 50) -> str:
    """Generate a preview for a new file being created.

    Args:
        content: The content to be written
        file_path: Path to the file (for display)
        max_lines: Maximum number of lines to show

    Returns:
        A formatted preview string
    """
    lines = content.splitlines()
    total_lines = len(lines)

    output = []
    output.append(f"{Colors.BOLD}{Colors.BLUE}Creating new file: {file_path}{Colors.RESET}")
    output.append(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")

    display_lines = lines[:max_lines]
    for i, line in enumerate(display_lines, 1):
        output.append(f"{Colors.GREEN}+ {line}{Colors.RESET}")

    if total_lines > max_lines:
        output.append(f"{Colors.YELLOW}... ({total_lines - max_lines} more lines){Colors.RESET}")

    output.append(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")
    output.append(f"Total: {total_lines} lines")

    return '\n'.join(output)


def ask_user_confirmation(
    diff_output: str,
    action_description: str,
    default: bool = True,
) -> bool:
    """Display a diff and ask the user for confirmation before applying changes.

    Args:
        diff_output: The formatted diff to display
        action_description: Description of what will happen if confirmed
        default: Default response if user just presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    import sys

    print()
    print(f"{Colors.BOLD}{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Proposed changes:{Colors.RESET}")
    print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
    print()
    print(diff_output)
    print()
    print(f"{Colors.YELLOW}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Action:{Colors.RESET} {action_description}")
    print(f"{Colors.YELLOW}{'─' * 60}{Colors.RESET}")

    default_str = "Y/n" if default else "y/N"

    # Flush stdout to ensure the prompt is displayed
    sys.stdout.flush()

    try:
        # Try to read from /dev/tty directly to handle cases where stdin is not a terminal
        try:
            with open('/dev/tty', 'r') as tty:
                print(f"\n{Colors.BOLD}Apply these changes? [{default_str}]: {Colors.RESET}", end='')
                sys.stdout.flush()
                response = tty.readline().strip().lower()
                print(f"{Colors.CYAN}[DEBUG] Got response from /dev/tty: '{response}'{Colors.RESET}")
        except (OSError, IOError) as e:
            print(f"{Colors.CYAN}[DEBUG] /dev/tty not available ({e}), using stdin{Colors.RESET}")
            # Fall back to regular input if /dev/tty is not available
            response = input(f"\n{Colors.BOLD}Apply these changes? [{default_str}]: {Colors.RESET}").strip().lower()
            print(f"{Colors.CYAN}[DEBUG] Got response from stdin: '{response}'{Colors.RESET}")

        if response == '':
            print(f"{Colors.GREEN}Using default: {'yes' if default else 'no'}{Colors.RESET}")
            return default
        elif response in ('y', 'yes'):
            print(f"{Colors.GREEN}User confirmed: applying changes{Colors.RESET}")
            return True
        elif response in ('n', 'no'):
            print(f"{Colors.RED}User declined: rejecting changes{Colors.RESET}")
            return False
        else:
            print(f"{Colors.YELLOW}Invalid response '{response}', using default: {'yes' if default else 'no'}{Colors.RESET}")
            return default

    except (EOFError, KeyboardInterrupt) as e:
        print(f"\n{Colors.RED}Operation cancelled ({type(e).__name__}){Colors.RESET}")
        return False
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error during confirmation: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Rejecting changes for safety{Colors.RESET}")
        return False
