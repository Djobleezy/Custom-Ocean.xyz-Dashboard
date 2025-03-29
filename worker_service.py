"""
Worker service module for managing workers data.
"""
import logging
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class WorkerService:
    """Service for retrieving and managing worker data."""
    
    def __init__(self):
        """Initialize the worker service."""
        self.worker_data_cache = None
        self.last_worker_data_update = None
        self.WORKER_DATA_CACHE_TIMEOUT = 60  # Cache worker data for 60 seconds
        self.dashboard_service = None  # Will be set by App.py during initialization
        self.sats_per_btc = 100_000_000  # Constant for conversion

    def set_dashboard_service(self, dashboard_service):
        """
        Set the dashboard service instance - to be called from App.py
        
        Args:
            dashboard_service (MiningDashboardService): The initialized dashboard service
        """
        self.dashboard_service = dashboard_service
        logging.info("Dashboard service connected to worker service")

    def generate_default_workers_data(self):
        """
        Generate default worker data when no metrics are available.
        
        Returns:
            dict: Default worker data structure
        """
        return {
            "workers": [],
            "workers_total": 0,
            "workers_online": 0,
            "workers_offline": 0,
            "total_hashrate": 0.0,
            "hashrate_unit": "TH/s",
            "total_earnings": 0.0,
            "daily_sats": 0,
            "avg_acceptance_rate": 0.0,
            "hashrate_history": [],
            "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
        }

    def get_workers_data(self, cached_metrics, force_refresh=False):
        """
        Get worker data with caching for better performance.
        
        Args:
            cached_metrics (dict): Cached metrics from the dashboard
            force_refresh (bool): Whether to force a refresh of cached data
                
        Returns:
            dict: Worker data
        """
        current_time = datetime.now().timestamp()
        
        # Return cached data if it's still fresh and not forced to refresh
        if not force_refresh and self.worker_data_cache and self.last_worker_data_update and \
        (current_time - self.last_worker_data_update) < self.WORKER_DATA_CACHE_TIMEOUT:
            # Even when using cached data, sync worker count with main dashboard
            if cached_metrics and cached_metrics.get("workers_hashing") is not None:
                self.sync_worker_counts_with_dashboard(self.worker_data_cache, cached_metrics)
            
            logging.info("Using cached worker data")
            return self.worker_data_cache
                
        try:
            # First try to get actual worker data from the dashboard service
            if self.dashboard_service:
                logging.info("Attempting to fetch real worker data from Ocean.xyz")
                real_worker_data = self.dashboard_service.get_worker_data()
                
                if real_worker_data and real_worker_data.get('workers') and len(real_worker_data['workers']) > 0:
                    # Validate that worker names are not just "Online" or "Offline"
                    valid_names = False
                    for worker in real_worker_data['workers']:
                        name = worker.get('name', '').lower()
                        if name and name not in ['online', 'offline', 'total', 'worker', 'status']:
                            valid_names = True
                            break
                    
                    if valid_names:
                        logging.info(f"Successfully retrieved {len(real_worker_data['workers'])} real workers from Ocean.xyz")
                        
                        # Add hashrate history if available in cached metrics
                        if cached_metrics and cached_metrics.get("arrow_history") and cached_metrics["arrow_history"].get("hashrate_3hr"):
                            real_worker_data["hashrate_history"] = cached_metrics["arrow_history"]["hashrate_3hr"]
                        
                        # Sync with dashboard metrics to ensure consistency
                        if cached_metrics:
                            self.sync_worker_counts_with_dashboard(real_worker_data, cached_metrics)
                        
                        # Update cache
                        self.worker_data_cache = real_worker_data
                        self.last_worker_data_update = current_time
                        
                        return real_worker_data
                    else:
                        logging.warning("Real worker data had invalid names (like 'online'/'offline'), falling back to simulated data")
                else:
                    logging.warning("Real worker data fetch returned no workers, falling back to simulated data")
            else:
                logging.warning("Dashboard service not available, cannot fetch real worker data")
            
            # Fallback to simulated data if real data fetch fails or returns no workers
            logging.info("Generating fallback simulated worker data")
            worker_data = self.generate_fallback_data(cached_metrics)
            
            # Add hashrate history if available in cached metrics
            if cached_metrics and cached_metrics.get("arrow_history") and cached_metrics["arrow_history"].get("hashrate_3hr"):
                worker_data["hashrate_history"] = cached_metrics["arrow_history"]["hashrate_3hr"]
            
            # Ensure worker counts match dashboard metrics
            if cached_metrics:
                self.sync_worker_counts_with_dashboard(worker_data, cached_metrics)
            
            # Update cache
            self.worker_data_cache = worker_data
            self.last_worker_data_update = current_time
            
            logging.info(f"Successfully generated fallback worker data: {worker_data['workers_total']} workers")
            return worker_data
                
        except Exception as e:
            logging.error(f"Error getting worker data: {e}")
            fallback_data = self.generate_fallback_data(cached_metrics)
            
            # Even on error, try to sync with dashboard metrics
            if cached_metrics:
                self.sync_worker_counts_with_dashboard(fallback_data, cached_metrics)
                
            return fallback_data

    def sync_worker_counts_with_dashboard(self, worker_data, dashboard_metrics):
        """
        Synchronize worker counts and other metrics between worker data and dashboard metrics.
        
        Args:
            worker_data (dict): Worker data to be updated
            dashboard_metrics (dict): Dashboard metrics with worker count and other data
        """
        if not worker_data or not dashboard_metrics:
            return
            
        # Sync worker count
        dashboard_worker_count = dashboard_metrics.get("workers_hashing")
        
        # Only proceed if dashboard has valid worker count
        if dashboard_worker_count is not None:
            current_worker_count = worker_data.get("workers_total", 0)
            
            # If counts already match, no need to sync workers count
            if current_worker_count != dashboard_worker_count:
                logging.info(f"Syncing worker count: worker page({current_worker_count}) → dashboard({dashboard_worker_count})")
                
                # Update the total count
                worker_data["workers_total"] = dashboard_worker_count
                
                # Adjust online/offline counts proportionally
                current_online = worker_data.get("workers_online", 0)
                current_total = max(1, current_worker_count)  # Avoid division by zero
                
                # Calculate ratio of online workers
                online_ratio = current_online / current_total
                
                # Recalculate online and offline counts
                new_online_count = round(dashboard_worker_count * online_ratio)
                new_offline_count = dashboard_worker_count - new_online_count
                
                # Update the counts
                worker_data["workers_online"] = new_online_count
                worker_data["workers_offline"] = new_offline_count
                
                logging.info(f"Updated worker counts - Total: {dashboard_worker_count}, Online: {new_online_count}, Offline: {new_offline_count}")
                
                # If we have worker instances, try to adjust them as well
                if "workers" in worker_data and isinstance(worker_data["workers"], list):
                    self.adjust_worker_instances(worker_data, dashboard_worker_count)
                    
        # Sync daily sats - critical for fixing the daily sats discrepancy
        if dashboard_metrics.get("daily_mined_sats") is not None:
            daily_sats_value = dashboard_metrics.get("daily_mined_sats")
            if daily_sats_value != worker_data.get("daily_sats"):
                worker_data["daily_sats"] = daily_sats_value
                logging.info(f"Synced daily sats: {worker_data['daily_sats']}")
        
        # Sync other important metrics
        if dashboard_metrics.get("total_hashrate") is not None:
            worker_data["total_hashrate"] = dashboard_metrics.get("total_hashrate")
            
        if dashboard_metrics.get("unpaid_earnings") is not None:
            # Attempt to convert string to float if needed
            unpaid_value = dashboard_metrics.get("unpaid_earnings")
            if isinstance(unpaid_value, str):
                try:
                    unpaid_value = float(unpaid_value.split()[0].replace(',', ''))
                except (ValueError, IndexError):
                    pass
            worker_data["total_earnings"] = unpaid_value

    def adjust_worker_instances(self, worker_data, target_count):
        """
        Adjust the number of worker instances to match the target count.
        
        Args:
            worker_data (dict): Worker data containing worker instances
            target_count (int): Target number of worker instances
        """
        current_workers = worker_data.get("workers", [])
        current_count = len(current_workers)
        
        if current_count == target_count:
            return
            
        if current_count < target_count:
            # Need to add more workers
            workers_to_add = target_count - current_count
            
            # Get existing online/offline worker counts
            online_workers = [w for w in current_workers if w["status"] == "online"]
            offline_workers = [w for w in current_workers if w["status"] == "offline"]
            
            # Use the same online/offline ratio for new workers
            online_ratio = len(online_workers) / max(1, current_count)
            new_online = round(workers_to_add * online_ratio)
            new_offline = workers_to_add - new_online
            
            # Copy and adjust existing workers to create new ones
            if online_workers and new_online > 0:
                for i in range(new_online):
                    # Pick a random online worker as template
                    template = random.choice(online_workers).copy()
                    # Give it a new name to avoid duplicates
                    template["name"] = f"{template['name']}_{current_count + i + 1}"
                    current_workers.append(template)
                    
            if offline_workers and new_offline > 0:
                for i in range(new_offline):
                    # Pick a random offline worker as template
                    template = random.choice(offline_workers).copy()
                    # Give it a new name to avoid duplicates
                    template["name"] = f"{template['name']}_{current_count + new_online + i + 1}"
                    current_workers.append(template)
                    
            # If no existing workers of either type, create new ones from scratch
            if not online_workers and new_online > 0:
                for i in range(new_online):
                    worker = self.create_default_worker(f"Miner_{current_count + i + 1}", "online")
                    current_workers.append(worker)
                    
            if not offline_workers and new_offline > 0:
                for i in range(new_offline):
                    worker = self.create_default_worker(f"Miner_{current_count + new_online + i + 1}", "offline")
                    current_workers.append(worker)
                    
        elif current_count > target_count:
            # Need to remove some workers
            workers_to_remove = current_count - target_count
            
            # Remove workers from the end of the list to preserve earlier ones
            worker_data["workers"] = current_workers[:target_count]
            
        # Update the worker data
        worker_data["workers"] = current_workers

    def create_default_worker(self, name, status):
        """
        Create a default worker with given name and status.
        
        Args:
            name (str): Worker name
            status (str): Worker status ('online' or 'offline')
            
        Returns:
            dict: Default worker data
        """
        is_online = status == "online"
        current_time = datetime.now(ZoneInfo("America/Los_Angeles"))
        
        # Generate some reasonable hashrate and other values
        hashrate = round(random.uniform(50, 100), 2) if is_online else 0
        last_share = current_time.strftime("%Y-%m-%d %H:%M") if is_online else (
            (current_time - timedelta(hours=random.uniform(1, 24))).strftime("%Y-%m-%d %H:%M")
        )
        
        return {
            "name": name,
            "status": status,
            "type": "ASIC",
            "model": "Default Miner",
            "hashrate_60sec": hashrate if is_online else 0,
            "hashrate_60sec_unit": "TH/s",
            "hashrate_3hr": hashrate if is_online else round(random.uniform(30, 80), 2),
            "hashrate_3hr_unit": "TH/s",
            "efficiency": round(random.uniform(80, 95), 1) if is_online else 0,
            "last_share": last_share,
            "earnings": round(random.uniform(0.0001, 0.001), 8),
            "acceptance_rate": round(random.uniform(95, 99), 1),
            "power_consumption": round(random.uniform(2000, 3500)) if is_online else 0,
            "temperature": round(random.uniform(55, 75)) if is_online else 0
        }

    def generate_fallback_data(self, cached_metrics):
        """
        Generate fallback worker data from cached metrics when real data can't be fetched.
        Try to preserve real worker names if available.
        
        Args:
            cached_metrics (dict): Cached metrics from the dashboard
                
        Returns:
            dict: Generated worker data
        """
        # If metrics aren't available yet, return default data
        if not cached_metrics:
            logging.warning("No cached metrics available for worker fallback data")
            return self.generate_default_workers_data()
                
        # Check if we have workers_hashing information
        workers_count = cached_metrics.get("workers_hashing", 0)
        
        # Force at least 1 worker if the count is 0
        if workers_count <= 0:
            logging.warning("No workers reported in metrics, forcing 1 worker")
            workers_count = 1
                
        # Get hashrate from cached metrics
        original_hashrate_3hr = float(cached_metrics.get("hashrate_3hr", 0) or 0)
        hashrate_unit = cached_metrics.get("hashrate_3hr_unit", "TH/s")
        
        # If hashrate is 0, set a minimum value to avoid empty display
        if original_hashrate_3hr <= 0:
            original_hashrate_3hr = 50.0
            logging.warning(f"Hashrate was 0, setting minimum value of {original_hashrate_3hr} {hashrate_unit}")
        
        # Check if we have any previously cached real worker names
        real_worker_names = []
        if self.worker_data_cache and self.worker_data_cache.get('workers'):
            for worker in self.worker_data_cache['workers']:
                name = worker.get('name', '')
                # Only use names that don't look like status indicators
                if name and name.lower() not in ['online', 'offline', 'total']:
                    real_worker_names.append(name)
        
        # Generate worker data
        workers_data = []
        
        # If we have real worker names, use them
        if real_worker_names:
            logging.info(f"Using {len(real_worker_names)} real worker names from cache")
            workers_data = self.generate_simulated_workers(
                workers_count, 
                original_hashrate_3hr, 
                hashrate_unit,
                real_worker_names=real_worker_names
            )
        else:
            # Otherwise use sequential names
            logging.info("No real worker names available, using sequential names")
            workers_data = self.generate_sequential_workers(
                workers_count,
                original_hashrate_3hr,
                hashrate_unit
            )
        
        # Calculate basic statistics
        workers_online = len([w for w in workers_data if w['status'] == 'online'])
        workers_offline = len(workers_data) - workers_online
        
        # Use unpaid_earnings from main dashboard
        unpaid_earnings = cached_metrics.get("unpaid_earnings", 0)
        # Handle case where unpaid_earnings might be a string
        if isinstance(unpaid_earnings, str):
            try:
                # Handle case where it might include "BTC" or other text
                unpaid_earnings = float(unpaid_earnings.split()[0].replace(',', ''))
            except (ValueError, IndexError):
                unpaid_earnings = 0.001
        
        # Ensure we have a minimum value for unpaid earnings
        if unpaid_earnings <= 0:
            unpaid_earnings = 0.001
        
        # Use unpaid_earnings as total_earnings
        total_earnings = unpaid_earnings
        
        # ---- IMPORTANT FIX: Daily sats calculation ----
        # Get daily_mined_sats directly from cached metrics
        daily_sats = cached_metrics.get("daily_mined_sats", 0)
        
        # If daily_sats is missing or zero, try to calculate it from other available metrics
        if daily_sats is None or daily_sats == 0:
            logging.warning("daily_mined_sats is missing or zero, attempting alternative calculations")
            
            # Try to calculate from daily_btc_net
            if cached_metrics.get("daily_btc_net") is not None:
                daily_btc_net = cached_metrics.get("daily_btc_net")
                daily_sats = int(round(daily_btc_net * self.sats_per_btc))
                logging.info(f"Calculated daily_sats from daily_btc_net: {daily_sats}")
                
            # Alternative calculation from estimated_earnings_per_day
            elif cached_metrics.get("estimated_earnings_per_day") is not None:
                daily_btc = cached_metrics.get("estimated_earnings_per_day")
                daily_sats = int(round(daily_btc * self.sats_per_btc))
                logging.info(f"Calculated daily_sats from estimated_earnings_per_day: {daily_sats}")
                
            # If still zero, try to use estimated_earnings_per_day_sats directly
            elif cached_metrics.get("estimated_earnings_per_day_sats") is not None:
                daily_sats = cached_metrics.get("estimated_earnings_per_day_sats")
                logging.info(f"Using estimated_earnings_per_day_sats as fallback: {daily_sats}")
        
        logging.info(f"Final daily_sats value: {daily_sats}")
        
        # Create hashrate history based on arrow_history if available
        hashrate_history = []
        if cached_metrics.get("arrow_history") and cached_metrics["arrow_history"].get("hashrate_3hr"):
            hashrate_history = cached_metrics["arrow_history"]["hashrate_3hr"]
        
        result = {
            "workers": workers_data,
            "workers_total": len(workers_data),
            "workers_online": workers_online,
            "workers_offline": workers_offline,
            "total_hashrate": original_hashrate_3hr,
            "hashrate_unit": hashrate_unit,
            "total_earnings": total_earnings,
            "daily_sats": daily_sats,  # Fixed daily_sats value
            "avg_acceptance_rate": 98.8,  # Default value
            "hashrate_history": hashrate_history,
            "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
        }
        
        # Update cache
        self.worker_data_cache = result
        self.last_worker_data_update = datetime.now().timestamp()
        
        logging.info(f"Generated fallback data with {len(workers_data)} workers")
        return result

    def generate_sequential_workers(self, num_workers, total_hashrate, hashrate_unit, total_unpaid_earnings=None):
        """
        Generate workers with sequential names when other methods fail.
        
        Args:
            num_workers (int): Number of workers
            total_hashrate (float): Total hashrate
            hashrate_unit (str): Hashrate unit
            total_unpaid_earnings (float, optional): Total unpaid earnings
                
        Returns:
            list: List of worker data dictionaries
        """
        logging.info(f"Generating {num_workers} workers with sequential names")
        
        # Ensure we have at least 1 worker
        num_workers = max(1, num_workers)
        
        # Worker model types for simulation
        models = [
            {"type": "ASIC", "model": "Bitmain Antminer S19 Pro", "max_hashrate": 110, "power": 3250},
            {"type": "ASIC", "model": "MicroBT Whatsminer M50S", "max_hashrate": 130, "power": 3276},
            {"type": "ASIC", "model": "Bitmain Antminer S19j Pro", "max_hashrate": 104, "power": 3150},
            {"type": "FPGA", "model": "BitAxe FPGA Miner", "max_hashrate": 3.2, "power": 35}
        ]
        
        # Calculate hashrate distribution - majority of hashrate to online workers
        online_count = max(1, int(num_workers * 0.8))  # At least 1 online worker
        offline_count = num_workers - online_count
        
        # Average hashrate per online worker (ensure it's at least 0.5 TH/s)
        avg_hashrate = max(0.5, total_hashrate / online_count if online_count > 0 else 0)
        
        workers = []
        current_time = datetime.now(ZoneInfo("America/Los_Angeles"))
        
        # Default total unpaid earnings if not provided
        if total_unpaid_earnings is None or total_unpaid_earnings <= 0:
            total_unpaid_earnings = 0.001  # Default small amount
        
        # Generate online workers with sequential names
        for i in range(online_count):
            # Select a model based on hashrate
            model_info = models[0] if avg_hashrate > 50 else models[-1] if avg_hashrate < 5 else random.choice(models)
            
            # For Antminers and regular ASICs, use ASIC model
            if i < online_count - 1 or avg_hashrate > 5:
                model_idx = random.randint(0, len(models) - 2)  # Exclude FPGA for most workers
            else:
                model_idx = len(models) - 1  # FPGA for last worker if small hashrate
                    
            model_info = models[model_idx]
            
            # Generate hashrate with some random variation
            base_hashrate = min(model_info["max_hashrate"], avg_hashrate * random.uniform(0.5, 1.5))
            hashrate_60sec = round(base_hashrate * random.uniform(0.9, 1.1), 2)
            hashrate_3hr = round(base_hashrate * random.uniform(0.85, 1.0), 2)
            
            # Generate last share time (within last 5 minutes)
            minutes_ago = random.randint(0, 5)
            last_share = (current_time - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M")
            
            # Generate acceptance rate (95-100%)
            acceptance_rate = round(random.uniform(95, 100), 1)
            
            # Generate temperature (normal operating range)
            temperature = random.randint(55, 70) if model_info["type"] == "ASIC" else random.randint(45, 55)
            
            # Create a sequential name
            name = f"Miner_{i+1}"
            
            workers.append({
                "name": name,
                "status": "online",
                "type": model_info["type"],
                "model": model_info["model"],
                "hashrate_60sec": hashrate_60sec,
                "hashrate_60sec_unit": hashrate_unit,
                "hashrate_3hr": hashrate_3hr,
                "hashrate_3hr_unit": hashrate_unit,
                "efficiency": round(random.uniform(65, 95), 1),
                "last_share": last_share,
                "earnings": 0,  # Will be set after all workers are generated
                "acceptance_rate": acceptance_rate,
                "power_consumption": model_info["power"],
                "temperature": temperature
            })
        
        # Generate offline workers
        for i in range(offline_count):
            # Select a model - more likely to be FPGA for offline
            if random.random() > 0.6:
                model_info = models[-1]  # FPGA
            else:
                model_info = random.choice(models[:-1])  # ASIC
                    
            # Generate last share time (0.5 to 8 hours ago)
            hours_ago = random.uniform(0.5, 8)
            last_share = (current_time - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M")
            
            # Generate hashrate (historical before going offline)
            if model_info["type"] == "FPGA":
                hashrate_3hr = round(random.uniform(1, 3), 2)
            else:
                hashrate_3hr = round(random.uniform(20, 90), 2)
                    
            # Create a sequential name
            idx = i + online_count  # Index for offline workers starts after online workers
            name = f"Miner_{idx+1}"
            
            workers.append({
                "name": name,
                "status": "offline",
                "type": model_info["type"],
                "model": model_info["model"],
                "hashrate_60sec": 0,
                "hashrate_60sec_unit": hashrate_unit,
                "hashrate_3hr": hashrate_3hr,
                "hashrate_3hr_unit": hashrate_unit,
                "efficiency": 0,
                "last_share": last_share,
                "earnings": 0,  # Minimal earnings for offline workers
                "acceptance_rate": round(random.uniform(95, 99), 1),
                "power_consumption": 0,
                "temperature": 0
            })

        # Distribute earnings based on hashrate proportion
        # Reserve a small portion (5%) of earnings for offline workers
        online_earnings_pool = total_unpaid_earnings * 0.95
        offline_earnings_pool = total_unpaid_earnings * 0.05
        
        # Distribute earnings based on hashrate proportion for online workers
        total_effective_hashrate = sum(w["hashrate_3hr"] for w in workers if w["status"] == "online")
        if total_effective_hashrate > 0:
            for worker in workers:
                if worker["status"] == "online":
                    hashrate_proportion = worker["hashrate_3hr"] / total_effective_hashrate
                    worker["earnings"] = round(online_earnings_pool * hashrate_proportion, 8)
        
        # Distribute minimal earnings to offline workers
        if offline_count > 0:
            offline_per_worker = offline_earnings_pool / offline_count
            for worker in workers:
                if worker["status"] == "offline":
                    worker["earnings"] = round(offline_per_worker, 8)
        
        logging.info(f"Generated {len(workers)} workers with sequential names")
        return workers

    def generate_simulated_workers(self, num_workers, total_hashrate, hashrate_unit, total_unpaid_earnings=None, real_worker_names=None):
        """
        Generate simulated worker data based on total hashrate.
        This is a fallback method used when real data can't be fetched.
        
        Args:
            num_workers (int): Number of workers
            total_hashrate (float): Total hashrate
            hashrate_unit (str): Hashrate unit
            total_unpaid_earnings (float, optional): Total unpaid earnings
            real_worker_names (list, optional): List of real worker names to use instead of random names
                
        Returns:
            list: List of worker data dictionaries
        """
        # Ensure we have at least 1 worker
        num_workers = max(1, num_workers)
        
        # Worker model types for simulation
        models = [
            {"type": "ASIC", "model": "Bitmain Antminer S19 Pro", "max_hashrate": 110, "power": 3250},
            {"type": "ASIC", "model": "MicroBT Whatsminer M50S", "max_hashrate": 130, "power": 3276},
            {"type": "ASIC", "model": "Bitmain Antminer S19j Pro", "max_hashrate": 104, "power": 3150},
            {"type": "FPGA", "model": "BitAxe FPGA Miner", "max_hashrate": 3.2, "power": 35}
        ]
        
        # Worker names for simulation - only used if no real worker names are provided
        prefixes = ["Antminer", "Whatsminer", "Miner", "Rig", "Node", "Worker", "BitAxe", "BTC"]
        
        # Calculate hashrate distribution - majority of hashrate to online workers
        online_count = max(1, int(num_workers * 0.8))  # At least 1 online worker
        offline_count = num_workers - online_count
        
        # Average hashrate per online worker (ensure it's at least 0.5 TH/s)
        avg_hashrate = max(0.5, total_hashrate / online_count if online_count > 0 else 0)
        
        workers = []
        current_time = datetime.now(ZoneInfo("America/Los_Angeles"))
        
        # Default total unpaid earnings if not provided
        if total_unpaid_earnings is None or total_unpaid_earnings <= 0:
            total_unpaid_earnings = 0.001  # Default small amount
        
        # Prepare name list - use real names if available, otherwise will generate random names
        # If we have real names but not enough, we'll reuse them or generate additional random ones
        name_list = []
        if real_worker_names and len(real_worker_names) > 0:
            logging.info(f"Using {len(real_worker_names)} real worker names")
            # Ensure we have enough names by cycling through the list if needed
            name_list = real_worker_names * (num_workers // len(real_worker_names) + 1)
            name_list = name_list[:num_workers]  # Truncate to exact number needed
        
        # Generate online workers
        for i in range(online_count):
            # Select a model based on hashrate
            model_info = models[0] if avg_hashrate > 50 else models[-1] if avg_hashrate < 5 else random.choice(models)
            
            # For Antminers and regular ASICs, use ASIC model
            if i < online_count - 1 or avg_hashrate > 5:
                model_idx = random.randint(0, len(models) - 2)  # Exclude FPGA for most workers
            else:
                model_idx = len(models) - 1  # FPGA for last worker if small hashrate
                    
            model_info = models[model_idx]
            
            # Generate hashrate with some random variation
            base_hashrate = min(model_info["max_hashrate"], avg_hashrate * random.uniform(0.5, 1.5))
            hashrate_60sec = round(base_hashrate * random.uniform(0.9, 1.1), 2)
            hashrate_3hr = round(base_hashrate * random.uniform(0.85, 1.0), 2)
            
            # Generate last share time (within last 3 minutes)
            minutes_ago = random.randint(0, 3)
            last_share = (current_time - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M")
            
            # Generate acceptance rate (95-100%)
            acceptance_rate = round(random.uniform(95, 100), 1)
            
            # Generate temperature (normal operating range)
            temperature = random.randint(55, 70) if model_info["type"] == "ASIC" else random.randint(45, 55)
            
            # Use a real name if available, otherwise generate a random name
            if name_list and i < len(name_list):
                name = name_list[i]
            else:
                # Create a unique name
                if model_info["type"] == "FPGA":
                    name = f"{prefixes[-1]}{random.randint(1, 99):02d}"
                else:
                    name = f"{random.choice(prefixes[:-1])}{random.randint(1, 99):02d}"
            
            workers.append({
                "name": name,
                "status": "online",
                "type": model_info["type"],
                "model": model_info["model"],
                "hashrate_60sec": hashrate_60sec,
                "hashrate_60sec_unit": hashrate_unit,
                "hashrate_3hr": hashrate_3hr,
                "hashrate_3hr_unit": hashrate_unit,
                "efficiency": round(random.uniform(65, 95), 1),
                "last_share": last_share,
                "earnings": 0,  # Will be set after all workers are generated
                "acceptance_rate": acceptance_rate,
                "power_consumption": model_info["power"],
                "temperature": temperature
            })
        
        # Generate offline workers
        for i in range(offline_count):
            # Select a model - more likely to be FPGA for offline
            if random.random() > 0.6:
                model_info = models[-1]  # FPGA
            else:
                model_info = random.choice(models[:-1])  # ASIC
                    
            # Generate last share time (0.5 to 8 hours ago)
            hours_ago = random.uniform(0.5, 8)
            last_share = (current_time - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M")
            
            # Generate hashrate (historical before going offline)
            if model_info["type"] == "FPGA":
                hashrate_3hr = round(random.uniform(1, 3), 2)
            else:
                hashrate_3hr = round(random.uniform(20, 90), 2)
                    
            # Use a real name if available, otherwise generate a random name
            idx = i + online_count  # Index for offline workers starts after online workers
            if name_list and idx < len(name_list):
                name = name_list[idx]
            else:
                # Create a unique name
                if model_info["type"] == "FPGA":
                    name = f"{prefixes[-1]}{random.randint(1, 99):02d}"
                else:
                    name = f"{random.choice(prefixes[:-1])}{random.randint(1, 99):02d}"
            
            workers.append({
                "name": name,
                "status": "offline",
                "type": model_info["type"],
                "model": model_info["model"],
                "hashrate_60sec": 0,
                "hashrate_60sec_unit": hashrate_unit,
                "hashrate_3hr": hashrate_3hr,
                "hashrate_3hr_unit": hashrate_unit,
                "efficiency": 0,
                "last_share": last_share,
                "earnings": 0,  # Minimal earnings for offline workers
                "acceptance_rate": round(random.uniform(95, 99), 1),
                "power_consumption": 0,
                "temperature": 0
            })

        # Calculate the current sum of online worker hashrates
        current_total = sum(w["hashrate_3hr"] for w in workers if w["status"] == "online")
        
        # If we have online workers and the total doesn't match, apply a scaling factor
        if online_count > 0 and abs(current_total - total_hashrate) > 0.01 and current_total > 0:
            scaling_factor = total_hashrate / current_total
            
            # Apply scaling to all online workers
            for worker in workers:
                if worker["status"] == "online":
                    # Scale the 3hr hashrate to exactly match total
                    worker["hashrate_3hr"] = round(worker["hashrate_3hr"] * scaling_factor, 2)
                    
                    # Scale the 60sec hashrate proportionally
                    if worker["hashrate_60sec"] > 0:
                        worker["hashrate_60sec"] = round(worker["hashrate_60sec"] * scaling_factor, 2)
        
        # Reserve a small portion (5%) of earnings for offline workers
        online_earnings_pool = total_unpaid_earnings * 0.95
        offline_earnings_pool = total_unpaid_earnings * 0.05
        
        # Distribute earnings based on hashrate proportion for online workers
        total_effective_hashrate = sum(w["hashrate_3hr"] for w in workers if w["status"] == "online")
        if total_effective_hashrate > 0:
            for worker in workers:
                if worker["status"] == "online":
                    hashrate_proportion = worker["hashrate_3hr"] / total_effective_hashrate
                    worker["earnings"] = round(online_earnings_pool * hashrate_proportion, 8)
        
        # Distribute minimal earnings to offline workers
        if offline_count > 0:
            offline_per_worker = offline_earnings_pool / offline_count
            for worker in workers:
                if worker["status"] == "offline":
                    worker["earnings"] = round(offline_per_worker, 8)
        
        # Final verification - ensure total earnings match
        current_total_earnings = sum(w["earnings"] for w in workers)
        if abs(current_total_earnings - total_unpaid_earnings) > 0.00000001:
            # Adjust the first worker to account for any rounding errors
            adjustment = total_unpaid_earnings - current_total_earnings
            for worker in workers:
                if worker["status"] == "online":
                    worker["earnings"] = round(worker["earnings"] + adjustment, 8)
                    break
        
        return workers
