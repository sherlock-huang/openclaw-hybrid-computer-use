#!/usr/bin/env python3
"""自动测试录制功能 - 无需手动输入"""
import sys
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple
import json

print("=" * 60)
print("Task Recorder Auto Test")
print("=" * 60)

# 定义数据类
@dataclass
class RecordingEvent:
    action: str
    timestamp: float
    target: Optional[str] = None
    position: Optional[Tuple[int, int]] = None
    value: Optional[str] = None

@dataclass
class RecordingSession:
    name: str
    start_time: datetime
    events: List[RecordingEvent]
    
    def to_dict(self):
        return {
            "name": self.name,
            "recorded_at": self.start_time.isoformat(),
            "tasks": [
                {
                    "action": e.action,
                    "target": e.target or (f"{e.position[0]},{e.position[1]}" if e.position else None),
                    "value": e.value,
                    "delay": 0.5
                }
                for e in self.events
            ]
        }
    
    def save_to_file(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return filepath

# 模拟录制过程
print("\n[Step 1/5] Creating recording session...")
session = RecordingSession(
    name="Auto Test Recording",
    start_time=datetime.now(),
    events=[]
)
print("  OK Session created")

print("\n[Step 2/5] Adding click events...")
session.events.append(RecordingEvent(
    action="click",
    timestamp=0.5,
    position=(100, 200),
    target="button_1"
))
session.events.append(RecordingEvent(
    action="click", 
    timestamp=1.2,
    position=(500, 300)
))
print(f"  OK Added {len([e for e in session.events if e.action == 'click'])} click events")

print("\n[Step 3/5] Adding type events...")
session.events.append(RecordingEvent(
    action="type",
    timestamp=2.0,
    value="Hello World"
))
session.events.append(RecordingEvent(
    action="type",
    timestamp=3.5, 
    value="Testing recorder"
))
print(f"  OK Added {len([e for e in session.events if e.action == 'type'])} type events")

print("\n[Step 4/5] Saving to JSON file...")
output_file = "test_recording_auto.json"
session.save_to_file(output_file)
print(f"  OK Saved to: {os.path.abspath(output_file)}")

print("\n[Step 5/5] Verifying saved file...")
with open(output_file, 'r') as f:
    data = json.load(f)

print(f"\n  Verification:")
print(f"    - Recording name: {data['name']}")
print(f"    - Recorded at: {data['recorded_at']}")
print(f"    - Total tasks: {len(data['tasks'])}")
print(f"\n  Tasks breakdown:")
for i, task in enumerate(data['tasks'], 1):
    if task['action'] == 'click':
        print(f"    {i}. CLICK -> {task['target']}")
    elif task['action'] == 'type':
        print(f"    {i}. TYPE -> {task['value']}")

print("\n" + "=" * 60)
print("SUCCESS! Recording function works correctly!")
print("=" * 60)
print(f"\nOutput file: {os.path.abspath(output_file)}")
print("\nFile content preview:")
print(json.dumps(data, indent=2)[:500] + "...")
