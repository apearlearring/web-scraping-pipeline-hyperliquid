from .schema import *

def validate_global_data(data):
    try:
        validated_global_data = GlobalMarketMetrics(**data)
        print(validated_global_data)
    except Exception as e:
        print(f"Validation error for global data: {e}")
    return data

def validate_asset_data(asset_data_list):
    """
    Validates a list of asset data dictionaries using the AssetMetrics Pydantic model.

    Args:
        asset_data_list (list): A list of dictionaries, each representing an asset's data.

    Returns:
        list: A list of validated AssetMetrics objects.

    """
    print(len(asset_data_list))
    validated_assets = []
    for asset_data in asset_data_list:
        try:
            validated_asset = AssetMetrics(**asset_data)
            validated_assets.append(validated_asset)
        except Exception as e:
            print(f"Validation error for asset {asset_data.get('Asset')}: {e}")
    return validated_assets


