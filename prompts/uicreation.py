from __future__ import annotations
from typing import Any, Dict, List
from dynamicprompts.wildcardmanager import WildcardManager

class UiCreation:
    def __init__(self, wildcard_manager: WildcardManager):
        self._wildcard_manager = wildcard_manager

    def write(self, wildcards: List[str], hierarchy: Dict[str, Any]) -> str:
        html = ""
        for wildcard in wildcards:
            html += f"""<p class="wildcard">{wildcard}</p>"""

        for directory, h in hierarchy.items():
            contents = self.write(h[0], h[1])
            html += f"""
                <button type="button" class="collapsible">{directory} :</button>
                <div class="content">
                    {contents}
                </div>
            """

        return html

    def probe(self) -> str:
        wildcards, hierarchy = self._wildcard_manager.get_wildcard_hierarchy()
        return self.write(wildcards, hierarchy)


