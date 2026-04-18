from packaging.requirements import Requirement, InvalidRequirement
from typing import Optional, List
import tomli


class DependencyParser:
    @staticmethod
    def parse_pep_508(spec: str) -> Optional[Requirement]:
        try:
            return Requirement(spec)
        except InvalidRequirement:
            return None

    @staticmethod
    def extract_from_requirements_txt(content: str) -> List[Requirement]:
        reqs = []
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                req = DependencyParser.parse_pep_508(line)
                if req:
                    reqs.append(req)
        return reqs

    @staticmethod
    def extract_from_pyproject_toml(content: str) -> List[Requirement]:
        try:
            data = tomli.loads(content)
            deps = data.get("project", {}).get("dependencies", [])
            reqs = []
            for dep in deps:
                req = DependencyParser.parse_pep_508(dep)
                if req:
                    reqs.append(req)
            return reqs
        except tomli.TOMLDecodeError:
            return []
