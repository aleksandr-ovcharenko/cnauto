import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


def get_log_files() -> List[str]:
    """Return a list of available log files"""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_files = []

    if log_dir.exists():
        log_files = [f.name for f in log_dir.glob('app_*.log') if f.is_file()]
        # Sort by date (newest first)
        log_files.sort(reverse=True)

    return log_files


def parse_log_line(line: str) -> Optional[Dict]:
    """Parse a log line into its components"""
    # Match log format: timestamp - module - level - message
    # Updated pattern to better handle various logging formats
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - ([A-Z]+) - (.+)$'
    match = re.match(pattern, line)

    if match:
        timestamp, module, level, message = match.groups()
        return {
            'timestamp': timestamp,
            'module': module.strip(),
            'level': level.strip(),
            'message': message.strip()
        }

    # Try alternate patterns - sometimes logs have different formats
    # This format is often used by Flask and other libraries: LEVEL [Module] Message
    alt_pattern = r'^([A-Z]+)\s+\[([^\]]+)\]\s+(.+)$'
    alt_match = re.match(alt_pattern, line)
    if alt_match:
        level, module, message = alt_match.groups()
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],  # Use current time as timestamp
            'module': module.strip(),
            'level': level.strip(),
            'message': message.strip()
        }

    return None


def get_log_content(log_file: str, max_lines: int = 1000) -> List[Dict]:
    """Read log file and return structured content"""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_path = log_dir / log_file

    if not log_path.exists():
        return []

    log_lines = []
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            # Read from the end to get the most recent logs first
            lines = f.readlines()
            # Limit the number of lines to avoid performance issues
            lines = lines[-max_lines:] if len(lines) > max_lines else lines

            for line in lines:
                parsed = parse_log_line(line.strip())
                if parsed:
                    log_lines.append(parsed)
                elif line.strip() and log_lines:  # Add continuation lines to previous message
                    log_lines[-1]['message'] += f"\n{line.strip()}"
    except Exception as e:
        # Add an error entry if we can't read the log file
        log_lines.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],
            'module': 'log_viewer',
            'level': 'ERROR',
            'message': f"Failed to read log file: {str(e)}"
        })

    return log_lines
