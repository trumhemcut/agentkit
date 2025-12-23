from typing import Dict, Any, Optional
from tools import BaseTool
from graphs.canvas_graph import ArtifactV3, ArtifactContentCode, ArtifactContentText


class ExtractCodeTool(BaseTool):
    """Extract code from artifact for analysis"""
    name = "extract_code"
    description = "Extract code from current artifact"
    
    async def execute(self, artifact: Optional[ArtifactV3] = None, **kwargs) -> Dict[str, Any]:
        """Extract code from artifact"""
        if not artifact:
            return {"error": "No artifact provided", "code": None}
        
        current_content = artifact["contents"][artifact["currentIndex"] - 1]
        
        if current_content["type"] != "code":
            return {"error": "Current artifact is not a code artifact", "code": None}
        
        return {
            "code": current_content["code"],
            "language": current_content["language"],
            "title": current_content["title"]
        }


class UpdateCodeBlockTool(BaseTool):
    """Update specific code block in artifact"""
    name = "update_code_block"
    description = "Update code at specific line range"
    
    async def execute(
        self, 
        artifact: Optional[ArtifactV3] = None,
        start_line: int = 0,
        end_line: int = 0,
        new_code: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Update code block at specified line range"""
        if not artifact:
            return {"error": "No artifact provided", "success": False}
        
        current_content = artifact["contents"][artifact["currentIndex"] - 1]
        
        if current_content["type"] != "code":
            return {"error": "Current artifact is not a code artifact", "success": False}
        
        # Split code into lines
        code_lines = current_content["code"].split("\n")
        
        # Validate line numbers
        if start_line < 0 or end_line > len(code_lines) or start_line > end_line:
            return {"error": "Invalid line range", "success": False}
        
        # Replace lines
        new_code_lines = new_code.split("\n")
        updated_lines = code_lines[:start_line] + new_code_lines + code_lines[end_line:]
        updated_code = "\n".join(updated_lines)
        
        # Create new version
        new_index = len(artifact["contents"]) + 1
        new_content: ArtifactContentCode = {
            "index": new_index,
            "type": "code",
            "title": current_content["title"],
            "code": updated_code,
            "language": current_content["language"]
        }
        
        updated_artifact: ArtifactV3 = {
            "currentIndex": new_index,
            "contents": [*artifact["contents"], new_content]
        }
        
        return {
            "success": True,
            "artifact": updated_artifact,
            "lines_updated": f"{start_line}-{end_line}"
        }


class ConvertArtifactTypeTool(BaseTool):
    """Convert between code and text artifacts"""
    name = "convert_artifact"
    description = "Convert artifact type (code <-> text)"
    
    async def execute(
        self,
        artifact: Optional[ArtifactV3] = None,
        target_type: str = "text",
        **kwargs
    ) -> Dict[str, Any]:
        """Convert artifact to different type"""
        if not artifact:
            return {"error": "No artifact provided", "success": False}
        
        current_content = artifact["contents"][artifact["currentIndex"] - 1]
        
        if current_content["type"] == target_type:
            return {"error": f"Artifact is already of type {target_type}", "success": False}
        
        new_index = len(artifact["contents"]) + 1
        
        if target_type == "text":
            # Convert code to text (wrap in markdown code block)
            code = current_content["code"]
            language = current_content["language"]
            markdown = f"```{language}\n{code}\n```"
            
            new_content: ArtifactContentText = {
                "index": new_index,
                "type": "text",
                "title": current_content["title"],
                "fullMarkdown": markdown
            }
        else:
            # Convert text to code (extract from markdown code block)
            markdown = current_content["fullMarkdown"]
            
            # Try to extract code from markdown code block
            if "```" in markdown:
                parts = markdown.split("```")
                if len(parts) >= 3:
                    code_block = parts[1]
                    lines = code_block.split("\n")
                    language = lines[0].strip() if lines else "python"
                    code = "\n".join(lines[1:]) if len(lines) > 1 else code_block
                else:
                    code = markdown
                    language = "python"
            else:
                code = markdown
                language = "python"
            
            new_content: ArtifactContentCode = {
                "index": new_index,
                "type": "code",
                "title": current_content["title"],
                "code": code,
                "language": language
            }
        
        updated_artifact: ArtifactV3 = {
            "currentIndex": new_index,
            "contents": [*artifact["contents"], new_content]
        }
        
        return {
            "success": True,
            "artifact": updated_artifact,
            "converted_to": target_type
        }


class AnalyzeArtifactTool(BaseTool):
    """Analyze artifact for complexity, quality, etc."""
    name = "analyze_artifact"
    description = "Analyze artifact content for metrics and insights"
    
    async def execute(self, artifact: Optional[ArtifactV3] = None, **kwargs) -> Dict[str, Any]:
        """Analyze artifact"""
        if not artifact:
            return {"error": "No artifact provided"}
        
        current_content = artifact["contents"][artifact["currentIndex"] - 1]
        
        if current_content["type"] == "code":
            code = current_content["code"]
            lines = code.split("\n")
            
            analysis = {
                "type": "code",
                "language": current_content["language"],
                "total_lines": len(lines),
                "non_empty_lines": len([line for line in lines if line.strip()]),
                "comment_lines": len([line for line in lines if line.strip().startswith("#")]),
                "has_functions": "def " in code or "function " in code,
                "has_classes": "class " in code,
            }
        else:
            markdown = current_content["fullMarkdown"]
            
            analysis = {
                "type": "text",
                "total_characters": len(markdown),
                "word_count": len(markdown.split()),
                "has_headings": "#" in markdown,
                "has_code_blocks": "```" in markdown,
                "has_lists": "- " in markdown or "* " in markdown or "1. " in markdown,
            }
        
        return analysis
