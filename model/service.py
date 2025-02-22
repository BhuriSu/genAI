# model/service.py

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from .llm.inference import LLMInference
from .rag.pipeline import RAGPipeline
from .rag.retriever import SemanticRetriever
from .visualization.charts import ChartGenerator
from .visualization.data_processor import FinancialDataProcessor
from .config import LLMConfig, RAGConfig, VisualizationConfig

class FinancialAnalysisService:
    def __init__(
        self,
        llm: LLMInference,
        retriever: SemanticRetriever,
        chart_generator: ChartGenerator,
        data_processor: FinancialDataProcessor,
        rag_config: RAGConfig,
        viz_config: VisualizationConfig
    ):
        self.llm = llm
        self.retriever = retriever
        self.chart_generator = chart_generator
        self.data_processor = data_processor
        self.rag_config = rag_config
        self.viz_config = viz_config

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query and return analysis with visualizations.
        
        Args:
            query: User's question or request
            context: Optional context like date range, specific stocks, etc.
            
        Returns:
            Dictionary containing the answer, visualizations, and sources
        """
        try:
            # 1. Get relevant documents using RAG
            rag_results = await self.retriever.retrieve(
                query=query,
                filters=context.get('filters') if context else None
            )

            # 2. Process financial data if present
            financial_data = await self._extract_financial_data(rag_results)
            
            # 3. Generate visualizations if needed
            visualizations = await self._generate_visualizations(
                query, financial_data, context
            ) if financial_data else None

            # 4. Prepare context for LLM
            llm_context = await self._prepare_llm_context(
                query, rag_results, financial_data, visualizations
            )

            # 5. Generate LLM response
            llm_response = await self._generate_llm_response(llm_context)

            return {
                "answer": llm_response,
                "visualizations": visualizations,
                "sources": self._extract_sources(rag_results),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "query_type": self._determine_query_type(query),
                    "data_freshness": self._calculate_data_freshness(rag_results)
                }
            }

        except Exception as e:
            # Log error and return user-friendly message
            error_msg = f"Error processing query: {str(e)}"
            # You should log this error properly in production
            print(error_msg)  
            return {
                "error": "An error occurred while processing your request.",
                "details": str(e)
            }

    async def _extract_financial_data(
        self, 
        rag_results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Extract and structure financial data from RAG results."""
        try:
            financial_data = []
            
            for result in rag_results:
                if 'financial_data' in result.get('meta', {}):
                    financial_data.extend(result['meta']['financial_data'])
                    
            if not financial_data:
                return None
                
            # Determine if it's OHLCV or time series data
            if all(self._is_ohlcv_data(item) for item in financial_data):
                return await self.data_processor.process_ohlcv_data(financial_data)
            else:
                return await self.data_processor.process_timeseries_data(financial_data)
                
        except Exception as e:
            print(f"Error extracting financial data: {str(e)}")
            return None

    async def _generate_visualizations(
        self,
        query: str,
        financial_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate appropriate visualizations based on data and query."""
        visualizations = {}
        
        # Determine visualization types needed
        viz_types = self._determine_visualization_types(query, financial_data)
        
        for viz_type in viz_types:
            if viz_type == 'candlestick':
                visualizations['price_chart'] = self.chart_generator.create_candlestick_chart(
                    financial_data['candlesticks'],
                    title="Price History"
                )
            elif viz_type == 'line':
                for metric, values in financial_data['values'].items():
                    visualizations[f'{metric}_chart'] = self.chart_generator.create_line_chart(
                        {metric: values['data']},
                        title=f"{metric.replace('_', ' ').title()} Trend"
                    )
            elif viz_type == 'technical':
                visualizations['technical_indicators'] = self.chart_generator.create_technical_chart(
                    financial_data['indicators'],
                    title="Technical Indicators"
                )

        return visualizations

    async def _prepare_llm_context(
        self,
        query: str,
        rag_results: List[Dict[str, Any]],
        financial_data: Optional[Dict[str, Any]] = None,
        visualizations: Optional[Dict[str, Any]] = None
    ) -> str:
        """Prepare context for LLM including relevant information and visualization descriptions."""
        context_parts = []
        
        # Add retrieved documents
        context_parts.append("Retrieved Information:")
        for result in rag_results:
            context_parts.append(result['content'])
        
        # Add financial data summary if available
        if financial_data:
            context_parts.append("\nFinancial Data Summary:")
            context_parts.append(self._summarize_financial_data(financial_data))
        
        # Add visualization descriptions if available
        if visualizations:
            context_parts.append("\nVisualizations Generated:")
            context_parts.append(self._describe_visualizations(visualizations))
        
        # Add the original query
        context_parts.append(f"\nUser Query: {query}")
        
        return "\n".join(context_parts)

    async def _generate_llm_response(self, context: str) -> str:
        """Generate LLM response based on context."""
        # Create a prompt that encourages detailed analysis
        prompt = f"""Based on the following context, provide a detailed financial analysis. 
Include specific insights from the data and references to any visualizations.

{context}

Provide a comprehensive analysis with:
1. Direct answer to the query
2. Key insights from the data
3. Relevant trends or patterns
4. References to specific visualizations
5. Any important caveats or limitations

Analysis:"""

        return await self.llm.generate_response(prompt)

    def _determine_query_type(self, query: str) -> str:
        """Determine the type of financial query."""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ['price', 'stock', 'ohlc', 'candlestick']):
            return 'price_analysis'
        elif any(term in query_lower for term in ['trend', 'compare', 'correlation']):
            return 'trend_analysis'
        elif any(term in query_lower for term in ['forecast', 'predict', 'future']):
            return 'prediction'
        return 'general_analysis'

    def _calculate_data_freshness(self, rag_results: List[Dict[str, Any]]) -> str:
        """Calculate how recent the data is."""
        dates = []
        for result in rag_results:
            if 'date' in result.get('meta', {}):
                dates.append(datetime.fromisoformat(result['meta']['date']))
        
        if not dates:
            return "unknown"
            
        most_recent = max(dates)
        age = datetime.now() - most_recent
        
        if age.days < 1:
            return "very_fresh"
        elif age.days < 7:
            return "fresh"
        elif age.days < 30:
            return "recent"
        else:
            return "historical"

    def _is_ohlcv_data(self, item: Dict[str, Any]) -> bool:
        """Check if data item contains OHLCV fields."""
        required_fields = {'open', 'high', 'low', 'close', 'volume'}
        return all(field in item for field in required_fields)

    def _summarize_financial_data(self, data: Dict[str, Any]) -> str:
        """Create a text summary of financial data."""
        if 'candlesticks' in data:
            return self._summarize_ohlcv_data(data)
        return self._summarize_timeseries_data(data)

    def _describe_visualizations(self, visualizations: Dict[str, Any]) -> str:
        """Create text descriptions of generated visualizations."""
        descriptions = []
        for name, viz in visualizations.items():
            viz_type = name.split('_')[-1]
            descriptions.append(f"- {name}: {viz_type} chart showing {name.replace('_', ' ')}")
        return "\n".join(descriptions)

    def _summarize_ohlcv_data(self, data: Dict[str, Any]) -> str:
        """Summarize OHLCV data."""
        close_prices = data['candlesticks']['close']
        return f"Price data available from {data['dates'][0]} to {data['dates'][-1]}. "
               f"Price range: ${min(close_prices):.2f} - ${max(close_prices):.2f}"

    def _summarize_timeseries_data(self, data: Dict[str, Any]) -> str:
        """Summarize time series data."""
        metrics = list(data['values'].keys())
        return f"Time series data for {', '.join(metrics)} "
               f"from {data['dates'][0]} to {data['dates'][-1]}"

    def _extract_sources(self, rag_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract source information from RAG results."""
        sources = []
        for result in rag_results:
            if 'meta' in result:
                source = {
                    'title': result['meta'].get('title', 'Untitled'),
                    'date': result['meta'].get('date', 'Unknown date'),
                    'source': result['meta'].get('source', 'Unknown source'),
                    'relevance': f"{result.get('similarity', 0):.2%}"
                }
                sources.append(source)
        return sources