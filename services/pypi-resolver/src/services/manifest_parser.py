import logging
import tomli  # requires 'tomli' in requirements.txt (or tomllib in 3.11+)
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ManifestParser:
    @staticmethod
    def parse_requirements_txt(content: str) -> List[str]:
        """
        Parse a requirements.txt file, handling comments and basic formatting.
        Returns a list of PEP 508 requirement strings.
        """
        requirements = []
        for line in content.splitlines():
            line = line.strip()
            # Ignore comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Ignore CLI flags like -r, -e, --index-url
            if line.startswith('-'):
                continue
                
            # Strip inline comments
            line = line.split('#')[0].strip()
            requirements.append(line)
            
        return requirements

    @staticmethod
    def parse_pyproject_toml(content: str) -> Dict[str, List[str]]:
        """
        Parse a pyproject.toml file.
        Extracts dependencies and optional-dependencies (extras).
        """
        result = {
            "dependencies": [],
            "extras": {}
        }
        
        try:
            # Using standard tomllib available in Python 3.11+
            import tomllib
            data = tomllib.loads(content)
            
            project = data.get("project", {})
            
            # Standard PEP 621 dependencies
            if "dependencies" in project:
                result["dependencies"].extend(project["dependencies"])
                
            if "optional-dependencies" in project:
                for extra, deps in project["optional-dependencies"].items():
                    result["extras"][extra] = deps
                    
            # Check for Poetry style (tool.poetry.dependencies)
            poetry = data.get("tool", {}).get("poetry", {})
            if "dependencies" in poetry:
                # Poetry uses a dict format, we simplify it here for the stub
                for pkg, version in poetry["dependencies"].items():
                    if pkg == "python": continue
                    if isinstance(version, str):
                        result["dependencies"].append(f"{pkg}{version}")
                    
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml: {e}")
            
        return result
