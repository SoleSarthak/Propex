import logging
from typing import List, Dict, Any, Optional
from defusedxml import ElementTree as ET

logger = logging.getLogger(__name__)

class PomParser:
    def __init__(self):
        # Maven POMs usually have a namespace like xmlns="http://maven.apache.org/POM/4.0.0"
        # We define a generic namespace mapping to make querying easier
        self.ns = {'m': 'http://maven.apache.org/POM/4.0.0'}

    def parse_pom(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse a Maven POM XML string and extract dependencies and dependencyManagement.
        """
        result = {
            "dependencies": [],
            "managed_dependencies": []
        }

        if not xml_content:
            return result

        try:
            # Parse the XML string safely
            root = ET.fromstring(xml_content.encode('utf-8'))
            
            # Helper to strip namespace prefix if present, as sometimes POMs are missing it
            def get_elements(parent, tag):
                # Try with namespace first
                elems = parent.findall(f'm:{tag}', self.ns)
                if not elems:
                    # Try without namespace
                    elems = parent.findall(tag)
                return elems

            # Helper to get text content safely
            def get_text(parent, tag):
                # Try with namespace
                elem = parent.find(f'm:{tag}', self.ns)
                if elem is None:
                    # Try without namespace
                    elem = parent.find(tag)
                
                return elem.text.strip() if elem is not None and elem.text else None

            # 1. Extract direct dependencies
            deps_nodes = get_elements(root, 'dependencies')
            if deps_nodes:
                for deps_node in deps_nodes:
                    # Don't iterate dependencyManagement/dependencies here
                    # Wait, 'dependencies' can be at the root or under 'dependencyManagement'
                    # We want the root 'dependencies'
                    # In ElementTree, findall from root only searches direct children unless '//' is used
                    
                    for dep in get_elements(deps_node, 'dependency'):
                        group_id = get_text(dep, 'groupId')
                        artifact_id = get_text(dep, 'artifactId')
                        version = get_text(dep, 'version')
                        scope = get_text(dep, 'scope') or 'compile' # Default scope is compile
                        optional = get_text(dep, 'optional') == 'true'

                        if group_id and artifact_id:
                            result["dependencies"].append({
                                "group_id": group_id,
                                "artifact_id": artifact_id,
                                "version": version,
                                "scope": scope,
                                "optional": optional
                            })

            # 2. Extract Dependency Management (BOMs and locked versions)
            dep_mgmt_nodes = get_elements(root, 'dependencyManagement')
            if dep_mgmt_nodes:
                for dep_mgmt_node in dep_mgmt_nodes:
                    deps_nodes = get_elements(dep_mgmt_node, 'dependencies')
                    for deps_node in deps_nodes:
                        for dep in get_elements(deps_node, 'dependency'):
                            group_id = get_text(dep, 'groupId')
                            artifact_id = get_text(dep, 'artifactId')
                            version = get_text(dep, 'version')
                            scope = get_text(dep, 'scope')

                            if group_id and artifact_id:
                                result["managed_dependencies"].append({
                                    "group_id": group_id,
                                    "artifact_id": artifact_id,
                                    "version": version,
                                    "scope": scope
                                })

            logger.debug(f"Parsed {len(result['dependencies'])} deps and {len(result['managed_dependencies'])} managed deps.")
            return result

        except Exception as e:
            logger.error(f"Error parsing POM XML: {e}")
            return result
