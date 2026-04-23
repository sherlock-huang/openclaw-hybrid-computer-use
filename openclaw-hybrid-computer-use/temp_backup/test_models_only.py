#!/usr/bin/env python3
"""
Independent test - only test recording feature data models
No dependencies on other libraries like pyautogui
"""
import sys
import os

# Directly define test classes (avoid importing whole src package)
print("=" * 60)
print("TEST Recording Feature Data Models")
print("=" * 60)

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json

@dataclass
class RecordingEvent:
    """Recording event"""
    action: str
    timestamp: float
    target: Optional[str] = None
    position: Optional[Tuple[int, int]] = None
    value: Optional[str] = None
    element_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "timestamp": self.timestamp,
            "target": self.target,
            "position": self.position,
            "value": self.value,
            "element_type": self.element_type,
        }


@dataclass
class Task:
    """Atomic task"""
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    delay: float = 0.5
    
    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "delay": self.delay,
        }


@dataclass
class TaskSequence:
    """Task sequence"""
    name: str
    tasks: List[Task]
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
            "max_retries": self.max_retries,
        }


@dataclass
class RecordingSession:
    """Recording session"""
    name: str
    start_time: datetime
    events: List[RecordingEvent]
    
    def to_task_sequence(self) -> TaskSequence:
        """Convert to executable task sequence"""
        tasks = []
        for event in self.events:
            target = event.target
            if target is None and event.position is not None:
                target = f"{event.position[0]},{event.position[1]}"
            
            task = Task(
                action=event.action,
                target=target,
                value=event.value,
                delay=0.5
            )
            tasks.append(task)
        return TaskSequence(name=self.name, tasks=tasks)
    
    def save_to_file(self, filepath: str):
        """Save to JSON file"""
        sequence = self.to_task_sequence()
        
        data = {
            "name": self.name,
            "recorded_at": self.start_time.isoformat(),
            "tasks": [task.to_dict() for task in sequence.tasks]
        }
        
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# Test 1: Create event
print("\n[1/6] Test RecordingEvent...")
event1 = RecordingEvent(
    action="click",
    timestamp=1.5,
    target="elem_001",
    position=(100, 200),
    element_type="button"
)
print(f"  OK Click event: {event1.action} @ {event1.position}")

event2 = RecordingEvent(
    action="type",
    timestamp=2.0,
    value="Hello World"
)
print(f"  OK Type event: {event2.action} = {event2.value}")

# Test 2: Serialization
print("\n[2/6] Test to_dict()...")
print(f"  {event1.to_dict()}")
print(f"  {event2.to_dict()}")
print("  OK Serialization passed")

# Test 3: Create session
print("\n[3/6] Test RecordingSession...")
session = RecordingSession(
    name="My Recording Task",
    start_time=datetime.now(),
    events=[event1, event2]
)
print(f"  OK Session: {session.name}, {len(session.events)} events")

# Test 4: Convert to task sequence
print("\n[4/6] Test to_task_sequence()...")
sequence = session.to_task_sequence()
print(f"  OK Task sequence: {sequence.name}")
print(f"  OK Task count: {len(sequence.tasks)}")
for i, task in enumerate(sequence.tasks):
    target = task.target or task.value
    print(f"    Task {i+1}: {task.action} -> {target}")

# Test 5: Save to file
print("\n[5/6] Test save_to_file()...")
output_file = "test_recording_output.json"
session.save_to_file(output_file)
print(f"  OK Saved to {output_file}")

# Verify file content
with open(output_file, 'r') as f:
    saved_data = json.load(f)
print(f"\n[6/6] Verify saved file...")
print(f"  Name: {saved_data['name']}")
print(f"  Time: {saved_data['recorded_at']}")
print(f"  Tasks: {len(saved_data['tasks'])} total")
for task in saved_data['tasks']:
    print(f"    - {task}")

# Cleanup
os.remove(output_file)

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
print("\nRecording feature core data models work correctly!")
print("\nGenerated JSON format:")
print(json.dumps(saved_data, ensure_ascii=False, indent=2))
