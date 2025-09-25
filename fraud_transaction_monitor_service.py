from typing import List, Dict, Any
import polars as pl
from fraud_transaction_rules import FraudTransactionRule
import logging

"""
Fraud Transaction Monitor Service
"""
class FraudTransactionMonitorService:
    """
    Service for monitoring and detecting fraudulent transactions.
    Supports configurable rules for fraud detection.
    """
    
    def __init__(self):
        self.rules: List[FraudTransactionRule] = []
        self.logger = logging.getLogger(__name__)
    
    def add_rule(self, rule: FraudTransactionRule) -> None:
        """
        Add a fraud detection rule to the service.
        
        Args:
            rule: FraudTransactionRule instance to add
        """
        self.rules.append(rule)
        self.logger.info(f"Added rule: {rule}")
    
    def remove_rule(self, rule_code: str) -> bool:
        """
        Remove a fraud detection rule by its code.
        
        Args:
            rule_code: Code of the rule to remove
            
        Returns:
            bool: True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.code == rule_code:
                removed_rule = self.rules.pop(i)
                self.logger.info(f"Removed rule: {removed_rule}")
                return True
        return False
    
    def get_rules(self) -> List[FraudTransactionRule]:
        """
        Get all configured rules.
        
        Returns:
            List of configured rules
        """
        return self.rules.copy()
    
    def analyze_transactions(self, file_path: str, page: int = 1, page_size: int = 15) -> Dict[str, Any]:
        """
        Analyze transactions in a CSV file for fraud.
        
        Args:
            file_path: Path to the CSV file containing transaction data
            page: Page number for pagination (1-based)
            page_size: Number of transactions per page
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Load the CSV file
            self.logger.info(f"Loading transactions from: {file_path}")
            df = pl.read_csv(file_path)
            
            self.logger.info(f"Loaded {len(df)} transactions")
            
            # Validate required columns
            self._validate_dataframe(df)
            
            # Apply all rules and get fraud codes
            fraud_flags, fraud_codes = self._apply_rules_with_codes(df)
            
            # Get fraudulent transactions with fraud codes
            fraudulent_df = df.filter(fraud_flags).with_columns(
                pl.Series("fraud_code", fraud_codes).filter(fraud_flags)
            )
            
            # Remove is_fraud column if it exists
            if 'is_fraud' in fraudulent_df.columns:
                fraudulent_df = fraudulent_df.drop('is_fraud')
            
            # Calculate statistics
            total_transactions = len(df)
            fraudulent_transactions = len(fraudulent_df)
            fraud_percentage = (fraudulent_transactions / total_transactions) if total_transactions > 0 else 0
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_df = fraudulent_df.slice(start_idx, page_size)
            
            # Convert fraudulent data to list of dictionaries for JSON serialization
            fraud_data = paginated_df.to_dicts() if len(paginated_df) > 0 else []
            
            # Get rule descriptions and fraud code explanations
            rules_applied = [rule.description for rule in self.rules]
            fraud_code_explanations = self._get_fraud_code_explanations()
            
            # Calculate pagination info
            total_pages = (fraudulent_transactions + page_size - 1) // page_size if fraudulent_transactions > 0 else 0
            
            result = {
                'total_transactions': total_transactions,
                'fraudulent_transactions': fraudulent_transactions,
                'fraud_percentage': fraud_percentage,
                'fraud_data': fraud_data,
                'rules_applied': rules_applied,
                'fraud_code_explanations': fraud_code_explanations,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                }
            }
            
            self.logger.info(f"Analysis complete: {fraudulent_transactions}/{total_transactions} fraudulent ({fraud_percentage:.2%})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing transactions: {str(e)}")
            raise
    
    def _validate_dataframe(self, df: pl.DataFrame) -> None:
        """
        Validate that the dataframe has the required structure for fraud detection.
        
        Args:
            df: Polars DataFrame to validate
            
        Raises:
            ValueError: If dataframe doesn't meet requirements
        """
        if len(df) == 0:
            raise ValueError("DataFrame is empty")
        
        # Check for common transaction columns
        common_columns = ['user_id', 'timestamp', 'merchant_name', 'amount']
        missing_columns = [col for col in common_columns if col not in df.columns]
        
        if missing_columns:
            self.logger.warning(f"Missing common columns: {missing_columns}")
            self.logger.warning("Some rules may not work properly")
        
        # Check for numeric amount column
        if 'amount' in df.columns:
            if not df['amount'].dtype.is_numeric():
                self.logger.warning("Amount column is not numeric, attempting conversion")
                try:
                    df = df.with_columns(pl.col('amount').cast(pl.Float64, strict=False))
                except Exception:
                    self.logger.error("Could not convert amount column to numeric")
    
    def _apply_rules_with_codes(self, df: pl.DataFrame) -> tuple[pl.Series, pl.Series]:
        """
        Apply all configured rules to detect fraudulent transactions and get fraud codes.
        
        Args:
            df: Polars DataFrame containing transaction data
            
        Returns:
            tuple: (Boolean series indicating fraudulent transactions, String series with fraud codes)
        """
        if not self.rules:
            self.logger.warning("No rules configured, returning no fraud flags")
            return pl.Series([False] * len(df)), pl.Series([""] * len(df))
        
        # Initialize fraud flags and codes
        fraud_flags = pl.Series([False] * len(df))
        fraud_codes = pl.Series([""] * len(df))
        
        # Apply each rule
        for rule in self.rules:
            try:
                self.logger.info(f"Applying rule: {rule.code}")
                rule_flags = rule.check(df)
                rule_codes = rule.get_fraud_codes(df)
                self.logger.info(f"Rule check complete!!!")
                # Combine flags (OR operation)
                fraud_flags = fraud_flags | rule_flags
                
                # Combine codes (concatenate with comma if multiple)
                for i in range(len(fraud_codes)):
                    if rule_flags[i]:
                        if fraud_codes[i]:
                            fraud_codes[i] = fraud_codes[i] + "," + rule_codes[i]
                        else:
                            fraud_codes[i] = rule_codes[i]
                
                fraud_count = rule_flags.sum()
                self.logger.info(f"Rule {rule.code} flagged {fraud_count} transactions")
                
            except Exception as e:
                self.logger.error(f"Error applying rule {rule.code}: {str(e)}")
                continue
        
        total_fraud = fraud_flags.sum()
        self.logger.info(f"Total fraudulent transactions detected: {total_fraud}")
        
        return fraud_flags, fraud_codes
    
    def _apply_rules(self, df: pl.DataFrame) -> pl.Series:
        """
        Apply all configured rules to detect fraudulent transactions.
        
        Args:
            df: Polars DataFrame containing transaction data
            
        Returns:
            pl.Series: Boolean series indicating fraudulent transactions
        """
        if not self.rules:
            self.logger.warning("No rules configured, returning no fraud flags")
            return pl.Series([False] * len(df))
        
        # Initialize fraud flags
        fraud_flags = pl.Series([False] * len(df))
        
        # Apply each rule
        for rule in self.rules:
            try:
                self.logger.info(f"Applying rule: {rule.code}")
                rule_flags = rule.check(df)
                
                # Combine with existing flags (OR operation)
                fraud_flags = fraud_flags | rule_flags
                
                fraud_count = rule_flags.sum()
                self.logger.info(f"Rule {rule.code} flagged {fraud_count} transactions")
                
            except Exception as e:
                self.logger.error(f"Error applying rule {rule.code}: {str(e)}")
                continue
        
        total_fraud = fraud_flags.sum()
        self.logger.info(f"Total fraudulent transactions detected: {total_fraud}")
        
        return fraud_flags

    def _get_fraud_code_explanations(self) -> Dict[str, str]:
        """
        Get friendly explanations for fraud codes.
        
        Returns:
            Dictionary mapping fraud codes to explanations
        """
        explanations = {
            "HIGH_AMOUNT": "Transaction amount is unusually high compared to typical transactions",
            "SUSPICIOUS_FREQUENCY": "User shows suspiciously high transaction frequency",
            "UNUSUAL_TIME": "Transaction occurred at unusual hours (late night/early morning)",
            "DUPLICATE_TRANSACTION": "Duplicate transaction detected within a short time window",
            "AMOUNT_VELOCITY": "Rapid increase in transaction amounts detected",
            "SUSPICIOUS_MERCHANT": "Transaction involves a merchant known for suspicious activity",
            "MERCHANT_VELOCITY": "User making rapid transactions to the same merchant"
        }
        
        # Only return explanations for rules that are actually configured
        configured_codes = {rule.code for rule in self.rules}
        return {code: explanation for code, explanation in explanations.items() if code in configured_codes}
    
    def clear_rules(self) -> None:
        """Remove all configured rules."""
        self.rules.clear()
        self.logger.info("Cleared all rules")
