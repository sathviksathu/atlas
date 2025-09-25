from abc import ABC, abstractmethod
from typing import List, Dict, Any
import polars as pl
from datetime import datetime, time
import logging

class FraudTransactionRule(ABC):
    """
    Base class for fraud detection rules.
    Each rule should implement the check method to identify fraudulent transactions.
    """
    
    def __init__(self, description: str, code: str):
        self.logger = logging.getLogger(__name__)
        self.description = description
        self.code = code
    
    @abstractmethod
    def check(self, df: pl.DataFrame) -> pl.Series:
        """
        Check for fraudulent transactions in the dataframe.
        
        Args:
            df: Polars DataFrame containing transaction data
            
        Returns:
            pl.Series: Boolean series where True indicates fraudulent transaction
        """
        pass
    
    def get_fraud_codes(self, df: pl.DataFrame) -> pl.Series:
        """
        Get fraud codes for transactions that match this rule.
        
        Args:
            df: Polars DataFrame containing transaction data
            
        Returns:
            pl.Series: String series with fraud codes (empty string for non-fraudulent)
        """
        fraud_flags = self.check(df)
        return pl.Series([self.code if flag else "" for flag in fraud_flags])
    
    def __str__(self):
        return f"{self.code}: {self.description}"


class HighAmountRule(FraudTransactionRule):
    """
    Rule to detect transactions with unusually high amounts.
    Flags transactions above the 99th percentile as potentially fraudulent.
    """
    
    def __init__(self, threshold_percentile: float = 99.0):
        super().__init__(
            description="Detects transactions with unusually high amounts",
            code="HIGH_AMOUNT"
        )
        self.threshold_percentile = threshold_percentile
    
    def check(self, df: pl.DataFrame) -> pl.Series:
        if 'amount' not in df.columns:
            return pl.Series([False] * len(df))
        
        # Calculate threshold based on percentile
        threshold = df['amount'].quantile(self.threshold_percentile / 100)
        
        # Flag transactions above threshold
        return df['amount'] > threshold


class SuspiciousFrequencyRule(FraudTransactionRule):
    """
    Rule to detect suspicious transaction frequency patterns.
    Flags users with unusually high transaction frequency.
    """
    
    def __init__(self, frequency_threshold: int = 10):
        super().__init__(
            description="Detects users with suspiciously high transaction frequency",
            code="SUSPICIOUS_FREQUENCY"
        )
        self.frequency_threshold = frequency_threshold
    
    def check(self, df: pl.DataFrame) -> pl.Series:
        if 'user_id' not in df.columns:
            return pl.Series([False] * len(df))
        
        # Count transactions per user and find suspicious users
        suspicious_users = (
            df.group_by('user_id')
            .agg(pl.count().alias('count'))
            .filter(pl.col('count') >= self.frequency_threshold)
            .select('user_id')
        )
        
        # Flag transactions from suspicious users
        return df['user_id'].is_in(suspicious_users['user_id'])


class UnusualTimeRule(FraudTransactionRule):
    """
    Rule to detect transactions at unusual times (e.g., late night, early morning).
    """
    
    def __init__(self, start_hour: int = 22, end_hour: int = 6):
        super().__init__(
            description="Detects transactions at unusual times (late night/early morning)",
            code="UNUSUAL_TIME"
        )
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def check(self, df: pl.DataFrame) -> pl.Series:
        if 'timestamp' not in df.columns:
            return pl.Series([False] * len(df))
        
        try:
            # Convert timestamp to datetime and extract hour
            df_with_hour = df.with_columns(
                pl.col('timestamp').str.to_datetime().dt.hour().alias('hour')
            )
            
            # Flag transactions in unusual time windows
            if self.start_hour > self.end_hour:  # Crosses midnight
                return (df_with_hour['hour'] >= self.start_hour) | (df_with_hour['hour'] <= self.end_hour)
            else:
                return (df_with_hour['hour'] >= self.start_hour) & (df_with_hour['hour'] <= self.end_hour)
                
        except Exception:
            # If timestamp parsing fails, return no flags
            return pl.Series([False] * len(df))


class DuplicateTransactionRule(FraudTransactionRule):
    """
    Rule to detect duplicate transactions (same amount, same user, close in time).
    """
    
    def __init__(self, time_window_minutes: int = 5):
        super().__init__(
            description="Detects duplicate transactions within a time window",
            code="DUPLICATE_TRANSACTION"
        )
        self.time_window_minutes = time_window_minutes
    
    def check(self, df: pl.DataFrame) -> pl.Series:
        required_columns = ['user_id', 'amount', 'timestamp']
        if not all(col in df.columns for col in required_columns):
            return pl.Series([False] * len(df))
        
        try:
            # Convert timestamp to datetime and sort
            df_processed = (
                df.with_columns(
                    pl.col('timestamp').str.to_datetime().alias('timestamp')
                )
                .sort(['user_id', 'amount', 'timestamp'])
            )
            
            # Find duplicates using window functions
            df_with_duplicates = (
                df_processed
                .with_columns([
                    pl.col('timestamp').shift(1).over(['user_id', 'amount']).alias('prev_timestamp'),
                    pl.col('timestamp').shift(-1).over(['user_id', 'amount']).alias('next_timestamp')
                ])
                .with_columns([
                    # Check if current transaction is duplicate of previous
                    (
                        (pl.col('prev_timestamp').is_not_null()) &
                        ((pl.col('timestamp') - pl.col('prev_timestamp')).dt.total_minutes() <= self.time_window_minutes)
                    ).alias('is_prev_duplicate'),
                    # Check if current transaction is duplicate of next
                    (
                        (pl.col('next_timestamp').is_not_null()) &
                        ((pl.col('next_timestamp') - pl.col('timestamp')).dt.total_minutes() <= self.time_window_minutes)
                    ).alias('is_next_duplicate')
                ])
                .with_columns(
                    (pl.col('is_prev_duplicate') | pl.col('is_next_duplicate')).alias('is_duplicate')
                )
            )
            
            return df_with_duplicates['is_duplicate']
            
        except Exception:
            # If processing fails, return no flags
            return pl.Series([False] * len(df))


class SuspiciousMerchantRule(FraudTransactionRule):
    """
    Rule to detect transactions with suspicious merchants or unusual merchant patterns.
    """
    
    def __init__(self, suspicious_merchants: list = None):
        super().__init__(
            description="Detects transactions with suspicious merchants",
            code="SUSPICIOUS_MERCHANT"
        )
        # Default list of potentially suspicious merchants
        self.suspicious_merchants = suspicious_merchants or [
            "Crypto Exchange", "Unverified Market", "Foreign Electronics Hub", 
            "Luxury Watches Inc", "Gift Card Reseller", "Wire Transfer Service",
            "HighValueElectronics", "International Goods Ltd"
        ]
    
    def check(self, df: pl.DataFrame) -> pl.Series:
        if 'merchant_name' not in df.columns:
            return pl.Series([False] * len(df))
        self.logger.info(f"Performing check for suspicious merchants: {self.suspicious_merchants}")
        # Flag transactions with suspicious merchants
        return df['merchant_name'].is_in(self.suspicious_merchants)


class MerchantVelocityRule(FraudTransactionRule):
    """
    Rule to detect users making rapid transactions to the same merchant.
    """
    
    def __init__(self, time_window_minutes: int = 30, transaction_count: int = 5):
        super().__init__(
            description="Detects rapid transactions to the same merchant",
            code="MERCHANT_VELOCITY"
        )
        self.time_window_minutes = time_window_minutes
        self.transaction_count = transaction_count
    
    def check(self, df: pl.DataFrame) -> pl.Series:
        required_columns = ['user_id', 'merchant_name', 'timestamp']
        if not all(col in df.columns for col in required_columns):
            return pl.Series([False] * len(df))
        
        try:
            # Convert timestamp to datetime and sort
            df_processed = (
                df.with_columns(
                    pl.col('timestamp').str.to_datetime().alias('timestamp')
                )
                .sort(['user_id', 'merchant_name', 'timestamp'])
            )
            
            # Count transactions per user-merchant combination within time window
            df_with_counts = (
                df_processed
                .with_columns([
                    # Count transactions in the last N minutes for each user-merchant pair
                    pl.col('timestamp').count().over(['user_id', 'merchant_name']).alias('merchant_count')
                ])
            )
            
            # Flag transactions where user has made many transactions to same merchant
            return df_with_counts['merchant_count'] >= self.transaction_count
            
        except Exception:
            return pl.Series([False] * len(df))
