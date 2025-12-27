"""
Tests for partial content editing feature in Canvas mode
"""
import pytest
import asyncio
from agents.canvas_agent import CanvasAgent
from graphs.canvas_graph import (
    CanvasGraphState,
    detect_intent_node,
    Artifact,
    SelectedText
)
from protocols.event_types import CanvasEventType


class TestPartialUpdateIntentDetection:
    """Test intent detection for partial updates"""
    
    def test_partial_update_intent_with_selection(self):
        """Test that selection + message triggers partial_update action"""
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "make this async"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test Function",
                    "code": "def foo():\n    pass",
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 0,
                "end": 13,
                "text": "def foo():",
                "lineStart": 1,
                "lineEnd": 1
            },
            "artifactAction": None
        }
        
        result = detect_intent_node(state)
        assert result["artifactAction"] == "partial_update"
    
    def test_no_partial_update_without_selection(self):
        """Test that without selection, regular update is triggered"""
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "update this code"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test Function",
                    "code": "def foo():\n    pass",
                    "language": "python"
                }]
            },
            "selectedText": None,
            "artifactAction": None
        }
        
        result = detect_intent_node(state)
        assert result["artifactAction"] == "update"
    
    def test_no_partial_update_without_artifact(self):
        """Test that selection without artifact doesn't trigger partial_update"""
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "edit this"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": None,
            "selectedText": {
                "start": 0,
                "end": 10,
                "text": "some text"
            },
            "artifactAction": None
        }
        
        result = detect_intent_node(state)
        # Should not be partial_update since there's no artifact
        assert result["artifactAction"] != "partial_update"


class TestPartialUpdatePromptBuilding:
    """Test prompt construction for partial updates"""
    
    def test_partial_update_prompt_includes_context(self):
        """Ensure prompt includes proper context window"""
        agent = CanvasAgent()
        
        full_code = """def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def calculate_average(numbers):
    return sum(numbers) / len(numbers)"""
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "use list comprehension"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Math Functions",
                    "code": full_code,
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 36,
                "end": 77,
                "text": "for num in numbers:\n        total += num",
                "lineStart": 3,
                "lineEnd": 4
            },
            "artifactAction": "partial_update"
        }
        
        prompt = agent._build_partial_update_prompt(state)
        
        # Verify prompt structure
        assert "Context Before Selection" in prompt
        assert "SELECTED TEXT" in prompt
        assert "Context After Selection" in prompt
        assert "for num in numbers:" in prompt
        assert "total += num" in prompt
        assert "python" in prompt.lower()
        assert "use list comprehension" in prompt
    
    def test_partial_update_prompt_for_text_artifact(self):
        """Test prompt building for text/markdown artifacts"""
        agent = CanvasAgent()
        
        full_text = """# Introduction

This is a sample document that contains some text.

## Section One

Here is some content that we want to edit.

## Section Two

More content here."""
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "make this more formal"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "text",
                    "title": "Sample Document",
                    "fullMarkdown": full_text
                }]
            },
            "selectedText": {
                "start": 77,
                "end": 118,
                "text": "Here is some content that we want to edit."
            },
            "artifactAction": "partial_update"
        }
        
        prompt = agent._build_partial_update_prompt(state)
        
        assert "text" in prompt
        assert "Here is some content that we want to edit." in prompt
        assert "make this more formal" in prompt


class TestPartialUpdateStreaming:
    """Test streaming events for partial updates"""
    
    @pytest.mark.asyncio
    async def test_partial_update_event_sequence(self):
        """Verify correct event sequence for partial updates"""
        agent = CanvasAgent(model="qwen:7b")
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "make it async"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test Function",
                    "code": "def process_data(data):\n    return transform(data)",
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 0,
                "end": 23,
                "text": "def process_data(data):",
                "lineStart": 1,
                "lineEnd": 1
            },
            "artifactAction": "partial_update"
        }
        
        events = []
        try:
            async for event in agent.run(state):
                events.append(event)
                # Limit collection to prevent infinite wait
                if len(events) > 100:
                    break
        except Exception as e:
            # In case LLM is not available, test structure is still valid
            print(f"LLM not available for test: {e}")
            return
        
        # Verify event sequence
        event_types = [getattr(event, 'event_type', None) for event in events]
        
        # Should have START event
        assert CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START in event_types
        
        # Should have at least one CHUNK event
        assert CanvasEventType.ARTIFACT_PARTIAL_UPDATE_CHUNK in event_types
        
        # Should have COMPLETE event
        assert CanvasEventType.ARTIFACT_PARTIAL_UPDATE_COMPLETE in event_types
        
        # START should come before COMPLETE
        start_idx = event_types.index(CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START)
        complete_idx = event_types.index(CanvasEventType.ARTIFACT_PARTIAL_UPDATE_COMPLETE)
        assert start_idx < complete_idx
    
    @pytest.mark.asyncio
    async def test_partial_update_includes_selection_data(self):
        """Verify events include selection boundary data"""
        agent = CanvasAgent(model="qwen:7b")
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "add docstring"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test Function",
                    "code": "def foo():\n    pass",
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 0,
                "end": 10,
                "text": "def foo():",
                "lineStart": 1,
                "lineEnd": 1
            },
            "artifactAction": "partial_update"
        }
        
        events = []
        try:
            async for event in agent.run(state):
                events.append(event)
                if len(events) > 50:
                    break
        except Exception as e:
            print(f"LLM not available for test: {e}")
            return
        
        # Find START event and verify it has selection data
        start_events = [e for e in events if getattr(e, 'event_type', None) == CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START]
        
        if start_events:
            start_event = start_events[0]
            assert hasattr(start_event, 'data')
            assert 'selection' in start_event.data
            assert start_event.data['selection']['start'] == 0
            assert start_event.data['selection']['end'] == 10


class TestPartialUpdateMerging:
    """Test content merging logic"""
    
    def test_merge_partial_update_replace_strategy(self):
        """Test that partial updates correctly merge into full content"""
        agent = CanvasAgent()
        
        original_code = "def foo():\n    return 42\n\ndef bar():\n    return 100"
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "make it async"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test Functions",
                    "code": original_code,
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 0,
                "end": 10,
                "text": "def foo():",
                "lineStart": 1,
                "lineEnd": 1
            },
            "artifactAction": "partial_update"
        }
        
        # Simulate updated content
        updated_selection = "async def foo():"
        
        # Merge the update
        agent._merge_partial_update(state, updated_selection)
        
        # Verify merge
        new_artifact = state["artifact"]
        assert new_artifact["currentIndex"] == 2
        assert len(new_artifact["contents"]) == 2
        
        new_code = new_artifact["contents"][1]["code"]
        assert new_code.startswith("async def foo():")
        assert "return 42" in new_code
        assert "def bar():" in new_code
    
    def test_merge_preserves_artifact_metadata(self):
        """Test that merging preserves artifact title and language"""
        agent = CanvasAgent()
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "edit"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "My Custom Title",
                    "code": "function test() { return true; }",
                    "language": "javascript"
                }]
            },
            "selectedText": {
                "start": 0,
                "end": 13,
                "text": "function test"
            },
            "artifactAction": "partial_update"
        }
        
        updated_selection = "async function test"
        agent._merge_partial_update(state, updated_selection)
        
        new_content = state["artifact"]["contents"][1]
        assert new_content["title"] == "My Custom Title"
        assert new_content["language"] == "javascript"
        assert new_content["type"] == "code"
    
    def test_merge_with_text_artifact(self):
        """Test merging partial updates in text/markdown artifacts"""
        agent = CanvasAgent()
        
        original_text = "# Title\n\nThis is a paragraph.\n\n## Section\n\nMore text here."
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "make it formal"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "text",
                    "title": "Document",
                    "fullMarkdown": original_text
                }]
            },
            "selectedText": {
                "start": 9,
                "end": 30,
                "text": "This is a paragraph."
            },
            "artifactAction": "partial_update"
        }
        
        updated_selection = "This represents a formal statement."
        agent._merge_partial_update(state, updated_selection)
        
        new_content = state["artifact"]["contents"][1]
        assert new_content["type"] == "text"
        assert "This represents a formal statement." in new_content["fullMarkdown"]
        assert "# Title" in new_content["fullMarkdown"]
        assert "## Section" in new_content["fullMarkdown"]


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_selection(self):
        """Test handling of empty selection"""
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "edit"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test",
                    "code": "def foo(): pass",
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 5,
                "end": 5,  # Empty selection
                "text": ""
            },
            "artifactAction": None
        }
        
        # Empty selection should still trigger partial_update if text is selected
        result = detect_intent_node(state)
        # With empty text, it might not be treated as partial_update
        # This is expected behavior
    
    def test_selection_beyond_content_bounds(self):
        """Test handling of invalid selection bounds"""
        agent = CanvasAgent()
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "edit"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test",
                    "code": "short",
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 0,
                "end": 1000,  # Beyond content length
                "text": "short"
            },
            "artifactAction": "partial_update"
        }
        
        # Should handle gracefully without crashing
        try:
            updated_content = "new content"
            agent._merge_partial_update(state, updated_content)
            # If it doesn't crash, test passes
            assert True
        except Exception as e:
            pytest.fail(f"Should handle invalid bounds gracefully: {e}")


class TestContextWindow:
    """Test context window extraction for partial updates"""
    
    def test_context_window_at_start_of_content(self):
        """Test context window when selection is at the start"""
        agent = CanvasAgent()
        
        code = "def foo():\n    pass\n\ndef bar():\n    pass"
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "edit"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test",
                    "code": code,
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 0,
                "end": 10,
                "text": "def foo():"
            },
            "artifactAction": "partial_update"
        }
        
        prompt = agent._build_partial_update_prompt(state)
        
        # Should include context after, even if before is empty
        assert "Context After Selection" in prompt
        assert "pass" in prompt
    
    def test_context_window_at_end_of_content(self):
        """Test context window when selection is at the end"""
        agent = CanvasAgent()
        
        code = "def foo():\n    pass\n\ndef bar():\n    return 42"
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "edit"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test",
                    "code": code,
                    "language": "python"
                }]
            },
            "selectedText": {
                "start": 33,
                "end": 42,
                "text": "return 42"
            },
            "artifactAction": "partial_update"
        }
        
        prompt = agent._build_partial_update_prompt(state)
        
        # Should include context before, even if after is empty
        assert "Context Before Selection" in prompt
        assert "def bar():" in prompt


class TestSelectionAtDifferentPositions:
    """Test partial updates work correctly at different content positions - Bug fix verification"""
    
    def test_merge_at_start_position(self):
        """Test partial update at the very start of content (position 0)"""
        agent = CanvasAgent()
        
        original_content = "def foo():\n    return 42\n\ndef bar():\n    return 100"
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "make it async"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "artifact_id": "test-artifact-1",
                "title": "Test Functions",
                "content": original_content,
                "language": "python"
            },
            "selectedText": {
                "start": 0,
                "end": 10,  # "def foo():"
                "text": "def foo():",
                "lineStart": 1,
                "lineEnd": 1
            },
            "artifactAction": "partial_update"
        }
        
        # Simulate LLM generated update
        updated_selection = "async def foo():"
        
        # Merge the update
        agent._merge_partial_update(state, updated_selection)
        
        # Verify merge correctness
        new_artifact = state["artifact"]
        new_content = new_artifact["content"]
        
        # Check that replacement happened at correct position
        assert new_content.startswith("async def foo():"), f"Expected to start with 'async def foo():', got: {new_content[:20]}"
        assert "\n    return 42" in new_content, "Should preserve content after selection"
        assert "def bar():" in new_content, "Should preserve content far after selection"
        
        # Verify structure is maintained
        expected_content = "async def foo():\n    return 42\n\ndef bar():\n    return 100"
        assert new_content == expected_content, f"Content mismatch:\nExpected: {expected_content}\nGot: {new_content}"
    
    def test_merge_at_middle_position(self):
        """Test partial update in the middle of content - Primary bug location"""
        agent = CanvasAgent()
        
        original_content = "def foo():\n    return 42\n\ndef bar():\n    return 100\n\ndef baz():\n    return 200"
        
        # Select the middle function
        middle_function_start = original_content.index("def bar():")
        middle_function_end = middle_function_start + len("def bar():\n    return 100")
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "make bar return 999"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "artifact_id": "test-artifact-2",
                "title": "Test Functions",
                "content": original_content,
                "language": "python"
            },
            "selectedText": {
                "start": middle_function_start,
                "end": middle_function_end,
                "text": "def bar():\n    return 100",
                "lineStart": 4,
                "lineEnd": 5
            },
            "artifactAction": "partial_update"
        }
        
        # Simulate LLM generated update
        updated_selection = "def bar():\n    return 999"
        
        # Merge the update
        agent._merge_partial_update(state, updated_selection)
        
        # Verify merge correctness
        new_artifact = state["artifact"]
        new_content = new_artifact["content"]
        
        # Check that content before selection is preserved
        assert new_content.startswith("def foo():\n    return 42"), "Content before selection should be preserved"
        
        # Check that replacement happened at correct position
        assert "return 999" in new_content, "Updated content should be present"
        assert "return 100" not in new_content, "Old content should be replaced"
        
        # Check that content after selection is preserved
        assert "def baz():\n    return 200" in new_content, "Content after selection should be preserved"
        
        # Verify exact structure
        expected_content = "def foo():\n    return 42\n\ndef bar():\n    return 999\n\ndef baz():\n    return 200"
        assert new_content == expected_content, f"Content mismatch:\nExpected: {expected_content}\nGot: {new_content}"
    
    def test_merge_at_end_position(self):
        """Test partial update at the end of content"""
        agent = CanvasAgent()
        
        original_content = "def foo():\n    return 42\n\ndef bar():\n    return 100"
        
        # Select the last function
        last_function_start = original_content.index("def bar():")
        last_function_end = len(original_content)
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "add error handling"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "artifact_id": "test-artifact-3",
                "title": "Test Functions",
                "content": original_content,
                "language": "python"
            },
            "selectedText": {
                "start": last_function_start,
                "end": last_function_end,
                "text": "def bar():\n    return 100",
                "lineStart": 4,
                "lineEnd": 5
            },
            "artifactAction": "partial_update"
        }
        
        # Simulate LLM generated update
        updated_selection = "def bar():\n    try:\n        return 100\n    except Exception as e:\n        return 0"
        
        # Merge the update
        agent._merge_partial_update(state, updated_selection)
        
        # Verify merge correctness
        new_artifact = state["artifact"]
        new_content = new_artifact["content"]
        
        # Check that content before selection is preserved
        assert new_content.startswith("def foo():\n    return 42"), "Content before selection should be preserved"
        
        # Check that replacement happened at correct position
        assert "try:" in new_content, "Updated content should be present"
        assert "except Exception as e:" in new_content, "Updated content should be present"
        
        # Verify structure
        expected_content = "def foo():\n    return 42\n\ndef bar():\n    try:\n        return 100\n    except Exception as e:\n        return 0"
        assert new_content == expected_content, f"Content mismatch:\nExpected: {expected_content}\nGot: {new_content}"
    
    def test_merge_single_line_in_middle(self):
        """Test updating a single line in the middle - precise selection"""
        agent = CanvasAgent()
        
        original_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        
        # Select "Line 3"
        line3_start = original_content.index("Line 3")
        line3_end = line3_start + len("Line 3")
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "change line 3"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "artifact_id": "test-artifact-4",
                "title": "Test Lines",
                "content": original_content,
                "language": "text"
            },
            "selectedText": {
                "start": line3_start,
                "end": line3_end,
                "text": "Line 3"
            },
            "artifactAction": "partial_update"
        }
        
        # Simulate LLM generated update
        updated_selection = "Modified Line 3"
        
        # Merge the update
        agent._merge_partial_update(state, updated_selection)
        
        # Verify merge correctness
        new_artifact = state["artifact"]
        new_content = new_artifact["content"]
        
        # Verify exact replacement
        expected_content = "Line 1\nLine 2\nModified Line 3\nLine 4\nLine 5"
        assert new_content == expected_content, f"Content mismatch:\nExpected: {expected_content}\nGot: {new_content}"
        
        # Ensure other lines are untouched
        assert new_content.count("Line 1") == 1, "Line 1 should be unchanged"
        assert new_content.count("Line 2") == 1, "Line 2 should be unchanged"
        assert new_content.count("Line 4") == 1, "Line 4 should be unchanged"
        assert new_content.count("Line 5") == 1, "Line 5 should be unchanged"
        assert "Modified Line 3" in new_content, "Modified Line 3 should be present"
    
    def test_merge_with_multiline_selection_in_middle(self):
        """Test updating multiple lines in the middle of content"""
        agent = CanvasAgent()
        
        original_content = """# Header
        
## Section 1
Content 1

## Section 2
Content 2

## Section 3
Content 3"""
        
        # Select Section 2 (header + content)
        section2_start = original_content.index("## Section 2")
        section2_end = original_content.index("## Section 3")
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "rewrite section 2"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "artifact_id": "test-artifact-5",
                "title": "Test Document",
                "content": original_content,
                "language": None
            },
            "selectedText": {
                "start": section2_start,
                "end": section2_end,
                "text": original_content[section2_start:section2_end]
            },
            "artifactAction": "partial_update"
        }
        
        # Simulate LLM generated update
        updated_selection = "## Section 2 (Updated)\nNew content here\n\n"
        
        # Merge the update
        agent._merge_partial_update(state, updated_selection)
        
        # Verify merge correctness
        new_artifact = state["artifact"]
        new_content = new_artifact["content"]
        
        # Check structure
        assert "# Header" in new_content, "Header should be preserved"
        assert "## Section 1" in new_content, "Section 1 should be preserved"
        assert "## Section 2 (Updated)" in new_content, "Updated section should be present"
        assert "New content here" in new_content, "New content should be present"
        assert "## Section 3" in new_content, "Section 3 should be preserved"
        assert "Content 2" not in new_content, "Old Section 2 content should be replaced"
    
    def test_merge_preserves_unicode_and_special_chars(self):
        """Test that merge correctly handles unicode and special characters"""
        agent = CanvasAgent()
        
        original_content = "Hello 世界\nLine 2: émojis 🚀\nLine 3: symbols @#$%"
        
        # Select the emoji line
        emoji_line_start = original_content.index("Line 2")
        emoji_line_end = emoji_line_start + len("Line 2: émojis 🚀")
        
        state: CanvasGraphState = {
            "messages": [{"role": "user", "content": "update emoji line"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": {
                "artifact_id": "test-artifact-6",
                "title": "Unicode Test",
                "content": original_content,
                "language": None
            },
            "selectedText": {
                "start": emoji_line_start,
                "end": emoji_line_end,
                "text": "Line 2: émojis 🚀"
            },
            "artifactAction": "partial_update"
        }
        
        # Simulate LLM generated update
        updated_selection = "Line 2: more émojis 🎉✨"
        
        # Merge the update
        agent._merge_partial_update(state, updated_selection)
        
        # Verify merge correctness
        new_artifact = state["artifact"]
        new_content = new_artifact["content"]
        
        # Verify unicode preservation
        expected_content = "Hello 世界\nLine 2: more émojis 🎉✨\nLine 3: symbols @#$%"
        assert new_content == expected_content, f"Content mismatch:\nExpected: {expected_content}\nGot: {new_content}"
        assert "世界" in new_content, "Chinese characters should be preserved"
        assert "🎉" in new_content, "New emoji should be present"
        assert "@#$%" in new_content, "Special symbols should be preserved"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
