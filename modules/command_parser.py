import re
from typing import List, Dict, Any

class CommandParser:
    def __init__(self):
        """Initialize the command parser with predefined patterns"""
        # Define command patterns
        self.patterns = {
            # Basic UI interactions with coordinates support
            r'click (?:on )?(.+?)(?:\s|$)': {'action': 'click', 'target': 'group1'},
            r'double.?click (?:on )?(.+?)(?:\s|$)': {'action': 'double_click', 'target': 'group1'},
            r'right.?click (?:on )?(.+?)(?:\s|$)': {'action': 'right_click', 'target': 'group1'},
            
            # Coordinate-specific patterns
            r'click (?:at )?(?:\[)?(\d+)\s*,\s*(\d+)(?:\])?': {'action': 'click', 'x': 'group1', 'y': 'group2'},
            r'double.?click (?:at )?(?:\[)?(\d+)\s*,\s*(\d+)(?:\])?': {'action': 'double_click', 'x': 'group1', 'y': 'group2'},
            r'right.?click (?:at )?(?:\[)?(\d+)\s*,\s*(\d+)(?:\])?': {'action': 'right_click', 'x': 'group1', 'y': 'group2'},
            r'move (?:to )?(?:\[)?(\d+)\s*,\s*(\d+)(?:\])?': {'action': 'move', 'x': 'group1', 'y': 'group2'},
            
            # Text entry
            r'type "([^"]+)"': {'action': 'type', 'text': 'group1'},
            r'type \'([^\']+)\'': {'action': 'type', 'text': 'group1'},
            r'enter "([^"]+)"': {'action': 'type', 'text': 'group1'},
            r'enter \'([^\']+)\'': {'action': 'type', 'text': 'group1'},
            r'input "([^"]+)"': {'action': 'type', 'text': 'group1'},
            r'input \'([^\']+)\'': {'action': 'type', 'text': 'group1'},
            
            # Key actions
            r'press ([a-zA-Z0-9_+^]+)': {'action': 'key_press', 'text': 'group1'},
            r'key ([a-zA-Z0-9_+^]+)': {'action': 'key_press', 'text': 'group1'},
            r'hotkey ([a-zA-Z0-9_+^]+(?:\+[a-zA-Z0-9_+^]+)+)': {'action': 'hotkey', 'text': 'group1'},
            r'shortcut ([a-zA-Z0-9_+^]+(?:\+[a-zA-Z0-9_+^]+)+)': {'action': 'hotkey', 'text': 'group1'},
            
            # Navigation
            r'scroll (up|down)(?: (\d+))?': {'action': 'scroll', 'direction': 'group1', 'amount': 'group2'},
            r'drag from (.+?) to (.+)': {'action': 'drag', 'start': 'group1', 'end': 'group2'},
            r'move (to|mouse) (.+?)(?:\s|$)': {'action': 'move', 'target': 'group2'},
            
            # Waiting and timing
            r'wait (\d+\.?\d*)(?:\s?s(?:ec(?:ond)?s?)?)?': {'action': 'wait', 'duration': 'group1'},
            r'pause (\d+\.?\d*)(?:\s?s(?:ec(?:ond)?s?)?)?': {'action': 'wait', 'duration': 'group1'},
            r'sleep (\d+\.?\d*)(?:\s?s(?:ec(?:ond)?s?)?)?': {'action': 'wait', 'duration': 'group1'},
            
            # Application control
            r'open (.+)': {'action': 'open', 'target': 'group1'},
            r'close (.+)': {'action': 'close', 'target': 'group1'},
            r'maximize (.+)': {'action': 'maximize', 'target': 'group1'},
            r'minimize (.+)': {'action': 'minimize', 'target': 'group1'},
            
            # Screenshot and OCR
            r'screenshot(?: of)? (.+?)(?:\s|$)': {'action': 'screenshot', 'target': 'group1'},
            r'capture(?: of)? (.+?)(?:\s|$)': {'action': 'screenshot', 'target': 'group1'},
            r'read text(?: from)? (.+?)(?:\s|$)': {'action': 'read_text', 'target': 'group1'},
            r'ocr(?: on)? (.+?)(?:\s|$)': {'action': 'read_text', 'target': 'group1'},
            
            # Gemini format patterns with colons
            r'click:\s*(.+?)(?:\s|$)': {'action': 'click', 'target': 'group1'},
            r'double.?click:\s*(.+?)(?:\s|$)': {'action': 'double_click', 'target': 'group1'},
            r'right.?click:\s*(.+?)(?:\s|$)': {'action': 'right_click', 'target': 'group1'},
            r'type:\s*(.+?)(?:\s|$)': {'action': 'type', 'text': 'group1'},
            r'press:\s*(.+?)(?:\s|$)': {'action': 'key_press', 'text': 'group1'},
            r'wait:\s*(\d+\.?\d*)': {'action': 'wait', 'duration': 'group1'},
            r'scroll:\s*(up|down)(?: (\d+))?': {'action': 'scroll', 'direction': 'group1', 'amount': 'group2'},
        }
        
        # Patterns for composite commands
        self.composite_patterns = [
            r'first (.+?) then (.+)',
            r'(.+?) and then (.+)',
            r'(.+?) followed by (.+)',
            r'(.+?),? then (.+)',
        ]
    
    def parse_natural_language_command(self, command: str) -> List[Dict[str, Any]]:
        """Parse natural language commands into actionable instructions"""
        actions = []
        command = command.lower().strip()
        
        # Pre-process command to remove markdown and other formatting
        command = command.replace('**', '').replace('`', '')
        
        # First, check for Gemini-style commands with colons
        if ':' in command:
            # Parse Gemini format: action: value
            parts = command.split(':', 1)
            if len(parts) == 2:
                action_type = parts[0].strip()
                value = parts[1].strip()
                
                # Map action types to internal actions
                if action_type == 'click':
                    # Check if value is coordinates
                    coord_match = re.search(r'\[(\d+),\s*(\d+)\]', value)
                    if coord_match:
                        x, y = int(coord_match.group(1)), int(coord_match.group(2))
                        return [{'action': 'click', 'target': (x, y)}]
                    else:
                        return [{'action': 'click', 'target': value}]
                elif action_type == 'double_click' or action_type == 'doubleclick':
                    return [{'action': 'double_click', 'target': value}]
                elif action_type == 'right_click' or action_type == 'rightclick':
                    return [{'action': 'right_click', 'target': value}]
                elif action_type == 'type':
                    return [{'action': 'type', 'text': value}]
                elif action_type == 'press':
                    return [{'action': 'key_press', 'text': value}]
                elif action_type == 'wait':
                    try:
                        duration = float(value)
                        return [{'action': 'wait', 'duration': str(duration)}]
                    except ValueError:
                        return [{'action': 'wait', 'duration': '1.0'}]
                elif action_type == 'scroll':
                    direction = 'down'
                    amount = 3
                    if 'up' in value:
                        direction = 'up'
                    
                    # Try to extract amount
                    amount_match = re.search(r'(\d+)', value)
                    if amount_match:
                        amount = int(amount_match.group(1))
                    
                    return [{'action': 'scroll', 'clicks': str(amount if direction == 'up' else -amount)}]
        
        # If not a Gemini format or parsing failed, try regular patterns
        # First check for direct commands that we know will work
        if command.startswith('hotkey win+r'):
            return [{'action': 'hotkey', 'text': 'win+r'}]
        elif command.startswith('type '):
            text = command[5:].strip()
            return [{'action': 'type', 'text': text}]
        elif command.startswith('press '):
            key = command[6:].strip()
            return [{'action': 'key_press', 'text': key}]
        elif command.startswith('wait '):
            # Extract duration
            match = re.search(r'wait\s+(\d+\.?\d*)', command)
            if match:
                duration = match.group(1)
                return [{'action': 'wait', 'duration': duration}]
        elif command.startswith('click at '):
            # Extract coordinates
            match = re.search(r'click at (\d+),\s*(\d+)', command)
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                return [{'action': 'click', 'target': (x, y)}]
        elif command.startswith('move to '):
            # Extract coordinates
            match = re.search(r'move to (\d+),\s*(\d+)', command)
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                return [{'action': 'move', 'target': (x, y)}]
        
        # Check for command patterns
        for pattern, action_info in self.patterns.items():
            match = re.search(pattern, command)
            if match:
                action = action_info.copy()
                
                # Replace group references with actual matched text
                for key, value in list(action.items()):
                    if isinstance(value, str) and value.startswith('group'):
                        group_num = int(value.replace('group', ''))
                        try:
                            if group_num <= len(match.groups()) and match.group(group_num) is not None:
                                action[key] = match.group(group_num)
                            else:
                                # Remove the key if the group wasn't matched
                                del action[key]
                        except IndexError:
                            # Group doesn't exist in the match, remove it from action
                            del action[key]
                
                # Handle special cases
                if action.get('action') == 'scroll':
                    direction = action.get('direction', 'down')
                    amount = action.get('amount')
                    if amount:
                        try:
                            amount = int(amount)
                        except ValueError:
                            amount = 3
                    else:
                        amount = 3
                    
                    # Store as string to avoid linter errors
                    action['clicks'] = str(amount if direction == 'up' else -amount)
                    # Clean up temporary keys
                    if 'direction' in action:
                        del action['direction']
                    if 'amount' in action:
                        del action['amount']
                
                # Handle wait durations to convert to float
                if action.get('action') == 'wait' and 'duration' in action:
                    try:
                        # Store as string to avoid linter errors
                        action['duration'] = str(float(action['duration']))
                    except ValueError:
                        action['duration'] = '1.0'
                
                # Handle coordinate-based actions
                if 'x' in action and 'y' in action:
                    try:
                        x = int(action['x'])
                        y = int(action['y'])
                        # Create a tuple for target
                        action['target'] = (x, y)
                        # Clean up temporary keys
                        del action['x']
                        del action['y']
                    except (ValueError, TypeError):
                        # If conversion fails, keep as is
                        pass
                
                # Handle new action types
                if action.get('action') == 'open':
                    # Convert to a sequence of actions for opening applications
                    action = {'action': 'hotkey', 'text': 'win+r', 'follow_up': 'type', 'follow_text': action.get('target', '')}
                
                actions.append(action)
                
                # Check for follow-up actions
                if 'follow_up' in action:
                    follow_action = {'action': action.get('follow_up')}
                    if 'follow_text' in action:
                        follow_action['text'] = action.get('follow_text')
                    actions.append(follow_action)
                    
                    # For application opening, add an Enter press
                    if action.get('action') == 'hotkey' and action.get('text') == 'win+r':
                        actions.append({'action': 'key_press', 'text': 'enter'})
                break
        
        # If no pattern matched, try direct command parsing for common actions
        if not actions:
            # Direct command parsing for common actions
            if command.startswith('hotkey '):
                key_combo = command[7:].strip()
                actions.append({'action': 'hotkey', 'text': key_combo})
            elif command.startswith('type '):
                # Try to extract quoted text
                match = re.search(r'type\s+"([^"]+)"', command) or re.search(r"type\s+'([^']+)'", command)
                if match:
                    text = match.group(1)
                    actions.append({'action': 'type', 'text': text})
                else:
                    # Take everything after "type "
                    text = command[5:].strip()
                    actions.append({'action': 'type', 'text': text})
            elif command.startswith('press '):
                key = command[6:].strip()
                actions.append({'action': 'key_press', 'text': key})
            elif command.startswith('wait '):
                # Try to extract duration
                match = re.search(r'wait\s+(\d+\.?\d*)', command)
                if match:
                    duration = match.group(1)
                    actions.append({'action': 'wait', 'duration': duration})
                else:
                    actions.append({'action': 'wait', 'duration': '1.0'})
        
        # If still no actions, check for composite commands
        if not actions:
            # Check for composite commands (multiple actions in one command)
            for pattern in self.composite_patterns:
                match = re.search(pattern, command)
                if match:
                    first_command = match.group(1)
                    second_command = match.group(2)
                    
                    # Recursively parse each part
                    first_actions = self.parse_natural_language_command(first_command)
                    second_actions = self.parse_natural_language_command(second_command)
                    
                    actions = first_actions + second_actions
                    break
        
        return actions 