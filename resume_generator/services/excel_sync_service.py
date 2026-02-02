"""
Excel Sync Service - Manages syncing between Excel and local JSON cache
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ExcelSyncService:
    """Service to cache Excel data and track sync status"""
    
    def __init__(self, cache_file: str = 'data/excel_cache.json'):
        """Initialize sync service with cache file path"""
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
    def generate_unique_id(self) -> str:
        """Generate a unique ID for Excel row"""
        return f"JOB-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    def load_cache(self) -> Dict:
        """Load cached Excel data from JSON file"""
        if not self.cache_file.exists():
            return {
                'last_sync': None,
                'jobs': {},
                'metadata': {
                    'total_synced': 0,
                    'last_excel_modified': None
                }
            }
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {
                'last_sync': None,
                'jobs': {},
                'metadata': {
                    'total_synced': 0,
                    'last_excel_modified': None
                }
            }
    
    def save_cache(self, cache_data: Dict) -> bool:
        """Save cache data to JSON file"""
        try:
            cache_data['last_sync'] = datetime.now().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            return True
        except IOError as e:
            print(f"Error saving cache: {e}")
            return False
    
    def sync_excel_data(self, excel_data: List[Dict]) -> Dict:
        """
        Sync Excel data with cache
        
        Args:
            excel_data: List of job dictionaries from Excel
            
        Returns:
            Dictionary with sync statistics and updated data
        """
        cache = self.load_cache()
        stats = {
            'new': 0,
            'updated': 0,
            'unchanged': 0,
            'total': len(excel_data)
        }
        
        updated_jobs = []
        
        for job_data in excel_data:
            # Get or generate unique_id
            unique_id = job_data.get('unique_id')
            
            if not unique_id or unique_id == 'nan' or str(unique_id).strip() == '':
                # Generate new unique ID for this row
                unique_id = self.generate_unique_id()
                job_data['unique_id'] = unique_id
                stats['new'] += 1
            else:
                unique_id = str(unique_id).strip()
                job_data['unique_id'] = unique_id
                
                # Check if job exists in cache
                if unique_id in cache['jobs']:
                    # Compare with cached version
                    cached_job = cache['jobs'][unique_id]
                    if self._has_changes(cached_job, job_data):
                        stats['updated'] += 1
                    else:
                        stats['unchanged'] += 1
                else:
                    stats['new'] += 1
            
            # Update cache
            cache['jobs'][unique_id] = {
                **job_data,
                'last_synced': datetime.now().isoformat()
            }
            updated_jobs.append(job_data)
        
        # Update metadata
        cache['metadata']['total_synced'] = len(cache['jobs'])
        cache['metadata']['last_excel_modified'] = datetime.now().isoformat()
        
        # Save cache
        self.save_cache(cache)
        
        return {
            'success': True,
            'stats': stats,
            'jobs': updated_jobs,
            'cache_file': str(self.cache_file)
        }
    
    def _has_changes(self, cached_job: Dict, new_job: Dict) -> bool:
        """Check if job data has changed"""
        compare_fields = [
            'job_url', 'job_description', 'additional_instructions',
            'generate_resume', 'generate_cover_letter', 'company_name'
        ]
        
        for field in compare_fields:
            if str(cached_job.get(field, '')).strip() != str(new_job.get(field, '')).strip():
                return True
        
        return False
    
    def get_job_by_id(self, unique_id: str) -> Optional[Dict]:
        """Get job from cache by unique ID"""
        cache = self.load_cache()
        return cache['jobs'].get(unique_id)
    
    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs from cache"""
        cache = self.load_cache()
        return list(cache['jobs'].values())
    
    def get_sync_stats(self) -> Dict:
        """Get sync statistics"""
        cache = self.load_cache()
        return {
            'total_jobs': len(cache['jobs']),
            'last_sync': cache.get('last_sync'),
            'last_excel_modified': cache['metadata'].get('last_excel_modified'),
            'cache_file': str(self.cache_file),
            'cache_exists': self.cache_file.exists()
        }
    
    def update_job_status(self, unique_id: str, status_updates: Dict) -> bool:
        """
        Update job status in cache
        
        Args:
            unique_id: Unique job identifier
            status_updates: Dictionary with fields to update
        """
        cache = self.load_cache()
        
        if unique_id not in cache['jobs']:
            return False
        
        cache['jobs'][unique_id].update(status_updates)
        cache['jobs'][unique_id]['last_updated'] = datetime.now().isoformat()
        
        return self.save_cache(cache)
    
    def clear_cache(self) -> bool:
        """Clear the entire cache"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            return True
        except IOError:
            return False
    
    def export_to_json(self, output_file: str) -> bool:
        """Export cache to a different JSON file"""
        cache = self.load_cache()
        try:
            with open(output_file, 'w') as f:
                json.dump(cache, f, indent=2, default=str)
            return True
        except IOError:
            return False
