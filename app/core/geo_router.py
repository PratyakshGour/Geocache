import math
from typing import Tuple, List, Optional
from app.core.config import settings
from app.schemas.data import RouteComparison, GeoRouteResponse


class GeoRouter:
    """
    Location-based request routing engine using the Haversine formula
    to calculate geographical distances between client locations and
    distributed regional cache servers.
    """
    EARTH_RADIUS_KM = 6371.0

    @classmethod
    def haversine_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance in kilometers between two points on the earth."""
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = cls.EARTH_RADIUS_KM * c
        return round(distance, 2)

    @classmethod
    def resolve_location(
        cls,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city: Optional[str] = None
    ) -> Tuple[float, float, str]:
        """Resolve client coordinates from explicit lat/lon or city preset name."""
        if lat is not None and lon is not None:
            return lat, lon, f"Custom ({lat:.2f}, {lon:.2f})"

        if city:
            city_lower = city.lower().strip()
            for preset in settings.CITY_PRESETS:
                if city_lower in preset.name.lower():
                    return preset.lat, preset.lon, preset.name

        # Default fallback to first city (New York) if nothing provided
        default_city = settings.CITY_PRESETS[0]
        return default_city.lat, default_city.lon, default_city.name

    @classmethod
    def calculate_routes(cls, lat: float, lon: float) -> List[RouteComparison]:
        """Calculate distance and simulated latency to all regional servers."""
        routes = []
        for region_id, region in settings.REGIONS.items():
            dist = cls.haversine_distance(lat, lon, region.lat, region.lon)
            # Simulated fiber optic latency: base processing time ~4ms + ~0.01ms per km
            simulated_latency = round(dist * 0.012 + 4.0, 2)
            
            routes.append(
                RouteComparison(
                    region_id=region_id,
                    region_name=region.name,
                    distance_km=dist,
                    simulated_latency_ms=simulated_latency,
                    is_closest=False
                )
            )

        # Sort by distance ascending
        routes.sort(key=lambda r: r.distance_km)
        if routes:
            routes[0].is_closest = True

        return routes

    @classmethod
    def get_optimal_region(
        cls,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city: Optional[str] = None
    ) -> GeoRouteResponse:
        """Find the nearest optimal server node for a client request."""
        client_lat, client_lon, location_label = cls.resolve_location(lat, lon, city)
        routes = cls.calculate_routes(client_lat, client_lon)
        
        optimal = routes[0]
        return GeoRouteResponse(
            client_location=location_label,
            optimal_region_id=optimal.region_id,
            optimal_region_name=optimal.region_name,
            distance_km=optimal.distance_km,
            simulated_latency_ms=optimal.simulated_latency_ms,
            all_regions=routes
        )


geo_router = GeoRouter()
