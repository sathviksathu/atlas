# Fraud Transaction Monitor

Application for detecting fraudulent transactions in CSV files using configurable rules.


## Fraud Detection Rules

The application includes several built-in fraud detection rules:

### Selected Rules and Reasoning behind them
1. **Suspicious Merchant Rule**:

- What the rule does? - This rule checks the names of the merchants in transaction and flags suspicious ones. 

- Why I chose this rule? - I have heard of scams in the past where users are lured into clickbaits of famous websites hiding malicious intent. For example, my friend almost paid Amaazon.com. 

- How to configure? - This rules accepts a parameter of `suspicious_merchants` which can be configured to whatever we wish. Ideally this would be a bunch of regexes I would match with and will be a list growing in real-time whenever users report certain merchants.

2. **Merchant Velocity Rule**:

- What the rule does? - This rule detects users making rapid transactions to the same merchant.

- Why I chose this rule? - Multiple repeated transactions to the same merchant within short period of time definitely reeks of suspicion.

- How to configure? - This rules accepts a parameter of `time_window_minutes` and `transaction_count` which can be configured to whatever we wish. For instance, we can flag someone making 10 transactions to the same merchant within a span of 20 minutes.

3. **Duplicate Transaction Rule**:

- What the rule does? - This rule flags users making transacting exactly same amount to same merchant within a close window time.

- Why I chose this rule? - Repeated transactions to the same merchant indicates either the person has been hacked by some program (transacting same amount to same merchant) or the user is knowingly/unknowingly making duplicate transactions.

- How to configure? - This rules accepts a parameter of `time_window_minutes` which can be configured to tighten the window over which the `<merchant>-<user>-<amount>` combo is verified for repetiton.


4. **Suspicious Frequency Rule**: Flags users with unusually high transaction frequency.

- What the rule does? - This rule flags users making transacting exactly same amount to same merchant within a close window time.

- Why I chose this rule? - This might indicate theft since bad actors would try and transact quickly as much as possible.

- How to configure? - This rules accepts a parameter of `frequency_threshold` which can be configured 
to set a threshold of what frequency should be flagged.

5. **Unusual Time Rule**: Detects transactions at unusual hours (late night/early morning) indicating theft.

- What the rule does? - This rule flags users making transactions at odd times. 

- Why I chose this rule? - Ideally I would have paired this with location information. This would mean flagging users who typically transact in the united states suddenly have a transaction in Africa for a very high amount. This would imply either stolen card or theft.

- How to configure? - This rules accepts a parameter of `start_hour` and `end_hour` which can be configured to frame the window of transaction and ideally also couple it with location.

## Custom Rules

You can create your own custom fraud detection rules by extending the `FraudTransactionRule` base class:

```python
class CustomRule(FraudTransactionRule):
    def __init__(self):
        super().__init__(
            description="Your custom rule description",
            code="CUSTOM_RULE"
        )
    
    def check(self, df: pd.DataFrame) -> pd.Series:
        # Your fraud detection logic here
        return pd.Series([False] * len(df), index=df.index)
```

Then add it to the service:
```python
fraud_monitor.add_rule(CustomRule())
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Open your browser and go to: `http://localhost:8000`

3. Enter the path to your CSV file in the web interface
Sample csvs have been provided in the `/data` folder, use `transactions_mini.csv` which contains 196 transactions

**NOTE:** `transactions_1m.csv` contains 1 million rows but I have seen the app hang sometimes with this. So PLEASE USE IT WITH CAUTION.

4. Click "Analyze Transactions" to run fraud detection

## CSV File Format

Your CSV file should contain transaction data with these columns:
- `user_id`: ID of the user making the transaction (numeric)
- `timestamp`: Transaction timestamp (datetime string)
- `merchant_name`: Name of the merchant receiving the payment (string)
- `amount`: Transaction amount (numeric)
- `is_fraud`: Original fraud flag (will be removed from output)

## API Endpoints

- `GET /`: Web interface
- `POST /analyze-fraud`: Analyze CSV file for fraud with pagination support

### Request Parameters for /analyze-fraud:
- `file_path`: Path to the CSV file (required)
- `page`: Page number for pagination (default: 1)
- `page_size`: Number of transactions per page (default: 15)

### Response includes:
- Transaction statistics
- Paginated fraudulent transactions with fraud codes
- Fraud code explanations
- Pagination information

## Architecture

- **main.py**: FastAPI application with web interface and API endpoints
- **fraud_transaction_rules.py**: Base rule class and concrete rule implementations
- **fraud_transaction_monitor_service.py**: Service for managing and applying fraud detection rules

## Sample screenshot of working app

![Fraud monitoring app on transactions_mini.csv](/resources/fraud_monitor_app.png)
