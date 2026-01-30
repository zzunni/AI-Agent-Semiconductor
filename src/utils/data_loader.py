"""
Data loader for wafer data and proxy mappings

Works with both mock data (for development) and real data (from STEP teams)
"""

import pandas as pd
import os
from typing import Dict, Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DataLoader:
    """
    Load and cache wafer data

    Usage:
        loader = DataLoader()
        step1_df = loader.load_step1_data()
        wafer = loader.get_wafer_by_id("W0001")
    """

    def __init__(self, data_dir: str = "data/inputs"):
        """
        Initialize data loader

        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = data_dir

        # Cache
        self._step1_data = None
        self._wm811k_proxy = None
        self._carinthia_proxy = None

        # Check if mock data exists
        self._check_data_availability()

    def _check_data_availability(self):
        """Check if required data files exist"""
        required_files = [
            'step1_data.csv',
            'wm811k_proxy.csv',
            'carinthia_proxy.csv'
        ]

        for filename in required_files:
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                print(f"⚠️  Warning: {filename} not found")
                print(f"   Run: python scripts/generate_mock_data.py")

    def load_step1_data(self) -> pd.DataFrame:
        """
        Load step1 wafer data

        Returns:
            DataFrame with columns:
                wafer_id, lot_id, recipe, chamber, timestamp,
                etch_rate, pressure, temperature, rf_power, gas_flow,
                sensor6-10
        """
        if self._step1_data is None:
            filepath = os.path.join(self.data_dir, 'step1_data.csv')
            self._step1_data = pd.read_csv(filepath)
            print(f"✅ Loaded {len(self._step1_data)} wafers from step1_data.csv")

        return self._step1_data

    def load_wm811k_proxy(self) -> pd.DataFrame:
        """
        Load WM-811K proxy mapping

        Returns:
            DataFrame with columns:
                wafer_id, matched_wm811k_id, pattern_type,
                severity, defect_density, confidence
        """
        if self._wm811k_proxy is None:
            filepath = os.path.join(self.data_dir, 'wm811k_proxy.csv')
            self._wm811k_proxy = pd.read_csv(filepath)
            print(f"✅ Loaded {len(self._wm811k_proxy)} WM-811K mappings")

        return self._wm811k_proxy

    def load_carinthia_proxy(self) -> pd.DataFrame:
        """
        Load Carinthia proxy mapping

        Returns:
            DataFrame with columns:
                wafer_id, matched_carinthia_id, defect_type,
                defect_count, location_pattern, confidence
        """
        if self._carinthia_proxy is None:
            filepath = os.path.join(self.data_dir, 'carinthia_proxy.csv')
            self._carinthia_proxy = pd.read_csv(filepath)
            print(f"✅ Loaded {len(self._carinthia_proxy)} Carinthia mappings")

        return self._carinthia_proxy

    def get_wafer_by_id(self, wafer_id: str) -> Optional[Dict]:
        """
        Get single wafer data by ID

        Args:
            wafer_id: Wafer ID (e.g., "W0001")

        Returns:
            Dictionary with wafer data, or None if not found
        """
        df = self.load_step1_data()
        wafer_row = df[df['wafer_id'] == wafer_id]

        if len(wafer_row) == 0:
            return None

        return wafer_row.iloc[0].to_dict()

    def get_all_wafer_ids(self) -> list:
        """
        Get list of all wafer IDs in the dataset

        Returns:
            List of wafer IDs
        """
        df = self.load_step1_data()
        return df['wafer_id'].tolist()

    def get_lot_wafers(self, lot_id: str) -> pd.DataFrame:
        """
        Get all wafers in a lot

        Args:
            lot_id: Lot ID (e.g., "L001")

        Returns:
            DataFrame of wafers in the lot
        """
        df = self.load_step1_data()
        return df[df['lot_id'] == lot_id]

    def get_wafer_with_proxies(self, wafer_id: str) -> Dict:
        """
        Get wafer data with all proxy mappings

        Args:
            wafer_id: Wafer ID

        Returns:
            Dictionary with:
                - wafer_data: step1 data
                - wm811k: wafermap proxy
                - carinthia: SEM proxy
        """
        wafer_data = self.get_wafer_by_id(wafer_id)
        if wafer_data is None:
            return None

        # Get proxies
        wm811k_df = self.load_wm811k_proxy()
        carinthia_df = self.load_carinthia_proxy()

        wm811k_row = wm811k_df[wm811k_df['wafer_id'] == wafer_id]
        carinthia_row = carinthia_df[carinthia_df['wafer_id'] == wafer_id]

        return {
            'wafer_data': wafer_data,
            'wm811k': wm811k_row.iloc[0].to_dict() if len(wm811k_row) > 0 else None,
            'carinthia': carinthia_row.iloc[0].to_dict() if len(carinthia_row) > 0 else None
        }
