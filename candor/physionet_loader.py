"""
CandorHealth PhysioNet Data Loader

Loads real human PPG data from PhysioNet public databases.
This is actual physiological data, not synthetic.
"""

import numpy as np
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass

try:
    import wfdb
    WFDB_AVAILABLE = True
except ImportError:
    WFDB_AVAILABLE = False


@dataclass
class PPGRecord:
    """Container for a loaded PPG recording."""
    signal: np.ndarray
    sample_rate: int
    duration_sec: float
    subject_id: str
    activity: str  # sit, walk, run
    source: str
    channel_name: str
    
    def get_segment(self, start_sec: float, duration_sec: float) -> np.ndarray:
        """Extract a time segment from the recording."""
        start_idx = int(start_sec * self.sample_rate)
        end_idx = int((start_sec + duration_sec) * self.sample_rate)
        return self.signal[start_idx:end_idx]
    
    def normalize(self) -> np.ndarray:
        """Return signal normalized to 0-1 range."""
        sig = self.signal
        return (sig - sig.min()) / (sig.max() - sig.min() + 1e-10)


class PhysioNetPPGLoader:
    """
    Loader for real PPG data from PhysioNet.
    
    Currently supports:
    - Pulse Transit Time PPG Dataset (walking, running, sitting)
    - Wrist PPG During Exercise
    - BUT PPG Database
    """
    
    DATASETS = {
        'ptt-ppg': {
            'path': 'pulse-transit-time-ppg/1.1.0',
            'description': 'Pulse Transit Time PPG Dataset',
            'has_activities': True,
        },
        'wrist-exercise': {
            'path': 'wrist-ppg-during-exercise/1.0.0',
            'description': 'Wrist PPG During Exercise',
            'has_activities': True,
        },
    }
    
    def __init__(self):
        if not WFDB_AVAILABLE:
            raise ImportError("wfdb package required. Install with: pip install wfdb")
        
        self._cache = {}
    
    def list_records(self, dataset: str = 'ptt-ppg') -> List[str]:
        """List available records in a dataset."""
        if dataset not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset}. Available: {list(self.DATASETS.keys())}")
        
        path = self.DATASETS[dataset]['path']
        return wfdb.get_record_list(path.split('/')[0])
    
    def load_ptt_ppg(
        self, 
        subject: int = 1, 
        activity: str = 'walk',
        channel: int = 1,
        duration_sec: Optional[float] = None
    ) -> PPGRecord:
        """
        Load PPG from the Pulse Transit Time dataset.
        
        Args:
            subject: Subject number (1-12)
            activity: 'walk', 'run', or 'sit'
            channel: PPG channel (1-6, different sensor locations)
            duration_sec: Optional duration limit
            
        Returns:
            PPGRecord with real human PPG data
        """
        record_name = f"s{subject}_{activity}"
        pn_dir = self.DATASETS['ptt-ppg']['path']
        
        # Check cache
        cache_key = f"{record_name}_{channel}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load record
        record = wfdb.rdrecord(record_name, pn_dir=pn_dir)
        
        # Find the PPG channel (pleth_1 through pleth_6)
        channel_name = f"pleth_{channel}"
        try:
            ppg_idx = record.sig_name.index(channel_name)
        except ValueError:
            # Try alternate naming
            for i, name in enumerate(record.sig_name):
                if 'pleth' in name.lower():
                    ppg_idx = i
                    channel_name = name
                    break
            else:
                raise ValueError(f"No PPG channel found in record {record_name}")
        
        # Extract signal
        signal = record.p_signal[:, ppg_idx]
        
        if duration_sec is not None:
            signal = signal[:int(duration_sec * record.fs)]
        
        ppg_record = PPGRecord(
            signal=signal,
            sample_rate=record.fs,
            duration_sec=len(signal) / record.fs,
            subject_id=f"S{subject}",
            activity=activity,
            source="PhysioNet PTT-PPG",
            channel_name=channel_name
        )
        
        self._cache[cache_key] = ppg_record
        return ppg_record
    
    def load_random_segment(
        self,
        duration_sec: float = 10.0,
        activity: Optional[str] = None
    ) -> Tuple[np.ndarray, int, Dict]:
        """
        Load a random segment of real PPG data.
        
        Args:
            duration_sec: Desired segment duration
            activity: Optional activity filter ('walk', 'run', 'sit')
            
        Returns:
            signal: Normalized PPG signal
            sample_rate: Sample rate in Hz
            metadata: Dict with source information
        """
        # Random subject (1-12) and channel (1-6)
        subject = np.random.randint(1, 13)
        channel = np.random.randint(1, 7)
        
        if activity is None:
            activity = np.random.choice(['walk', 'run', 'sit'])
        
        try:
            record = self.load_ptt_ppg(
                subject=subject,
                activity=activity,
                channel=channel,
                duration_sec=duration_sec + 10  # Load extra for random offset
            )
            
            # Random start point (leave buffer at end)
            max_start = max(0, record.duration_sec - duration_sec - 1)
            start = np.random.uniform(0, max_start)
            
            segment = record.get_segment(start, duration_sec)
            
            # Normalize
            segment = (segment - segment.min()) / (segment.max() - segment.min() + 1e-10)
            
            metadata = {
                'source': record.source,
                'subject': record.subject_id,
                'activity': record.activity,
                'channel': record.channel_name,
                'sample_rate': record.sample_rate,
                'segment_start': start,
            }
            
            return segment, record.sample_rate, metadata
            
        except Exception as e:
            # Fallback if specific record not available
            raise RuntimeError(f"Failed to load PPG data: {e}")


def load_real_ppg(duration_sec: float = 10.0, activity: str = 'walk') -> Tuple[np.ndarray, int, Dict]:
    """
    Convenience function to load real PPG data.
    
    Returns:
        signal: Normalized PPG signal (0-1)
        sample_rate: Sample rate in Hz
        metadata: Source information
    """
    loader = PhysioNetPPGLoader()
    return loader.load_random_segment(duration_sec=duration_sec, activity=activity)


# Test function
if __name__ == "__main__":
    print("Testing PhysioNet PPG Loader...")
    
    signal, sr, meta = load_real_ppg(duration_sec=10.0, activity='walk')
    
    print(f"Loaded {len(signal)} samples at {sr} Hz")
    print(f"Duration: {len(signal)/sr:.1f} seconds")
    print(f"Source: {meta['source']}")
    print(f"Subject: {meta['subject']}")
    print(f"Activity: {meta['activity']}")
    print("✓ Real PPG data loaded successfully!")
