import logging
import importlib
import importlib.util
import os
import traceback
import hashlib
import time
from typing import Dict, Any, Tuple, Optional, List
from threading import Lock  # Added for thread safety

def setup_logging(log_file: str = 'logs/feature_writer.log') -> None:
    """Configure logging settings."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',  # Enhanced format
        filemode='a'  # Append mode
    )

class AdvancedFeatureWriter:
    def __init__(self, plugin_dir: str = 'plugins', max_versions: int = 5) -> None:
        """
        Initialize the AdvancedFeatureWriter.
        
        Args:
            plugin_dir (str): Directory for storing plugin files
            max_versions (int): Maximum number of feature versions to keep
        """
        if not isinstance(max_versions, int) or max_versions <= 0:
            raise ValueError("max_versions must be a positive integer")
            
        self.plugin_dir = plugin_dir
        self.max_versions = max_versions
        os.makedirs(self.plugin_dir, exist_ok=True)
        self.performance_records: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()  # Thread safety for concurrent access
        self.logger = logging.getLogger(self.__class__.__name__)

    def write_feature(self, feature_name: str, feature_code: str) -> bool:
        """
        Write a feature to a file.
        
        Args:
            feature_name (str): Name of the feature
            feature_code (str): Code content of the feature
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_path = os.path.join(self.plugin_dir, f"{feature_name}.py")
        try:
            with self._lock:  # Thread-safe file writing
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(feature_code.strip())
            self.logger.info(f"Feature '{feature_name}' written successfully to {file_path}")
            self._cleanup_old_versions(feature_name)
            return True
        except Exception as e:
            self.logger.error(f"Error writing feature '{feature_name}': {str(e)}")
            return False

    def load_feature(self, feature_name: str) -> Optional[Any]:
        """
        Load a feature module dynamically.
        
        Args:
            feature_name (str): Name of the feature to load
            
        Returns:
            Optional[Any]: Loaded module or None if failed
        """
        file_path = os.path.join(self.plugin_dir, f"{feature_name}.py")
        if not os.path.exists(file_path):
            self.logger.error(f"Feature file not found: {file_path}")
            return None
            
        try:
            spec = importlib.util.spec_from_file_location(feature_name, file_path)
            if spec is None:
                raise ImportError("Failed to create module spec")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.logger.info(f"Feature '{feature_name}' loaded successfully")
            return module
        except Exception as e:
            self.logger.error(f"Error loading feature '{feature_name}': {traceback.format_exc()}")
            return None

    def evaluate_feature(self, module: Any, eval_data: List[Dict]) -> Tuple[Optional[Dict], Optional[float]]:
        """
        Evaluate a feature's performance.
        
        Args:
            module (Any): Loaded feature module
            eval_data (List[Dict]): Evaluation data
            
        Returns:
            Tuple[Optional[Dict], Optional[float]]: Performance metrics and execution time
        """
        if not hasattr(module, 'new_strategy'):
            self.logger.error(f"Module '{module.__name__}' missing 'new_strategy' function")
            return None, None
            
        try:
            start_time = time.time()
            results = module.new_strategy(eval_data)
            if not isinstance(results, list):
                raise ValueError("new_strategy must return a list")
            performance = self.assess_performance(results)
            execution_time = time.time() - start_time

            with self._lock:  # Thread-safe record update
                performance_hash = hashlib.sha256(str(results).encode()).hexdigest()
                self.performance_records[module.__name__] = {
                    'performance': performance,
                    'execution_time': execution_time,
                    'hash': performance_hash,
                    'timestamp': time.ctime()
                }
            self.logger.info(
                f"Feature '{module.__name__}' evaluated. "
                f"Profit: {performance['profitability']:.2f}, "
                f"Success: {performance['success_rate']:.2%}, "
                f"Time: {execution_time:.3f}s"
            )
            return performance, execution_time
        except Exception as e:
            self.logger.error(f"Error evaluating feature '{module.__name__}': {traceback.format_exc()}")
            return None, None

    def assess_performance(self, results: List[Dict]) -> Dict[str, float]:
        """
        Assess performance metrics from results.
        
        Args:
            results (List[Dict]): List of trade results
            
        Returns:
            Dict[str, float]: Performance metrics
        """
        if not results:
            return {'profitability': 0.0, 'success_rate': 0.0, 'max_drawdown': 0.0}
            
        try:
            #Calculate total Profitablitiy
            profitability = sum(trade.get('profit', 0) for trade in results)
        
            #Calculate success rate (percentage of profitable trades)
            success_rate = len([t for t in results if t.get('profit', 0) > 0]) / len(results)
            
            # Calculate Max Drawdown (worst case loss)
            running_balance = [sum(trade.get('profit', 0) for trade in results[:i+1]) for i in range(len(results))]
            max_drawdown = min(running_balance) if running_balance else 0
            
            # Additional metrics
            cumulative_profits = [sum(trade.get('profit', 0) for trade in results[:i+1]) for i in range(len(results))]
            max_drawdown = min(cumulative_profits) if cumulative_profits else 0.0
            return {
                'profitability': profitability,
                'success_rate': success_rate,
                'max_drawdown': max_drawdown
            }
        except ZeroDivisionError:
            return {'profitability': 0.0, 'success_rate': 0.0, 'max_drawdown': 0.0}

    def self_improve(self, feature_name: str, eval_data: List[Dict]) -> Optional[str]:
        """
        Improve a feature based on performance.
        
        Args:
            feature_name (str): Name of the feature to improve
            eval_data (List[Dict]): Evaluation data
            
        Returns:
            Optional[str]: New feature name if improved, None otherwise
        """
        module = self.load_feature(feature_name)
        if not module:
            return None

        performance, exec_time = self.evaluate_feature(module, eval_data)
        if not performance:
            return None

        thresholds = {'profitability': 0, 'success_rate': 0.6, 'max_drawdown': -1000}
        needs_improvement = any(
            performance.get(k, float('-inf' if v > 0 else 'inf')) < v 
            for k, v in thresholds.items()
        )

        if needs_improvement:
            improved_code = self.generate_improved_feature(module, performance)
            new_feature_name = f"{feature_name}_v{int(time.time())}"
            if self.write_feature(new_feature_name, improved_code):
                return new_feature_name
        return None

    def generate_improved_feature(self, module: Any, previous_performance: Dict) -> str:
        """
        Generate improved feature code.
        
        Args:
            module (Any): Original module
            previous_performance (Dict): Previous performance metrics
            
        Returns:
            str: Improved feature code
        """
        # More sophisticated improvement logic
        profit_factor = 1.1 if previous_performance['profitability'] < 0 else 1.0
        risk_factor = 0.9 if previous_performance['max_drawdown'] < -500 else 1.0
        
        improved_feature_code = f'''
def new_strategy(data):
    improved_results = []
    for trade in data:
        base_profit = trade.get('expected_return', 0)
        profit = base_profit * {profit_factor} * {risk_factor}
        improved_results.append({{'profit': profit, 'expected_return': base_profit}})
    return improved_results
'''
        self.logger.info(f"Generated improved feature code. Previous performance: {previous_performance}")
        return improved_feature_code

    def continuous_evaluation_cycle(self, eval_data: List[Dict], interval: int = 3600) -> None:
        """
        Run continuous evaluation and improvement cycle.
        
        Args:
            eval_data (List[Dict]): Evaluation data
            interval (int): Sleep interval in seconds
        """
        if interval <= 0:
            raise ValueError("Interval must be positive")
            
        try:
            while True:
                features = [f[:-3] for f in os.listdir(self.plugin_dir) if f.endswith('.py')]
                if not features:
                    self.logger.warning("No features found in plugin directory")
                
                for feature_name in features:
                    new_feature = self.self_improve(feature_name, eval_data)
                    if new_feature:
                        self.logger.info(f"Improved '{feature_name}' to '{new_feature}'")
                
                self.logger.info(f"Completed evaluation cycle. Features evaluated: {len(features)}")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.logger.info("Continuous evaluation stopped by user")
        except Exception as e:
            self.logger.error(f"Evaluation cycle failed: {traceback.format_exc()}")

    def _cleanup_old_versions(self, feature_name: str) -> None:
        """Remove old versions exceeding max_versions."""
        prefix = feature_name.split('_v')[0]
        versions = sorted(
            [f for f in os.listdir(self.plugin_dir) if f.startswith(prefix) and f.endswith('.py')],
            key=lambda x: int(x.split('_v')[-1][:-3]) if '_v' in x else 0
        )
        if len(versions) > self.max_versions:
            for old_file in versions[:-self.max_versions]:
                try:
                    os.remove(os.path.join(self.plugin_dir, old_file))
                    self.logger.info(f"Cleaned up old version: {old_file}")
                except Exception as e:
                    self.logger.error(f"Failed to clean up {old_file}: {e}")

if __name__ == "__main__":
    setup_logging()
    writer = AdvancedFeatureWriter()
    sample_data = [{'expected_return': 100}, {'expected_return': -50}]
    try:
        writer.continuous_evaluation_cycle(sample_data, interval=5)
    except Exception as e:
        logging.error(f"Main execution failed: {e}")
