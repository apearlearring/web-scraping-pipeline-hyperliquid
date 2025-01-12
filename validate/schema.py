from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional

#################################L/S Trend Over Time#############################################

class LongShortTrendPoint(BaseModel):
    timestamp: datetime
    ls_ratio: float
    majority_side: str
    notional_delta: float

class LSTrendData(BaseModel):
    asset: str = Field(..., description="Which asset this trend belongs to")
    points: List[LongShortTrendPoint] = Field(..., description="Time-based L/S ratio snapshots")
    last_updated: datetime = Field(..., description="When this trend data was last updated")
    update_frequency: str = Field(default="daily", description="Could be 'daily', 'hourly', etc.")
    historical_days: int = Field(default=8, description="Number of days covered in this trend snapshot")

#########################Global / Market-Level#######################################

class GlobalMarketMetrics(BaseModel):
    total_notional_volume: float = Field(..., description="Global sum of all position values in USD")
    total_tickers: int = Field(..., description="Total number of tickers")
    long_positions_count: float = Field(..., description="Total count of long positions across all assets")
    short_positions_count: float = Field(..., description="Total count of short positions across all assets")
    global_ls_ratio: float = Field(..., description="Global ratio of long vs. short")
    timestamp: datetime = Field(..., description="Timestamp of this snapshot")
    base_currency: str = Field(default="USD", description="Quote currency (usually USD)")

    @validator('global_ls_ratio')
    def ls_ratio_nonnegative(cls, value):
        if value < 0:
            raise ValueError("global_ls_ratio cannot be negative")
        return value
    
    @validator('total_notional_volume')
    def is_total_notional_volume_presented(cls, value):
        if value is None:
            raise ValueError("total_notional_volume cannot be empty")
        return value

    @validator('timestamp')
    def is_timestamp_presented(cls, value):
        if value is None:
            raise ValueError("timestamp cannot be negative")
        return value

#########################################User Positions###############################

class UserPosition(BaseModel):
    asset: str = Field(..., description="e.g., BTC, HYPE, etc.")
    address: str = Field(..., description="Wallet or account address")
    notional_value: float = Field(..., description="Size of the position in USD")
    entry_price: float = Field(..., description="Position entry price")
    liquidation_price: float = Field(..., description="Liquidation threshold")
    pnl: float = Field(..., description="Current profit/loss in USD")
    funding_earned: float = Field(..., description="Total funding accrued on this position")
    account_value: float = Field(..., description="Total equity of the account")
    timestamp: datetime = Field(..., description="Time of this position snapshot")
    position_type: str = Field(..., description="LONG or SHORT")

    @validator('liquidation_price')
    def check_prices(cls, value):
        if value <= 0:
            raise ValueError("Liquidation price must be positive")
        return value


######################################Asset Overview##############################################

class LiquidationMetrics(BaseModel):
    total_volume: float = Field(..., alias="total_liquidation")
    largest_single: float = Field(..., alias="largest_liquidation") 
    long_volume: float = Field(..., alias="total_long_liquidation")
    short_volume: float = Field(..., alias="total_short_liquidation")
    time_window: str = Field(default="7D", alias="time_window")

    @validator('total_volume', 'largest_single')
    def non_negative_values(cls, value):
        if value < 0:
            raise ValueError("Value must be non-negative")
        return value


class FundingRate(BaseModel):
    timestamp: datetime = Field(..., alias="time")
    rate: float = Field(..., alias="premium")
    annual_rate: float = Field(..., alias="fundingRate")

    # @validator('annual_rate')
    # def non_negative_values(cls, value):
    #     if value < 0:
    #         raise ValueError("annual_rate must be non-negative")
    #     return value

class AssetMetrics(BaseModel):
    asset: str = Field(..., alias="Asset")
    open_interest_coverage: float = Field(..., alias="OI Coverage")
    total_notional: float = Field(..., alias="Total Notional")
    majority_side: str = Field(..., alias="Majority Side")
    minority_side: str = Field(..., alias="Minority Side")
    ls_ratio: float = Field(..., alias="L/S Ratio")
    majority_notional: float = Field(..., alias="Majority Side Notional")
    majority_pnl_status: str = Field(..., alias="Majority Side P/L")
    minority_notional: float = Field(..., alias="Minority Side Notional")
    minority_pnl_status: str = Field(..., alias="Minority Side P/L")
    traders_long: int = Field(..., alias="Number Long")
    traders_short: int = Field(..., alias="Number Short")
    open_interest: float = Field(..., alias="Open Interest")
    liquidation_metrics: Optional[LiquidationMetrics] = Field(..., alias="Liquidation_Metrics")
    funding_history: Optional[List[FundingRate]] = Field(..., alias="Funding_History")
    timestamp: Optional[datetime] = Field(..., alias="Timestamp")
    base_currency: str = Field(default="USD")

    @validator('majority_side', 'minority_side')
    def validate_pnl_status(cls, value):
        valid_values = ["LONG", "SHORT"]
        if value not in valid_values:
            raise ValueError(f"PnL status must be one of {valid_values}")
        return value

    @validator('ls_ratio', 'open_interest_coverage', 'total_notional', 'majority_notional', 'minority_notional', 'open_interest')
    def non_negative(cls, value):
        if value < 0:
            raise ValueError("Value must be non-negative")
        return value


####################################Liquidation Heatmap / Distribution#############################

class LiqDistributionPoint(BaseModel):
    price: float = Field(..., description="USD price level")
    long_liquidations: float = Field(..., description="Volume of long liq at this price")
    short_liquidations: float = Field(..., description="Volume of short liq at this price")
    cumulative_longs: float = Field(..., description="Cumulative long liq up to this price level")
    cumulative_shorts: float = Field(..., description="Cumulative short liq up to this price level")

class LiquidationDistributionData(BaseModel):
    asset: str
    distribution: List[LiqDistributionPoint] = Field(..., description="List of distribution entries")
    timestamp: datetime
    update_interval: int = Field(..., description="Refresh rate in seconds")
    base_currency: str = "USD"
    precision: int = Field(default=2, description="Decimal places for amounts")

