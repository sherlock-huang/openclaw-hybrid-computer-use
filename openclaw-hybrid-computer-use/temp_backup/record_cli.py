#!/usr/bin/env python3
"""CLI-based recording (no global hotkey needed)"""
import sys
import os
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple
import json


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


class SimpleRecorder:
    def __init__(self):
        self.is_recording = False
        self.events = []
        self.start_time = None
        self.name = None
        self._start_timestamp = None
    
    def start_recording(self, name=None):
        if self.is_recording:
            raise RuntimeError("Already recording")
        
        self.is_recording = True
        self.name = name or f"Recording {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.start_time = datetime.now()
        self._start_timestamp = time.time()
        self.events = []
        
        print(f"\n[START] Recording: {self.name}")
    
    def add_click(self, x, y, target=None):
        if not self.is_recording:
            return
        
        event = RecordingEvent(
            action="click",
            timestamp=time.time() - self._start_timestamp,
            target=target,
            position=(x, y)
        )
        self.events.append(event)
        print(f"  [CLICK] ({x}, {y}){' -> ' + target if target else ''}")
    
    def add_type(self, text):
        if not self.is_recording:
            return
        
        event = RecordingEvent(
            action="type",
            timestamp=time.time() - self._start_timestamp,
            value=text
        )
        self.events.append(event)
        display = text[:30] + '...' if len(text) > 30 else text
        print(f"  [TYPE] {display}")
    
    def stop_recording(self):
        if not self.is_recording:
            raise RuntimeError("Not recording")
        
        self.is_recording = False
        
        session = RecordingSession(
            name=self.name,
            start_time=self.start_time,
            events=self.events.copy()
        )
        
        print(f"\n[STOP] Recorded {len(self.events)} events")
        return session


def main():
    print("=" * 60)
    print("Task Recorder (CLI Mode)")
    print("=" * 60)
    print("\nCommands:")
    print("  s              = start recording")
    print("  c <x> <y>      = record click at (x, y)")
    print("  t <text>       = record text input")
    print("  x              = stop and save to JSON")
    print("  q              = quit")
    print("=" * 60)
    
    recorder = SimpleRecorder()
    
    while True:
        try:
            cmd = input("\n> ").strip()
            
            if cmd == 's':
                if recorder.is_recording:
                    print("Already recording!")
                else:
                    recorder.start_recording()
                    
            elif cmd.startswith('c '):
                if not recorder.is_recording:
                    print("Start recording first (use 's')")
                    continue
                parts = cmd.split()
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    recorder.add_click(x, y)
                except (IndexError, ValueError):
                    print("Usage: c <x> <y>")
                    
            elif cmd.startswith('t '):
                if not recorder.is_recording:
                    print("Start recording first (use 's')")
                    continue
                text = cmd[2:]
                recorder.add_type(text)
                    
            elif cmd == 'x':
                if not recorder.is_recording:
                    print("Not recording!")
                else:
                    session = recorder.stop_recording()
                    filename = f"recorded_{datetime.now():%Y%m%d_%H%M%S}.json"
                    session.save_to_file(filename)
                    print(f"\n[SAVED] {filename}")
                    print("\nContent:")
                    with open(filename, 'r') as f:
                        print(f.read())
                    
            elif cmd == 'q':
                if recorder.is_recording:
                    print("Stop recording first (use 'x')")
                else:
                    print("Goodbye!")
                    break
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            print("\nUse 'q' to quit")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
