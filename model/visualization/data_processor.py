# model/visualization/data_processor.py

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..config import VisualizationConfig

class FinancialDataProcessor:
    def __init__(self, config: VisualizationConfig):
        self.config = config

    async def process_timeseries_data(
        self,
        data: List[Dict[str, Any]],
        time_column: str = 'timestamp',
        value_columns: Optional[List[str]] = None,
        aggregation: str = 'mean'
    ) -> Dict[str, List[Any]]:
        """
        Process time series financial data for visualization.
        
        Args:
            data: List of dictionaries containing financial data
            time_column: Name of the timestamp column
            value_columns: List of columns to process
            aggregation: Aggregation method ('mean', 'sum', 'max', 'min')
            
        Returns:
            Processed data ready for visualization
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Validate timestamp column
            if time_column not in df.columns:
                raise ValueError(f"Time column '{time_column}' not found in data")
            
            # Convert timestamp strings to datetime
            df[time_column] = pd.to_datetime(df[time_column])
            
            # Sort by timestamp
            df = df.sort_values(time_column)
            
            # Select columns to process
            if not value_columns:
                value_columns = df.select_dtypes(include=[np.number]).columns.tolist()
                value_columns = [col for col in value_columns if col != time_column]
            
            # Validate value columns
            missing_columns = [col for col in value_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Columns not found in data: {missing_columns}")
            
            # Resample if needed
            if len(df) > self.config.max_data_points:
                df = await self._resample_timeseries(
                    df, 
                    time_column, 
                    value_columns,
                    aggregation
                )
            
            # Prepare result
            result = {
                'dates': df[time_column].tolist(),
                'values': {}
            }
            
            for col in value_columns:
                result['values'][col] = {
                    'data': df[col].tolist(),
                    'stats': {
                        'mean': float(df[col].mean()),
                        'std': float(df[col].std()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max())
                    }
                }
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error processing time series data: {str(e)}")

    async def process_ohlcv_data(
        self,
        data: List[Dict[str, Any]],
        time_column: str = 'timestamp'
    ) -> Dict[str, List[float]]:
        """
        Process OHLCV (Open-High-Low-Close-Volume) data for candlestick charts.
        """
        try:
            df = pd.DataFrame(data)
            
            # Validate required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert timestamp
            df[time_column] = pd.to_datetime(df[time_column])
            df = df.sort_values(time_column)
            
            # Resample if needed
            if len(df) > self.config.max_data_points:
                df = await self._resample_ohlcv(df, time_column)
            
            # Calculate additional technical indicators
            indicators = await self._calculate_technical_indicators(df)
            
            result = {
                'dates': df[time_column].tolist(),
                'candlesticks': {
                    'open': df['open'].tolist(),
                    'high': df['high'].tolist(),
                    'low': df['low'].tolist(),
                    'close': df['close'].tolist(),
                    'volume': df['volume'].tolist()
                },
                'indicators': indicators,
                'stats': await self._calculate_ohlcv_stats(df)
            }
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error processing OHLCV data: {str(e)}")

    async def _resample_timeseries(
        self,
        df: pd.DataFrame,
        time_column: str,
        value_columns: List[str],
        aggregation: str
    ) -> pd.DataFrame:
        """
        Resample time series data intelligently.
        """
        # Calculate appropriate interval
        total_duration = df[time_column].max() - df[time_column].min()
        target_points = self.config.max_data_points
        
        # Set index for resampling
        df = df.set_index(time_column)
        
        # Determine resampling rule
        if total_duration < timedelta(hours=1):
            rule = f"{int(total_duration.total_seconds() / target_points)}S"
        elif total_duration < timedelta(days=1):
            rule = f"{int(total_duration.total_seconds() / 3600 / target_points)}H"
        elif total_duration < timedelta(weeks=4):
            rule = f"{int(total_duration.days / target_points)}D"
        else:
            rule = f"{int(total_duration.days / 7 / target_points)}W"
        
        # Apply resampling with specified aggregation
        agg_dict = {col: aggregation for col in value_columns}
        df = df[value_columns].resample(rule).agg(agg_dict)
        
        return df.reset_index()

    async def _resample_ohlcv(
        self,
        df: pd.DataFrame,
        time_column: str
    ) -> pd.DataFrame:
        """
        Resample OHLCV data preserving candlestick integrity.
        """
        df = df.set_index(time_column)
        
        # Calculate appropriate interval
        total_duration = df.index.max() - df.index.min()
        target_points = self.config.max_data_points
        
        # Determine resampling rule
        if total_duration < timedelta(hours=1):
            rule = f"{int(total_duration.total_seconds() / target_points)}S"
        elif total_duration < timedelta(days=1):
            rule = f"{int(total_duration.total_seconds() / 3600 / target_points)}H"
        else:
            rule = f"{int(total_duration.days / target_points)}D"
        
        # Resample OHLCV
        resampled = pd.DataFrame({
            'open': df['open'].resample(rule).first(),
            'high': df['high'].resample(rule).max(),
            'low': df['low'].resample(rule).min(),
            'close': df['close'].resample(rule).last(),
            'volume': df['volume'].resample(rule).sum()
        })
        
        return resampled.reset_index()

    async def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """
        Calculate various technical indicators for the OHLCV data.
        """
        indicators = {}
        
        # Moving Averages
        for period in [5, 10, 20, 50]:
            ma = df['close'].rolling(window=period).mean()
            indicators[f'MA{period}'] = ma.tolist()
        
        # Relative Strength Index (RSI)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['RSI'] = rsi.tolist()
        
        # Bollinger Bands
        ma20 = df['close'].rolling(window=20).mean()
        std20 = df['close'].rolling(window=20).std()
        indicators['BB_upper'] = (ma20 + (std20 * 2)).tolist()
        indicators['BB_lower'] = (ma20 - (std20 * 2)).tolist()
        indicators['BB_middle'] = ma20.tolist()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        indicators['MACD'] = macd.tolist()
        indicators['MACD_signal'] = signal.tolist()
        indicators['MACD_histogram'] = (macd - signal).tolist()
        
        return indicators

    async def _calculate_ohlcv_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate various statistics for OHLCV data.
        """
        returns = df['close'].pct_change()
        log_returns = np.log(df['close'] / df['close'].shift(1))
        
        stats = {
            'summary': {
                'start_date': df.index.min().isoformat(),
                'end_date': df.index.max().isoformat(),
                'trading_days': len(df),
                'current_price': float(df['close'].iloc[-1]),
                'volume_total': float(df['volume'].sum()),
                'volume_avg': float(df['volume'].mean())
            },
            'price_stats': {
                'high': float(df['high'].max()),
                'low': float(df['low'].min()),
                'mean': float(df['close'].mean()),
                'std': float(df['close'].std())
            },
            'returns': {
                'total_return': float(((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100),
                'daily_returns_mean': float(returns.mean() * 100),
                'daily_returns_std': float(returns.std() * 100),
                'sharpe_ratio': float(returns.mean() / returns.std() * np.sqrt(252)),
                'volatility_annualized': float(log_returns.std() * np.sqrt(252) * 100)
            }
        }
        
        return stats