"""
Rule-based packing recommendation tool.
"""
import logging
from typing import Dict, List, Any

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class PackingTool(BaseTool):
    """Rule-based packing recommendations."""
    
    def __init__(self):
        super().__init__("packing", cache_ttl_hours=1)  # Shorter cache for packing
    
    def _execute(
        self,
        trip_length_days: int,
        weather_data: Dict[str, Any],
        activities: List[str],
        travelers: Dict[str, Any],
        accommodation_type: str = "hotel",
        has_laundry: bool = False,
        is_international: bool = True,
        requires_flight: bool = True,
        requires_accommodation_booking: bool = True
    ) -> ToolResult:
        """Generate packing recommendations based on trip parameters."""
        
        try:
            # Validate inputs
            if trip_length_days < 1 or trip_length_days > 365:
                return ToolResult(
                    success=False,
                    error="Trip length must be between 1 and 365 days",
                    confidence="high"
                )
            
            # Extract weather info
            avg_high = weather_data.get("avg_high", 20)
            avg_low = weather_data.get("avg_low", 10)
            max_precip = weather_data.get("max_precip_prob", 0)
            
            # Determine weather conditions
            climate = self._determine_climate(avg_high, avg_low)
            rain_risk = max_precip > 30
            
            # Build packing list
            packing_list = {
                "clothing": self._get_clothing_recommendations(
                    climate, trip_length_days, has_laundry, rain_risk
                ),
                "footwear": self._get_footwear_recommendations(activities, climate, rain_risk),
                "accessories": self._get_accessories_recommendations(climate, activities, rain_risk),
                "electronics": self._get_electronics_recommendations(trip_length_days, activities),
                "toiletries": self._get_toiletries_recommendations(trip_length_days, accommodation_type),
                "documents": self._get_documents_recommendations(
                    is_international, requires_flight, requires_accommodation_booking
                ),
                "optional": self._get_optional_recommendations(activities, travelers)
            }
            
            # Add weather-specific notes
            weather_notes = self._generate_weather_notes(climate, rain_risk, max_precip)
            
            # Calculate totals
            total_items = sum(
                sum(item["qty"] for item in category) 
                for category in packing_list.values()
            )
            
            result_data = {
                "categories": packing_list,
                "total_items": total_items,
                "weather_considerations": weather_notes,
                "trip_summary": {
                    "duration": f"{trip_length_days} days",
                    "climate": climate,
                    "rain_risk": "high" if rain_risk else "low",
                    "laundry_available": has_laundry
                }
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                confidence="high"
            )
            
        except Exception as e:
            logger.error(f"Packing tool error: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to generate packing list: {str(e)}",
                confidence="low"
            )
    
    def _determine_climate(self, avg_high: float, avg_low: float) -> str:
        """Determine climate category from temperature."""
        if avg_high > 30:
            return "hot"
        elif avg_high > 20:
            return "warm" 
        elif avg_high > 10:
            return "mild"
        elif avg_high > 0:
            return "cool"
        else:
            return "cold"
    
    def _get_clothing_recommendations(
        self, climate: str, trip_length: int, has_laundry: bool, rain_risk: bool
    ) -> List[Dict[str, Any]]:
        """Get clothing recommendations."""
        clothes = []
        
        # Base clothing calculation
        if has_laundry:
            underwear_days = min(trip_length, 7)  # Max 7 days if laundry available
            shirt_days = min(trip_length, 5)      # Max 5 days if laundry available
        else:
            underwear_days = min(trip_length, 14)  # Max 14 days even without laundry
            shirt_days = min(trip_length, 10)     # Max 10 days even without laundry
        
        # Underwear and basics
        clothes.extend([
            {"name": "Underwear", "qty": underwear_days, "reason": "Daily essentials"},
            {"name": "Socks", "qty": underwear_days, "reason": "Daily essentials"},
        ])
        
        # Climate-specific clothing
        if climate in ["hot", "warm"]:
            clothes.extend([
                {"name": "T-shirts", "qty": shirt_days, "reason": f"For {climate} weather"},
                {"name": "Shorts", "qty": max(2, trip_length // 3), "reason": f"For {climate} weather"},
                {"name": "Light pants", "qty": 1, "reason": "For air conditioning or evenings"},
                {"name": "Swimwear", "qty": 1, "reason": "For beaches or pools"},
            ])
            
        elif climate == "mild":
            clothes.extend([
                {"name": "T-shirts", "qty": shirt_days // 2, "reason": "For warmer days"},
                {"name": "Long-sleeve shirts", "qty": shirt_days // 2, "reason": "For cooler moments"},
                {"name": "Jeans/pants", "qty": 2, "reason": "Versatile for mild weather"},
                {"name": "Light sweater", "qty": 1, "reason": "For cooler evenings"},
            ])
            
        elif climate in ["cool", "cold"]:
            clothes.extend([
                {"name": "Long-sleeve shirts", "qty": shirt_days, "reason": f"For {climate} weather"},
                {"name": "Warm pants", "qty": max(2, trip_length // 4), "reason": f"For {climate} weather"},
                {"name": "Sweater/hoodie", "qty": 2, "reason": "For warmth and layering"},
                {"name": "Warm jacket", "qty": 1, "reason": f"Essential for {climate} weather"},
            ])
            
            if climate == "cold":
                clothes.extend([
                    {"name": "Thermal underwear", "qty": 2, "reason": "For very cold conditions"},
                    {"name": "Warm hat", "qty": 1, "reason": "Heat loss prevention"},
                    {"name": "Gloves", "qty": 1, "reason": "Hand protection"},
                ])
        
        # Rain gear
        if rain_risk:
            clothes.append({
                "name": "Rain jacket/poncho", 
                "qty": 1, 
                "reason": "High rain probability - waterproof protection"
            })
        
        return clothes
    
    def _get_footwear_recommendations(
        self, activities: List[str], climate: str, rain_risk: bool
    ) -> List[Dict[str, Any]]:
        """Get footwear recommendations."""
        shoes = []
        
        # Base comfortable shoes
        shoes.append({
            "name": "Comfortable walking shoes", 
            "qty": 1, 
            "reason": "Essential for sightseeing"
        })
        
        # Activity-specific footwear
        if any(act in " ".join(activities).lower() for act in ["hike", "trek", "nature", "mountain"]):
            shoes.append({
                "name": "Hiking boots", 
                "qty": 1, 
                "reason": "For hiking activities"
            })
        
        if any(act in " ".join(activities).lower() for act in ["beach", "swim", "pool"]):
            shoes.append({
                "name": "Sandals/flip-flops", 
                "qty": 1, 
                "reason": "For beach/pool activities"
            })
        
        if any(act in " ".join(activities).lower() for act in ["formal", "dining", "restaurant", "theater"]):
            shoes.append({
                "name": "Dress shoes", 
                "qty": 1, 
                "reason": "For formal occasions"
            })
        
        # Weather-specific
        if rain_risk:
            shoes.append({
                "name": "Waterproof shoes", 
                "qty": 1, 
                "reason": "Rain protection"
            })
        
        if climate == "cold":
            shoes.append({
                "name": "Warm boots", 
                "qty": 1, 
                "reason": "Insulation for cold weather"
            })
        
        return shoes
    
    def _get_accessories_recommendations(
        self, climate: str, activities: List[str], rain_risk: bool
    ) -> List[Dict[str, Any]]:
        """Get accessories recommendations."""
        accessories = []
        
        # Universal accessories
        accessories.extend([
            {"name": "Sunglasses", "qty": 1, "reason": "Eye protection"},
            {"name": "Watch", "qty": 1, "reason": "Time management"},
        ])
        
        # Climate-specific
        if climate in ["hot", "warm"]:
            accessories.extend([
                {"name": "Sun hat", "qty": 1, "reason": "Sun protection"},
                {"name": "Sunscreen", "qty": 1, "reason": "Skin protection"},
            ])
        
        # Activity-specific
        if any(act in " ".join(activities).lower() for act in ["swim", "beach"]):
            accessories.append({
                "name": "Beach towel", 
                "qty": 1, 
                "reason": "For swimming activities"
            })
        
        if rain_risk:
            accessories.append({
                "name": "Umbrella", 
                "qty": 1, 
                "reason": "Portable rain protection"
            })
        
        return accessories
    
    def _get_electronics_recommendations(
        self, trip_length: int, activities: List[str]
    ) -> List[Dict[str, Any]]:
        """Get electronics recommendations."""
        electronics = [
            {"name": "Phone charger", "qty": 1, "reason": "Essential communication"},
            {"name": "Power bank", "qty": 1, "reason": "Backup power for long days"},
        ]
        
        if trip_length > 3:
            electronics.append({
                "name": "Universal adapter", 
                "qty": 1, 
                "reason": "For international outlets"
            })
        
        if any(act in " ".join(activities).lower() for act in ["photo", "sightseeing", "tour"]):
            electronics.append({
                "name": "Camera", 
                "qty": 1, 
                "reason": "Capture memories"
            })
        
        return electronics
    
    def _get_toiletries_recommendations(
        self, trip_length: int, accommodation_type: str
    ) -> List[Dict[str, Any]]:
        """Get toiletries recommendations."""
        toiletries = [
            {"name": "Toothbrush", "qty": 1, "reason": "Daily hygiene"},
            {"name": "Toothpaste", "qty": 1, "reason": "Daily hygiene"},
        ]
        
        if accommodation_type in ["hostel", "camping", "airbnb"]:
            toiletries.extend([
                {"name": "Shampoo", "qty": 1, "reason": "May not be provided"},
                {"name": "Soap", "qty": 1, "reason": "May not be provided"},
                {"name": "Towel", "qty": 1, "reason": "May not be provided"},
            ])
        
        if trip_length > 7:
            toiletries.append({
                "name": "Laundry detergent pods", 
                "qty": 3, 
                "reason": "For longer trips"
            })
        
        return toiletries
    
    def _get_documents_recommendations(
        self, 
        is_international: bool = True, 
        requires_flight: bool = True,
        requires_accommodation_booking: bool = True
    ) -> List[Dict[str, Any]]:
        """Get travel documents recommendations based on trip type."""
        documents = []
        
        # Always useful for any trip
        documents.append({
            "name": "ID/Driver's license", 
            "qty": 1, 
            "reason": "Personal identification"
        })
        
        # International travel documents
        if is_international:
            documents.append({
                "name": "Passport", 
                "qty": 1, 
                "reason": "Required for international travel"
            })
            
            documents.append({
                "name": "Travel insurance", 
                "qty": 1, 
                "reason": "Emergency protection abroad"
            })
        else:
            # Domestic travel might still benefit from insurance for longer trips
            documents.append({
                "name": "Travel insurance (optional)", 
                "qty": 1, 
                "reason": "Emergency protection for extended trips"
            })
        
        # Flight-specific documents
        if requires_flight:
            documents.append({
                "name": "Flight tickets/boarding pass", 
                "qty": 1, 
                "reason": "Required for air travel"
            })
        
        # Accommodation documents
        if requires_accommodation_booking:
            documents.append({
                "name": "Accommodation booking confirmation", 
                "qty": 1, 
                "reason": "Reservation proof for check-in"
            })
        
        # Car travel documents (if not flying)
        if not requires_flight:
            documents.extend([
                {
                    "name": "Vehicle registration", 
                    "qty": 1, 
                    "reason": "Required if driving own vehicle"
                },
                {
                    "name": "Auto insurance", 
                    "qty": 1, 
                    "reason": "Legal requirement for driving"
                }
            ])
        
        return documents
    
    def _get_optional_recommendations(
        self, activities: List[str], travelers: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get optional items recommendations."""
        optional = []
        
        if travelers.get("kids", 0) > 0:
            optional.extend([
                {"name": "Entertainment for kids", "qty": 2, "reason": "Keep children occupied"},
                {"name": "Snacks", "qty": 5, "reason": "For hungry kids"},
            ])
        
        if any(act in " ".join(activities).lower() for act in ["read", "relax", "beach"]):
            optional.append({
                "name": "Book/e-reader", 
                "qty": 1, 
                "reason": "Entertainment during downtime"
            })
        
        return optional
    
    def _generate_weather_notes(
        self, climate: str, rain_risk: bool, max_precip: float
    ) -> str:
        """Generate weather-specific packing notes."""
        notes = []
        
        if climate == "hot":
            notes.append("Pack light, breathable fabrics. Don't forget sun protection.")
        elif climate == "cold":
            notes.append("Layer clothing for warmth. Waterproof outer layer recommended.")
        elif climate == "mild":
            notes.append("Pack layers for temperature changes throughout the day.")
        
        if rain_risk:
            notes.append(f"Rain probability up to {max_precip}% - pack waterproof items.")
        
        return " ".join(notes)


# Global packing tool instance
_packing_tool = PackingTool()


def get_packing_tool() -> PackingTool:
    """Get the packing tool instance."""
    return _packing_tool