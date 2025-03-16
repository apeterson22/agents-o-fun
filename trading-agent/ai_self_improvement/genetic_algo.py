import logging
import os
from typing import Tuple, List, Optional
from deap import base, creator, tools, algorithms
import random
import numpy as np

def setup_logging(log_file: str = 'logs/genetic_algo.log') -> None:
    """Configure logging settings."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s]: %(message)s',
        filemode='a'
    )

class GeneticOptimizer:
    def __init__(self, pop_size: int = 30, generations: int = 10, param_size: int = 10) -> None:
        """
        Initialize Genetic Algorithm Optimizer.
        
        Args:
            pop_size (int): Population size
            generations (int): Number of generations
            param_size (int): Number of parameters per individual
        """
        if not all(isinstance(x, int) and x > 0 for x in [pop_size, generations, param_size]):
            raise ValueError("pop_size, generations, and param_size must be positive integers")

        self.pop_size = pop_size
        self.generations = generations
        self.param_size = param_size
        
        try:
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
            creator.create("Individual", list, fitness=creator.FitnessMax)
        except RuntimeError:
            pass

        self.toolbox = base.Toolbox()
        
        self.toolbox.register("attr_float", random.uniform, -1.0, 1.0)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, 
                            self.toolbox.attr_float, n=param_size)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("population_custom", self._custom_population)
        
        self.toolbox.register("mate", tools.cxBlend, alpha=0.5)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
        self.toolbox.decorate("mutate", tools.DeltaUpdate(valid_range=(-1.0, 1.0)))
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        self.toolbox.register("evaluate", self.evaluate_individual)
        
        self.stats = tools.Statistics(lambda ind: ind.fitness.values)
        self.stats.register("avg", np.mean)
        self.stats.register("max", np.max)
        self.stats.register("min", np.min)

    def _custom_population(self, n: int) -> List:
        """Create population with custom initialization."""
        pop = []
        for _ in range(n):
            ind = self.toolbox.individual()
            # Example: bias first parameter towards higher values
            ind[0] = random.uniform(0.5, 1.0)
            pop.append(ind)
        return pop

    def evaluate_individual(self, individual: List[float]) -> Tuple[float]:
        """
        Evaluate an individual's fitness.
        
        Args:
            individual (List[float]): List of parameters
            
        Returns:
            Tuple[float]: Fitness value as a tuple
        """
        try:
            fitness = sum(x * x for x in individual)  # Example quadratic function
            return (fitness,)
        except Exception as e:
            logging.error(f"Evaluation failed: {e}")
            return (float('-inf'),)

    def run_optimization(self, checkpoint_path: str = "ga_checkpoint.pkl") -> Optional[List[float]]:
        """
        Run the genetic optimization algorithm with checkpointing.
        
        Args:
            checkpoint_path (str): Path for saving/loading checkpoint
            
        Returns:
            Optional[List[float]]: Best individual found or None if failed
        """
        try:
            # Load from checkpoint if exists
            if os.path.exists(checkpoint_path):
                cp = tools.load_checkpoint(checkpoint_path)
                population = cp["population"]
                hof = cp["halloffame"]
                logbook = cp["logbook"]
                random.setstate(cp["rndstate"])
                start_gen = cp["generation"]
                logging.info(f"Resuming from checkpoint at generation {start_gen}")
            else:
                population = self.toolbox.population_custom(n=self.pop_size)
                hof = tools.HallOfFame(1)
                logbook = tools.Logbook()
                start_gen = 0

            population, logbook = algorithms.eaSimple(
                population,
                self.toolbox,
                cxpb=0.8,
                mutpb=0.2,
                ngen=self.generations,
                stats=self.stats,
                halloffame=hof,
                verbose=True,
                checkpoint=checkpoint_path,
                start_gen=start_gen
            )
            
            best_individual = hof[0]
            stats_record = logbook.select("max", "avg")
            
            logging.info(f"Optimization completed. Best fitness: {best_individual.fitness.values[0]}")
            logging.info(f"Best individual: {best_individual}")
            logging.info(f"Final max fitness: {stats_record[0][-1]}, avg: {stats_record[1][-1]}")
            
            return best_individual
            
        except Exception as e:
            logging.error(f"Error running genetic algorithm: {e}")
            return None

    def __del__(self) -> None:
        """Clean up DEAP creator objects."""
        try:
            if "FitnessMax" in creator.__dict__:
                del creator.FitnessMax
            if "Individual" in creator.__dict__:
                del creator.Individual
        except:
            pass

if __name__ == "__main__":
    setup_logging()
    try:
        optimizer = GeneticOptimizer(pop_size=50, generations=20)
        best_solution = optimizer.run_optimization()
        if best_solution is not None:
            logging.info("Optimization successful")
    except Exception as e:
        logging.error(f"Main execution failed: {e}")
