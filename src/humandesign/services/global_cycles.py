from datetime import date
from ..schemas.v2.calculate import GlobalCycleOutput

class GlobalCycleEngine:
    """
    Determines the background frequency of the human consciousness based on the era.
    """
    
    def get_cycle(self, calculation_date: date) -> GlobalCycleOutput:
        year = calculation_date.year
        
        if year < 1615:
            return GlobalCycleOutput(
                great_cycle="Cycle of Pisces",
                cycle_cross="Pre-Planning Era",
                gates=[],
                description="The era preceding the current Great Cycle."
            )
        elif year < 2027:
            return GlobalCycleOutput(
                great_cycle="Cycle of Aries",
                cycle_cross="Cross of Planning",
                gates=[37, 40, 9, 16],
                description="Era of institutionalization, social contracts, and detailed structure (1615-2027)."
            )
        else:
            return GlobalCycleOutput(
                great_cycle="Cycle of Aries",
                cycle_cross="Cross of the Sleeping Phoenix",
                gates=[55, 59, 20, 34],
                description="Era of individual spirit, charisma, and biological transition (2027-2439)."
            )
