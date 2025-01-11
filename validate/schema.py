from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List

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
    total_volume: float = Field(..., description="Total liquidation volume in the chosen time window")
    largest_single: float = Field(..., description="Largest single liquidation amount")
    long_volume: float = Field(..., description="Long liquidation volume in the time window")
    short_volume: float = Field(..., description="Short liquidation volume in the time window")
    time_window: str = Field(..., description="Time range descriptor (e.g., '24h')")

    @validator('total_volume')
    def check_positive(cls, value):
        if value < 0:
            raise ValueError("total_volume must be >= 0")
        return value

class FundingRate(BaseModel):
    timestamp: datetime = Field(..., description="When this funding rate was recorded")
    rate: float = Field(..., description="Funding rate for this period (decimal, e.g. 0.01 = 1%)")
    annual_rate: float = Field(..., description="Annualized funding rate approximation")
   
    @validator('annual_rate')
    def annual_rate_nonnegative(cls, value):
        if value < 0:
            raise ValueError("annual_rate cannot be negative")
        return value

class AssetMetrics(BaseModel):
    asset: str = Field(..., description="Asset ticker, e.g., BTC, HYPE, etc.")
    open_interest_coverage: float = Field(..., description="Insurance coverage ratio (OI coverage)")
    total_notional: float = Field(..., description="Total notional in USD for this asset")
    majority_side: str = Field(..., description="Dominant position side, e.g., 'LONG' or 'SHORT'")
    ls_ratio: float = Field(..., description="Long/Short ratio for this asset")
    majority_notional: float = Field(..., description="Total notional on the majority side")
    majority_pnl_status: str = Field(..., description="Win/Loss for the majority side in aggregates")
    traders_long: int = Field(..., description="Number of users going long")
    traders_short: int = Field(..., description="Number of users going short")
    open_interest: float = Field(..., description="Aggregate open interest for this asset in USD")
    liquidation_metrics: LiquidationMetrics
    funding_history: List[FundingRate] = Field(..., description="List of historical funding data points")
    timestamp: datetime = Field(..., description="Data capture time")
    base_currency: str = Field(default="USD", description="Quote currency")
    
    @validator('ls_ratio')
    def ratio_within_range(cls, value):
        if value < 0:
            raise ValueError("ls_ratio must be >= 0")
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

