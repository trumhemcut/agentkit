#!/usr/bin/env python3
"""
Manual test script for bar chart generation with loop agent

Run this to see if bar charts work:
    python3 test_bar_chart_manual.py
"""
import sys
import os
import asyncio
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.a2ui_agent_with_loop import A2UIAgentWithLoop
from protocols.a2ui_encoder import is_a2ui_message


async def test_bar_chart():
    """Test bar chart creation with loop agent"""
    print("=" * 60)
    print("Testing Bar Chart Generation with Loop Agent")
    print("=" * 60)
    
    agent = A2UIAgentWithLoop(provider="ollama", model="qwen2.5:7b", max_iterations=3)
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Create a bar chart showing Q1 and Q2 sales. Q1 revenue: 50000, profit: 15000. Q2 revenue: 60000, profit: 18000."
            }
        ],
        "thread_id": "manual-test",
        "run_id": "run-manual"
    }
    
    print("\n📊 Request: Create bar chart for Q1/Q2 sales")
    print("-" * 60)
    
    try:
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        print(f"\n✓ Generated {len(events)} total events")
        
        # Filter A2UI events
        a2ui_events = [e for e in events if is_a2ui_message(e)]
        print(f"✓ Generated {len(a2ui_events)} A2UI events")
        
        # Analyze surface update
        surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
        if surface_updates:
            print(f"\n📦 Surface Update:")
            components = surface_updates[0].get("components", [])
            print(f"   Total components: {len(components)}")
            
            for comp in components:
                comp_type = list(comp.get("component", {}).keys())[0] if comp.get("component") else "Unknown"
                comp_id = comp.get("id", "?")
                print(f"   - {comp_type} (id: {comp_id})")
                
                if comp_type == "BarChart":
                    bar_chart = comp["component"]["BarChart"]
                    print(f"     Title: {bar_chart.get('title', {}).get('literalString', 'N/A')}")
                    print(f"     Data Path: {bar_chart.get('data', {}).get('path', 'N/A')}")
                    print(f"     Data Keys: {bar_chart.get('dataKeys', {}).get('literalString', 'N/A')}")
        
        # Analyze data model updates
        data_updates = [e for e in a2ui_events if e.get("type") == "dataModelUpdate"]
        print(f"\n💾 Data Model Updates: {len(data_updates)}")
        for i, du in enumerate(data_updates, 1):
            path = du.get("path", "?")
            contents = du.get("contents", [])
            print(f"   {i}. Path: {path}")
            print(f"      Contents: {len(contents)} item(s)")
            for content in contents:
                key = content.get("key", "?")
                has_data = "value_map" in content
                print(f"      - {key}: {'✓ Has data' if has_data else '✗ No data'}")
        
        # Check for bar chart component
        bar_chart_components = [
            c for c in components 
            if "BarChart" in c.get("component", {})
        ]
        
        if bar_chart_components:
            print("\n✅ SUCCESS: Bar chart component created!")
            
            # Verify data model paths match
            bar_chart = bar_chart_components[0]["component"]["BarChart"]
            chart_data_path = bar_chart.get("data", {}).get("path", "")
            expected_parent = '/'.join(chart_data_path.split('/')[:-1])
            
            matching_updates = [
                du for du in data_updates 
                if du.get("path") == expected_parent
            ]
            
            if matching_updates:
                print(f"✅ Data model path matches: {expected_parent}")
            else:
                print(f"⚠️  WARNING: No data update for path {expected_parent}")
                print(f"   Available paths: {[du.get('path') for du in data_updates]}")
        else:
            print("\n❌ FAIL: No bar chart component found!")
            print(f"   Component types: {[list(c.get('component', {}).keys())[0] for c in components if c.get('component')]}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_bar_chart_with_button():
    """Test bar chart + button creation"""
    print("\n" + "=" * 60)
    print("Testing Bar Chart + Button")
    print("=" * 60)
    
    agent = A2UIAgentWithLoop(provider="ollama", model="qwen2.5:7b", max_iterations=5)
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Create a bar chart for monthly sales (Jan: 100, Feb: 150, Mar: 200) and add a submit button."
            }
        ],
        "thread_id": "manual-test-2",
        "run_id": "run-manual-2"
    }
    
    print("\n📊 Request: Bar chart + button")
    print("-" * 60)
    
    try:
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        a2ui_events = [e for e in events if is_a2ui_message(e)]
        surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
        
        if surface_updates:
            components = surface_updates[0].get("components", [])
            
            has_bar_chart = any("BarChart" in c.get("component", {}) for c in components)
            has_button = any("Button" in c.get("component", {}) for c in components)
            has_column = any("Column" in c.get("component", {}) for c in components)
            
            print(f"\n📦 Components created:")
            print(f"   - Bar Chart: {'✓' if has_bar_chart else '✗'}")
            print(f"   - Button: {'✓' if has_button else '✗'}")
            print(f"   - Column Container: {'✓' if has_column else '✗'}")
            
            if has_bar_chart and has_button and has_column:
                print("\n✅ SUCCESS: Multi-component UI created correctly!")
                return True
            else:
                print("\n⚠️  WARNING: Some components missing")
                return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


async def main():
    """Run all manual tests"""
    print("\n🚀 Starting Manual Bar Chart Tests\n")
    
    result1 = await test_bar_chart()
    result2 = await test_bar_chart_with_button()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    print(f"Single bar chart: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Bar chart + button: {'✅ PASS' if result2 else '❌ FAIL'}")
    print()
    
    if result1 and result2:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
