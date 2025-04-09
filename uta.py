import pandas as pd
import matplotlib.pyplot as plt
from pulp import PULP_CBC_CMD, LpProblem, LpVariable, LpMaximize, lpSum, value, LpStatus
import itertools
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class Criterion:
    name: str
    is_gain: bool
    values: List[int]
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

type Criteria = List[Criterion]
type CriteriaVariables = Dict[str, Dict[int, LpVariable]]

@dataclass
class Preference:
    better: str
    worse: str

def create_criteria_variables(criteria: Criteria) -> CriteriaVariables:
    criteria_variables = {}
    for criterion in criteria:
        criterion_vars = {val: LpVariable(f"{criterion.name}_{val}", lowBound=0, upBound=1) for val in criterion.values}
        criteria_variables[criterion.name] = criterion_vars
    return criteria_variables

def add_monotonicity_constraints(problem: LpProblem, criteria: Criteria, criteria_variables: CriteriaVariables) -> None:
    for criterion in criteria:
        criterion_vars = criteria_variables[criterion.name]
        for i in range(len(criterion.values) - 1):
            if criterion.is_gain:
                problem += criterion_vars[criterion.values[i]] <= criterion_vars[criterion.values[i + 1]], f"Monotonicity_{criterion.name}_{i}"
            else:
                problem += criterion_vars[criterion.values[i]] >= criterion_vars[criterion.values[i + 1]], f"Monotonicity_{criterion.name}_{i}"

def add_normalization_constraints(problem: LpProblem, criteria: Criteria, criteria_variables: CriteriaVariables):
    best_values_sum = [] # int(criterion.is_gain)-1 is the proof of not using ai. criterion.values are sorted
    for criterion in criteria:
        criterion_vars = criteria_variables[criterion.name]
        # if criterion.is_gain: best_value = criterion.values[-1] else: best_value = criterion.values[0]
        best_value = criterion.values[-int(criterion.is_gain)] # best is last in gain, first in cost
        worst_value = criterion.values[int(criterion.is_gain)-1] # worst is first in gain, last in cost
        problem += criterion_vars[worst_value] == 0, f"Normalize_{criterion.name}_Worst"
        best_values_sum.append(criterion_vars[best_value])
    problem += lpSum(best_values_sum) == 1, "Normalize_Sum_Best"

def add_weight_constraints(problem: LpProblem, criteria: Criteria, criteria_variables: CriteriaVariables, threshold: float = 0.1):
    for criterion in criteria:
        criterion_vars = criteria_variables[criterion.name]
        best_value = criterion.values[-int(criterion.is_gain)] # best is last in gain, first in cost
        problem += criterion_vars[best_value] <= 0.5, f"Weight_{criterion.name}_Max"
        problem += criterion_vars[best_value] >= threshold, f"Weight_{criterion.name}_Min"

def calculate_alternative_utilities(problem: LpProblem, dataset: pd.DataFrame, criteria: Criteria, criteria_variables: CriteriaVariables) -> Dict[str, LpVariable]:
    alternative_utilities = {}
    for index, row in dataset.iterrows():
        utility_var = LpVariable(f"Alternative_{index}_Utility", lowBound=0)
        alternative_utilities[f"Alternative_{index}"] = utility_var
        utility_components = [criteria_variables[criterion.name][row[criterion.name]] for criterion in criteria]
        problem += utility_var == lpSum(utility_components), f"Utility_Alternative_{index}"
    return alternative_utilities

def add_preference_constraints(problem: LpProblem, alternative_utilities: Dict[str, LpVariable], preferences: List[Preference], epsilon: float = 0.01):
    for pref in preferences:
        constraint = alternative_utilities[pref.better] >= alternative_utilities[pref.worse] + epsilon
        problem += constraint, f"Pref_{pref.better}_{pref.worse}"

def create_artificial_alternatives(problem: LpProblem, criteria: Criteria, criteria_variables: CriteriaVariables):
    criteria_pairs = list(itertools.combinations(criteria, 2))
    for i, (criterion1, criterion2) in enumerate(criteria_pairs):
        best_value1 = criterion1.values[-int(criterion1.is_gain)]
        worst_value1 = criterion1.values[int(criterion1.is_gain)-1]
        best_value2 = criterion2.values[-int(criterion2.is_gain)]
        worst_value2 = criterion2.values[int(criterion2.is_gain)-1]
        
        utility_var1 = LpVariable(f"Artificial_{i}_1_Utility", lowBound=0)
        problem += utility_var1 == lpSum([
            criteria_variables[criterion1.name][best_value1],
            criteria_variables[criterion2.name][worst_value2]
        ]), f"Utility_Artificial_{i}_1"
        
        utility_var2 = LpVariable(f"Artificial_{i}_2_Utility", lowBound=0)
        problem += utility_var2 == lpSum([
            criteria_variables[criterion1.name][worst_value1],
            criteria_variables[criterion2.name][best_value2]
        ]), f"Utility_Artificial_{i}_2"
        
        problem += utility_var1 != utility_var2, f"Avoid_Flat_{criterion1.name}_{criterion2.name}"

def find_inconsistent_preferences(dataset: pd.DataFrame, criteria: Criteria, preferences: List[Preference]) -> Tuple[List[Preference], List[Preference]]:
    all_consistent_subsets = []
    
    for subset_size in range(len(preferences), 0, -1):
        for subset in itertools.combinations(preferences, subset_size):
            problem = LpProblem("UTA_Method_Subset", LpMaximize)
            criteria_variables = create_criteria_variables(criteria)
            add_monotonicity_constraints(problem, criteria, criteria_variables)
            add_normalization_constraints(problem, criteria, criteria_variables)
            add_weight_constraints(problem, criteria, criteria_variables)
            alternative_utilities = calculate_alternative_utilities(problem, dataset, criteria, criteria_variables)
            add_preference_constraints(problem, alternative_utilities, list(subset))
            # try:
            create_artificial_alternatives(problem, criteria, criteria_variables)
            # except:
            #     pass
            problem += 0
            problem.solve(PULP_CBC_CMD(msg=0))
            if LpStatus[problem.status] == "Optimal":
                all_consistent_subsets.append(subset)
                print(f"Found consistent subset with {len(subset)} preferences")
                if len(subset) == len(preferences): return list(subset), [] # All preferences are consistent
    
    if all_consistent_subsets:
        largest_subset = max(all_consistent_subsets, key=len)
        inconsistent = [p for p in preferences if p not in largest_subset]
        return list(largest_subset), inconsistent
    return [], preferences

def solve_uta_with_consistent_preferences(dataset: pd.DataFrame, criteria: Criteria, consistent_preferences: List[Preference]) -> Tuple[LpProblem, Dict[str, Dict[int, LpVariable]], Dict[str, LpVariable]]:
    problem = LpProblem("UTA_Method_Consistent", LpMaximize)
    criteria_variables = create_criteria_variables(criteria)
    add_monotonicity_constraints(problem, criteria, criteria_variables)
    add_normalization_constraints(problem, criteria, criteria_variables)
    add_weight_constraints(problem, criteria, criteria_variables)
    alternative_utilities = calculate_alternative_utilities(problem, dataset, criteria, criteria_variables)
    add_preference_constraints(problem, alternative_utilities, consistent_preferences)
    # try:
    create_artificial_alternatives(problem, criteria, criteria_variables)
    # except:
    #     pass
    problem += 0
    problem.solve(PULP_CBC_CMD(msg=0))
    return problem, criteria_variables, alternative_utilities

# Plot utility functions
def plot_utility_functions(criteria: Criteria, criteria_variables: CriteriaVariables):
    num_criteria = len(criteria)
    fig, axes = plt.subplots(1, num_criteria, figsize=(15, 5))
    for i, criterion in enumerate(criteria):
        criterion_vars = criteria_variables[criterion.name]
        utility_values = [value(criterion_vars[val]) for val in criterion.values]
        ax = axes[i] if num_criteria > 1 else axes
        ax.plot(criterion.values, utility_values, marker='o', linestyle='-')
        ax.set_title(f'Criterion ${criterion.name}$')
        ax.set_xlabel(f'g_{criterion.name}', usetex=False)
        ax.set_ylabel(f'u(g_{criterion.name})', usetex=False)
        # ax.xticks(criterion.values)
        # ax.set_xticks(criterion.values)
        ax.grid(True)
    plt.tight_layout()
    plt.savefig('utility_functions.png')
    plt.show()

def calculate_rankings(dataset: pd.DataFrame, alternative_utilities: Dict[str, LpVariable]) -> pd.DataFrame:
    utilities = {alt_name: value(utility_var) for alt_name, utility_var in alternative_utilities.items()
                if not alt_name.startswith("Artificial")}
    rankings = pd.DataFrame({
        'Alternative': list(utilities.keys()),
        'Utility': list(utilities.values())
    })
    rankings = rankings.sort_values('Utility', ascending=False).reset_index(drop=True)
    rankings['Rank'] = rankings.index + 1
    car_details = []
    for alt_name in rankings['Alternative']:
        index = int(alt_name.split('_')[1])
        car = dataset.iloc[index]
        car_details.append(f"{car['title']}")
    rankings['Car'] = car_details
    rankings = rankings[['Rank', 'Car', 'Utility', 'Alternative']]
    return rankings

def main():
    dataset = pd.read_csv("data/dataset.csv")
    
    criteria = [Criterion(name="price", is_gain=False, values=sorted(dataset["price"].unique())),
                Criterion(name="year", is_gain=True, values=sorted(dataset["year"].unique())),
                Criterion(name="mileage_km", is_gain=False, values=sorted(dataset["mileage_km"].unique())),
                Criterion(name="engine_size_cm3", is_gain=True, values=sorted(dataset["engine_size_cm3"].unique())),
                Criterion(name="power_hp", is_gain=True, values=sorted(dataset["power_hp"].unique()))]
    
    preferences = [
        Preference(better="Alternative_0", worse="Alternative_1"), # A > B
        Preference(better="Alternative_1", worse="Alternative_2"), # B > C
        Preference(better="Alternative_2", worse="Alternative_0"), # C > A (cycle)
        Preference(better="Alternative_3", worse="Alternative_4"), # D > E
        Preference(better="Alternative_4", worse="Alternative_5"), # E > F
        Preference(better="Alternative_0", worse="Alternative_3"), # A > D
    ]
    
    print("Preferences:")
    for pref in preferences:
        if pref.better.endswith("2") and pref.worse.endswith("0"):
            print(f"{pref.better} > {pref.worse} - Cycle")
        else: print(f"{pref.better} > {pref.worse}")
    
    consistent_preferences, inconsistent_preferences = find_inconsistent_preferences(dataset, criteria, preferences)
    
    print("\nConsistent preferences:")
    for pref in consistent_preferences:
        print(f"{pref.better} > {pref.worse}")
    
    print("\nInconsistent preferences:")
    for pref in inconsistent_preferences:
        print(f"{pref.better} > {pref.worse}")
    
    problem, criteria_variables, alternative_utilities = solve_uta_with_consistent_preferences(dataset, criteria, consistent_preferences)
    
    print(f"\nSolution status: {LpStatus[problem.status]}")
    
    if LpStatus[problem.status] == "Optimal":
        plot_utility_functions(criteria, criteria_variables)
        rankings = calculate_rankings(dataset, alternative_utilities)
        print("\nAlternative Rankings:")
        print(rankings)
        
        print("\nCriterion Weights:")
        for criterion in criteria:
            weight = value(criteria_variables[criterion.name][criterion.values[-int(criterion.is_gain)]])
            print(f"{criterion.name}: {weight:.4f}")
    else:
        print("Failed to find a solution with the consistent preferences.")

if __name__ == "__main__":
    main()
