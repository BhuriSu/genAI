# model/visualization/charts.py
import plotly.graph_objects as go
from typing import List, Dict, Any
from ..config import VisualizationConfig

class ChartGenerator:
    def __init__(self, config: VisualizationConfig):
        self.config = config
    
    def create_line_chart(self, data: Dict[str, List[Any]], title: str) -> go.Figure:
        fig = go.Figure()
        
        for key, values in data.items():
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(values))),
                    y=values,
                    name=key,
                    mode='lines+markers'
                )
            )
        
        fig.update_layout(
            title=title,
            template="plotly_dark" if self.config.theme == "dark" else "plotly_white",
            showlegend=True
        )
        
        return fig
    
    def create_candlestick_chart(self, data: Dict[str, List[float]], title: str) -> go.Figure:
        fig = go.Figure(data=[
            go.Candlestick(
                x=data['dates'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close']
            )
        ])
        
        fig.update_layout(
            title=title,
            template="plotly_dark" if self.config.theme == "dark" else "plotly_white"
        )
        
        return fig