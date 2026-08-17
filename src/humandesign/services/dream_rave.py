from typing import Set
from ..schemas.v2.calculate import DreamRaveOutput

class DreamRaveEngine:
    """
    Analyzes the 3-center 'Night' design (Dream Rave).
    Model: 3 Centers (Head, Ajna, Solar Plexus) and 15 specific gates.
    """
    
    DREAM_CENTERS = ["Head", "Ajna", "Solar Plexus"]
    
    # The 15 gates of the Dream Rave Matrix
    DREAM_GATES = {
        62, 23, 12, 15, 27, 50, 6, 20, 57, 8, 1, 14, 2, 46, 29
    }
    
    def analyze(self, active_gates: Set[int]) -> DreamRaveOutput:
        """
        Calculates which Dream Rave gates are active based on the combined design.
        """
        # Filter to Dream Matrix gates
        active_dream_gates = [g for g in self.DREAM_GATES if g in active_gates]
        
        return DreamRaveOutput(
            activated_centers=[], 
            activated_gates=sorted(active_dream_gates),
            status="Analyzed"
        )
