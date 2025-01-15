from typing import List
from datetime import datetime

def process_ls_trend(json_data: List[dict]) -> List[dict]:
    """
    Process raw L/S trend JSON data into LSTrendData objects.
    
    Args:
        json_data: List of dictionaries containing asset trend data
        
    Returns:
        List of LSTrendData objects
    """
    try:
        result = []

        for asset_data in json_data:
            asset_name = asset_data["Asset"]
            points = []
            
            # Get all dates except "Asset" key
            dates = [k for k in asset_data.keys() if k != "Asset"]
            dates.sort()  # Sort dates chronologically
            
            prev_ratio = None
            for date_str in dates:
                # Skip empty values
                if asset_data[date_str] == "":
                    continue
                    
                ratio = float(asset_data[date_str])
                
                # Determine majority side based on ratio change from previous day
                if prev_ratio is None:
                    majority_side = "LONG" if ratio >= 50 else "SHORT"
                else:
                    majority_side = "LONG" if ratio > prev_ratio else "SHORT"
                
                # Create point data
                point = {
                    "timestamp": datetime.strptime(date_str, "%Y-%m-%d"),
                    "ls_ratio": ratio,
                    "majority_side": majority_side,
                    "notional_delta": abs(50 - ratio) # Distance from neutral (50/50)
                }
                points.append(point)
                prev_ratio = ratio
                
            # Only create trend data if we have points
            if points:
                trend = {
                    "asset": asset_name,
                    "points": points,
                    "last_updated": max(p["timestamp"] for p in points),
                    "update_frequency": "daily",
                    "historical_days": len(points)
                }
                result.append(trend)
                
        return result
    except Exception as e:
        print(f"Error processing L/S trend data for {e}")
        return None
