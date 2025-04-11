import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

def calculate_weights(matrix: np.ndarray) -> Tuple[np.ndarray, float]:
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_index = np.argmax(eigenvalues.real)
    max_eigenvalue = eigenvalues[max_index].real
    eigenvector = eigenvectors[:, max_index].real
    weights: np.ndarray = eigenvector / np.sum(eigenvector)
    
    n = matrix.shape[0]
    ci = (max_eigenvalue - n) / (n - 1)
    ri_values: Dict[int, float] = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41}
    ri = ri_values.get(n, 1.5)
    cr = ci / ri if ri > 0 else 0
    
    return weights.real, cr

def main() -> None:
    dataset = pd.read_csv("data/dataset.csv")
    cars: List[str] = dataset['title'].tolist()
    
    # level 1 categories
    category_criteria = ["Reliability", "Cost", "Performance"]
    category_matrix: np.ndarray = np.array([
        [1, 3, 5], # reliability is 3x more important than cost and 5x more than performance
        [1/3, 1, 3], # cost is 3x more important than performance
        [1/4, 1/3, 1] # inconsistent - should be 1/5
    ])
    print(pd.DataFrame(category_matrix, index=category_criteria, columns=category_criteria))
    category_weights, category_cr = calculate_weights(category_matrix)
    print(f"\ncategory weights: {[f'{w:.4f}' for w in category_weights]}")
    print(f"consistency ratio: {category_cr:.4f} ({'consistent' if category_cr < 0.1 else 'inconsistent!'})")

    if category_cr >= 0.1:
        reconstructed = np.array([category_weights[i] / category_weights[j] for i in range(len(category_weights)) for j in range(len(category_weights))]).reshape(3, 3)
        difference = category_matrix - reconstructed
        max_diff_idx = np.unravel_index(np.argmax(np.abs(difference)), difference.shape)
        print(f"\nreconstructed\n{pd.DataFrame(reconstructed, index=category_criteria, columns=category_criteria)}")
        print(f"\ndifference\n{pd.DataFrame(difference, index=category_criteria, columns=category_criteria)}")
        print(f"\nlargest difference: {difference[max_diff_idx]:.4f} at position {category_criteria[max_diff_idx[0]]} vs {category_criteria[max_diff_idx[1]]}\n---")
    
    # level 2 criteria
    # cost - only one - price

    # performance
    # ["Engine Size", "Power"]
    performance_matrix: np.ndarray = np.array([
        [1, 1/3], # engine size is 1/3 as important as power
        [3, 1]
    ])
    print(f"\nperformance criteria\n{pd.DataFrame(performance_matrix, index=["Engine Size", "Power"], columns=["Engine Size", "Power"])}")
    performance_weights, performance_cr = calculate_weights(performance_matrix)
    print(f"\nperformance criteria weights: {[f'{w:.4f}' for w in performance_weights]}")
    print(f"consistency ratio: {performance_cr:.4f} ({'consistent' if performance_cr < 0.1 else 'inconsistent!'})\n---")
    
    # reliability
    # ["Mileage", "Year"]
    reliability_matrix: np.ndarray = np.array([
        [1, 3], # mileage is 3x more important than year
        [1/3, 1]
    ])
    print(f"\nreliability criteria\n{pd.DataFrame(reliability_matrix, index=["Mileage", "Year"], columns=["Mileage", "Year"])}")
    reliability_weights, reliability_cr = calculate_weights(reliability_matrix)
    print(f"\nreliability criteria weights: {[f'{w:.4f}' for w in reliability_weights]}")
    print(f"consistency ratio: {reliability_cr:.4f} ({'consistent' if reliability_cr < 0.1 else 'inconsistent!'})\n---")
    
    global_weights: Dict[str, float] = {
        "Price": category_weights[1] * 1.0,  # cost category has only price criterion
        "Engine Size": category_weights[2] * performance_weights[0],
        "Power": category_weights[2] * performance_weights[1],
        "Mileage": category_weights[0] * reliability_weights[0],
        "Year": category_weights[0] * reliability_weights[1]
    }
    
    for criterion, weight in global_weights.items():
        print(f"{criterion}: {weight:.4f}")
    
    print("\nalternative Evaluation")
    print("----------------")
    
    # normalize
    price_values: np.ndarray = 1 - (dataset['price'].values / dataset['price'].max())
    year_values: np.ndarray = dataset['year'].values / dataset['year'].max()
    mileage_values: np.ndarray = 1 - (dataset['mileage_km'].values / dataset['mileage_km'].max())
    engine_values: np.ndarray = dataset['engine_size_cm3'].values / dataset['engine_size_cm3'].max()
    power_values: np.ndarray = dataset['power_hp'].values / dataset['power_hp'].max()
    
    alt_matrix: np.ndarray = np.column_stack([
        price_values,
        engine_values,
        power_values,
        mileage_values,
        year_values
    ])
    
    criteria_list: List[str] = ["Price", "Engine Size", "Power", "Mileage", "Year"]
    weights_array: np.ndarray = np.array([global_weights[c] for c in criteria_list])
    final_scores: np.ndarray = np.dot(alt_matrix, weights_array)
    
    results: pd.DataFrame = pd.DataFrame({
        'Car': cars,
        'Score': final_scores
    }).sort_values('Score', ascending=False).reset_index(drop=True)
    results['Rank'] = results.index + 1
    
    print(results[['Rank', 'Car', 'Score']])
    
    # visualize weights
    plt.figure(figsize=(10, 6))
    plt.bar(list(global_weights.keys()), list(global_weights.values()))
    plt.title('Global Weights of Criteria')
    plt.ylabel('Weight')
    plt.xticks(rotation=45)
    for i, (criterion, weight) in enumerate(global_weights.items()):
        plt.text(i, weight + 0.01, f'{weight:.4f}', ha='center')
    plt.tight_layout()
    plt.savefig('ahp_weights.png')
    
    # visualize consistency ratios
    cr_data: Dict[str, float] = {
        'Categories': category_cr,
        'Performance': performance_cr,
        'Reliability': reliability_cr
    }
    
    plt.figure(figsize=(8, 5))
    plt.bar(list(cr_data.keys()), list(cr_data.values()), color=['green' if cr < 0.1 else 'red' for cr in cr_data.values()])
    plt.axhline(y=0.1, color='r', linestyle='--', label='Threshold (0.1)')
    plt.title('Consistency Ratios')
    plt.ylabel('Consistency Ratio (CR)')
    
    for i, (name, cr) in enumerate(cr_data.items()):
        plt.text(i, cr + 0.01, f'{cr:.4f}', ha='center')
    
    plt.legend()
    plt.tight_layout()
    plt.savefig('consistency_ratios.png')
    
    print("\nvisualizations saved as 'ahp_weights.png' and 'consistency_ratios.png'")

if __name__ == "__main__":
    main()
