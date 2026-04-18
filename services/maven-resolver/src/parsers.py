import xml.etree.ElementTree as ET
from typing import List, Dict


class PomParser:
    @staticmethod
    def parse_pom_dependencies(xml_content: str) -> List[Dict]:
        dependencies = []
        try:
            # Remove namespace prefixes to make parsing easier
            it = ET.iterparse(xml_content)
            for _, el in it:
                _, _, el.tag = el.tag.rpartition("}")
            root = it.root

            deps_node = root.find(".//dependencies")
            if deps_node is not None:
                for dep in deps_node.findall("dependency"):
                    group_id = dep.find("groupId")
                    artifact_id = dep.find("artifactId")
                    version = dep.find("version")
                    scope = dep.find("scope")

                    if group_id is not None and artifact_id is not None:
                        dependencies.append(
                            {
                                "group_id": group_id.text,
                                "artifact_id": artifact_id.text,
                                "version": (
                                    version.text if version is not None else "latest"
                                ),
                                "scope": scope.text if scope is not None else "compile",
                            }
                        )
        except Exception:
            pass
        return dependencies


class MavenVersionSpecParser:
    @staticmethod
    def parse_range(range_str: str) -> dict:
        """
        Parses Maven ranges like [1.0, 2.0)
        """
        range_str = range_str.strip()
        result = {"min": None, "max": None, "min_inc": False, "max_inc": False}
        if range_str.startswith("[") or range_str.startswith("("):
            result["min_inc"] = range_str.startswith("[")
            result["max_inc"] = range_str.endswith("]")
            parts = range_str[1:-1].split(",")
            if len(parts) == 2:
                result["min"] = parts[0].strip() or None
                result["max"] = parts[1].strip() or None
            elif len(parts) == 1:  # Single hard requirement [1.0]
                result["min"] = parts[0].strip()
                result["max"] = parts[0].strip()
        else:
            # Soft requirement
            result["min"] = range_str
        return result
