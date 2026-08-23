from typing import Dict, Any, Optional
from .sqlite_repository import SQLiteRepository

class EnrichmentService:
    def __init__(self):
        self.repo = SQLiteRepository()

    def enrich_gate(self, gate_number: int, line_number: int, planet_name: str) -> Dict[str, Any]:
        """
        Fetches semantic data and attempts to determine fixation.
        """
        gate_info = self.repo.get_gate_label(gate_number)
        line_info = self.repo.get_line_label(gate_number, line_number)
        
        # Simple Fixation Parser (Logic based on description text)
        fixation = self._parse_fixation(line_info.get("description", ""), planet_name)
        
        return {
            "gate_name": gate_info.get("name"),
            "gate_summary": gate_info.get("summary"),
            "line_name": line_info.get("name"),
            "line_description": line_info.get("description"),
            "fixation": fixation
        }

    def _parse_fixation(self, description: str, planet_name: str) -> Optional[Dict[str, Any]]:
        """
        Heuristic: Look for 'PlanetName exalted' or 'PlanetName in detriment'.
        This is a temporary parser until a structured table is found/provided.
        """
        if not description:
            return None
            
        desc_lower = description.lower()
        planet_lower = planet_name.lower()
        
        # Check for Exaltation
        if f"{planet_lower} exalted" in desc_lower or f"{planet_lower} as a symbol of" in desc_lower:
            return {"type": "Exalted", "value": "Up"}
        
        # Check for Detriment
        if f"{planet_lower} in detriment" in desc_lower or f"detriment of {planet_lower}" in desc_lower:
            return {"type": "Detriment", "value": "Down"}
            
        return None

    def enrich_channel(self, gate_a: int, gate_b: int) -> Dict[str, Any]:
        """Reference text for one channel, from hd_data.sqlite.

        This is what turns a relational payload from gate numbers into something a
        consultant can read: the channel's own name, what it is a design of, the
        long description, and the gift each gate contributes.
        """
        row = self.repo.get_channel(gate_a, gate_b)
        if not row:
            return {}
        gifts = self.repo.get_channel_gifts(row["channel_id"])
        return {
            "channel_id": row.get("channel_id"),
            "name": row.get("name"),
            "type": row.get("type"),
            "design_purpose": row.get("design_purpose"),
            "description": row.get("description"),
            "gifts": {str(g): gift for g, gift in sorted(gifts.items())},
        }

    def enrich_gate_reference(self, gate_number: int) -> Dict[str, Any]:
        """Gate name, summary, circuit and quarter — no line, no fixation."""
        return self.repo.get_gate_reference(gate_number)

    def enrich_response(self, response_data: Any) -> Any:
        """
        Recursively enrich the response structure. Supports both dicts and Pydantic models.
        """
        # Check if gates are nested or top-level
        if hasattr(response_data, "gates") and response_data.gates:
            # V2 structure with nested gates
            gates_obj = response_data.gates
            gate_collections = [
                ("personality", getattr(gates_obj, "personality", {})),
                ("design", getattr(gates_obj, "design", {}))
            ]
        else:
            # Fallback for old structure
            gate_collections = [
                ("personality_gates", getattr(response_data, "personality_gates", {})),
                ("design_gates", getattr(response_data, "design_gates", {}))
            ]
        
        for gate_key, gates in gate_collections:
            if gates:
                # Handle both dict of models and dict of dicts
                iterator = gates.items() if hasattr(gates, "items") else gates
                
                for planet, gate_data in iterator:
                    is_gate_model = not isinstance(gate_data, dict)
                    
                    if is_gate_model:
                        enriched = self.enrich_gate(gate_data.gate, gate_data.line, planet)
                        gate_data.gate_name = enriched.get("gate_name")
                        gate_data.gate_summary = enriched.get("gate_summary")
                        gate_data.line_name = enriched.get("line_name")
                        gate_data.line_description = enriched.get("line_description")
                        gate_data.fixation = enriched.get("fixation")
                    else:
                        enriched = self.enrich_gate(
                            gate_data.get("gate"), 
                            gate_data.get("line"),
                            planet
                        )
                        gate_data.update(enriched)
                    
        return response_data
