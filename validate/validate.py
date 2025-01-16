from .schema import (AssetMetrics, GlobalMarketMetrics,
                     LiquidationDistributionData, LSTrendData)


def validate_global_position_data(data):
    """
    Validates global market metrics data using the GlobalMarketMetrics Pydantic model.

    Args:
        data (dict): The global market metrics data.

    Returns:
        GlobalMarketMetrics: The validated global market metrics data.
    """
    try:
        validated_global_position_data = GlobalMarketMetrics(**data)
        return validated_global_position_data
    except Exception as e:
        print(f"Validation error for global data: {e}")
    return data


def validate_position_data(asset_data_list):
    """
    Validates a list of asset data dictionaries using the AssetMetrics Pydantic model.

    Args:
        asset_data_list (list): A list of dictionaries, each representing an asset's data.

    Returns:
        list: A list of validated AssetMetrics objects.
    """
    validated_assets = []
    for asset_data in asset_data_list:
        try:
            validated_asset = AssetMetrics(**asset_data)
            validated_assets.append(validated_asset)
        except Exception as e:
            print(f"Validation error for asset {asset_data.get('Asset')}: {e}")
    return validated_assets


def validate_liquidation_distribution_data(liquidation_distribution_list):
    """
    Validates a list of liquidation distribution data using the LiquidationDistributionData Pydantic model.

    Args:
        liquidation_distribution_list (list): A list of dictionaries, each representing liquidation distribution data.

    Returns:
        list: A list of validated LiquidationDistributionData objects.
    """
    validated_distributions = []
    for distribution_data in liquidation_distribution_list:
        try:
            validated_distribution = LiquidationDistributionData(
                **distribution_data)
            validated_distributions.append(validated_distribution)
        except Exception as e:
            print(
                f"Validation error for {
                    distribution_data.get('asset')} liquidation distribution: {e}")
    return validated_distributions


def validate_ls_trend_data(ls_trend_data_list):
    """
    Validates a list of L/S trend data using the LSTrendData Pydantic model.

    Args:
        ls_trend_data_list (list): A list of dictionaries, each representing L/S trend data.

    Returns:
        list: A list of validated LSTrendData objects.
    """
    validated_trends = []
    for trend_data in ls_trend_data_list:
        try:
            validated_trend = LSTrendData(**trend_data)
            validated_trends.append(validated_trend)
        except Exception as e:
            print(
                f"Validation error for {
                    trend_data.get('asset')} L/S trend: {e}")
    return validated_trends
