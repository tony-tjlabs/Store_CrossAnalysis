"""
Cache Loader for Pre-computed Conversion Analysis
Loads pre-processed data for fast web deployment
"""
import json
from pathlib import Path
from typing import Dict, Optional
import pandas as pd


class CacheLoader:
    """Load pre-computed conversion analysis cache"""
    
    def __init__(self, cache_folder: str = "Cache"):
        """
        Args:
            cache_folder: Path to cache folder containing pre-computed results
        """
        self.cache_folder = Path(cache_folder)
        self.cache_file = self.cache_folder / "conversion_analysis_cache.json"
        self.data: Optional[Dict] = None
        
    def load_cache(self) -> bool:
        """
        Load cache data from file
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading cache: {e}")
            return False
    
    def get_available_stores(self):
        """Get list of available store names"""
        if self.data is None:
            return []
        return list(self.data.keys())
    
    def get_store_profile(self, store_name: str) -> Dict:
        """Get store profile information"""
        if self.data is None or store_name not in self.data:
            return {}
        return self.data[store_name].get('profile', {})
    
    def get_aggregated_stats(self, store_name: str) -> Dict:
        """Get aggregated statistics for store"""
        if self.data is None or store_name not in self.data:
            return {}
        return self.data[store_name].get('aggregated_stats', {})
    
    def get_daily_results(self, store_name: str) -> list:
        """Get daily results for store"""
        if self.data is None or store_name not in self.data:
            return []
        return self.data[store_name].get('daily_results', [])
    
    def get_hourly_pattern(self, store_name: str) -> pd.DataFrame:
        """Get hourly pattern as DataFrame"""
        stats = self.get_aggregated_stats(store_name)
        if not stats:
            return pd.DataFrame()
        
        hourly_data = stats.get('hourly_pattern', [])
        return pd.DataFrame(hourly_data)
    
    def get_weekday_pattern(self, store_name: str) -> pd.DataFrame:
        """Get weekday pattern as DataFrame"""
        stats = self.get_aggregated_stats(store_name)
        if not stats:
            return pd.DataFrame()
        
        weekday_data = stats.get('weekday_pattern', [])
        return pd.DataFrame(weekday_data)
    
    def compare_stores(self, store_names: list) -> Dict:
        """
        Compare multiple stores
        
        Returns:
            Dict with comparison data
        """
        if self.data is None:
            return {}
        
        comparison = {
            'stores': [],
            'conversion_rates': [],
            'avg_visits': [],
            'avg_traffic': [],
            'location_types': [],
            'total_days': []
        }
        
        for store_name in store_names:
            if store_name not in self.data:
                continue
            
            stats = self.get_aggregated_stats(store_name)
            profile = self.get_store_profile(store_name)
            
            if not stats:
                continue
            
            overall = stats.get('overall', {})
            
            comparison['stores'].append(store_name)
            comparison['conversion_rates'].append(overall.get('avg_conversion_rate', 0) * 100)
            comparison['avg_visits'].append(overall.get('avg_visit_count', 0))
            comparison['avg_traffic'].append(overall.get('avg_total_traffic', 0))
            comparison['location_types'].append(profile.get('type', 'Unknown'))
            comparison['total_days'].append(overall.get('total_days', 0))
        
        return comparison
    
    def get_peak_hours(self, store_name: str) -> Dict:
        """Get peak hours for store"""
        stats = self.get_aggregated_stats(store_name)
        if not stats:
            return {}
        
        return {
            'peak_traffic_hour': stats.get('most_common_peak_traffic_hour', 0),
            'peak_visit_hour': stats.get('most_common_peak_visit_hour', 0),
            'peak_conversion_hour': stats.get('most_common_peak_conversion_hour', 0)
        }
