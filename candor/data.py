"""
CandorHealth Data Module - PhysioNet Integration

Provides utilities for loading real biosignal data from PhysioNet databases.
Requires credentialed access for restricted datasets.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

try:
    import wfdb
    WFDB_AVAILABLE = True
except ImportError:
    WFDB_AVAILABLE = False


@dataclass
class BiosignalRecord:
    """Container for a loaded biosignal."""
    signal: np.ndarray
    sample_rate: int
    duration_sec: float
    source: str
    record_name: str
    channel: str
    metadata: Dict[str, Any]
    
    def normalize(self) -> np.ndarray:
        """Return signal normalized to 0-1 range."""
        return (self.signal - self.signal.min()) / (self.signal.max() - self.signal.min())
    
    def slice_seconds(self, start: float, end: float) -> np.ndarray:
        """Extract a time slice from the signal."""
        start_idx = int(start * self.sample_rate)
        end_idx = int(end * self.sample_rate)
        return self.signal[start_idx:end_idx]


class PhysioNetLoader:
    """
    Loader for PhysioNet databases.
    
    Supported datasets (public):
    - BIDMC PPG and Respiration Dataset
    - MIT-BIH Arrhythmia Database
    - PTB Diagnostic ECG Database
    
    For credentialed datasets, ensure you've completed the
    PhysioNet credentialing process.
    """
    
    # Known dataset paths
    DATASETS = {
        'bidmc_ppg': 'bidmc-ppg-and-respiration-dataset/1.0.0',
        'mitdb': 'mitdb/1.0.0',
        'ptbdb': 'ptbdb/1.0.0',
        'mimic_ppg': 'mimic3wdb-matched/1.0',  # Requires credentials
    }
    
    def __init__(self):
        if not WFDB_AVAILABLE:
            raise ImportError(
                "wfdb package not installed. Run: pip install wfdb"
            )
    
    def load_bidmc_ppg(
        self, 
        record_num: int = 1,
        duration_sec: Optional[float] = None
    ) -> BiosignalRecord:
        """
        Load a PPG record from the BIDMC dataset.
        
        Args:
            record_num: Record number (1-53)
            duration_sec: Optional duration to load (None = full record)
            
        Returns:
            BiosignalRecord with PPG data
        """
        record_name = f'bidmc{record_num:02d}'
        pn_dir = self.DATASETS['bidmc_ppg']
        
        record = wfdb.rdrecord(record_name, pn_dir=pn_dir)
        
        # PPG is typically channel 1 (index 1)
        # Channel 0 is usually ECG or another signal
        ppg_channel = 1
        signal = record.p_signal[:, ppg_channel]
        
        if duration_sec is not None:
            signal = signal[:int(duration_sec * record.fs)]
        
        return BiosignalRecord(
            signal=signal,
            sample_rate=record.fs,
            duration_sec=len(signal) / record.fs,
            source='PhysioNet BIDMC',
            record_name=record_name,
            channel='PPG',
            metadata={
                'num_channels': record.n_sig,
                'signal_names': record.sig_name,
                'units': record.units,
            }
        )
    
    def load_mitdb_ecg(
        self,
        record_num: int = 100,
        duration_sec: Optional[float] = None
    ) -> BiosignalRecord:
        """
        Load an ECG record from the MIT-BIH Arrhythmia Database.
        
        Args:
            record_num: Record number (100-234, not all exist)
            duration_sec: Optional duration to load
            
        Returns:
            BiosignalRecord with ECG data
        """
        record_name = str(record_num)
        pn_dir = self.DATASETS['mitdb']
        
        record = wfdb.rdrecord(record_name, pn_dir=pn_dir)
        
        # Use first channel (MLII lead typically)
        signal = record.p_signal[:, 0]
        
        if duration_sec is not None:
            signal = signal[:int(duration_sec * record.fs)]
        
        return BiosignalRecord(
            signal=signal,
            sample_rate=record.fs,
            duration_sec=len(signal) / record.fs,
            source='PhysioNet MIT-BIH',
            record_name=record_name,
            channel=record.sig_name[0],
            metadata={
                'num_channels': record.n_sig,
                'signal_names': record.sig_name,
                'units': record.units,
            }
        )
    
    def list_available_records(self, dataset: str) -> list:
        """
        List available records in a dataset.
        
        Args:
            dataset: Dataset key (e.g., 'bidmc_ppg', 'mitdb')
            
        Returns:
            List of record names
        """
        if dataset not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset}. Available: {list(self.DATASETS.keys())}")
        
        return wfdb.get_record_list(self.DATASETS[dataset])


def load_sample_ppg(duration_sec: float = 10.0) -> Tuple[np.ndarray, int]:
    """
    Quick helper to load a sample PPG signal.
    
    Returns:
        signal: Normalized PPG signal (0-1 range)
        sample_rate: Sampling rate in Hz
    """
    loader = PhysioNetLoader()
    record = loader.load_bidmc_ppg(record_num=1, duration_sec=duration_sec)
    return record.normalize(), record.sample_rate
