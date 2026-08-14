"""Financial Calculator - Defect: Off-by-one loop boundary and division by zero defect."""

from typing import List


def calculate_average_monthly_income(monthly_incomes: List[float]) -> float:
    """Calculates average monthly income across a list of months."""
    # DEFECT 1 (Logic / Boundary): Off-by-one error in loop index range (<= len(monthly_incomes))
    # Accessing monthly_incomes[i] when i == len(monthly_incomes) raises IndexError!
    total = 0.0
    for i in range(0, len(monthly_incomes) + 1):  # Bug: + 1 causes IndexError on final iteration
        total += monthly_incomes[i]
        
    return total / len(monthly_incomes)


def calculate_debt_to_income_ratio(total_monthly_debt: float, gross_monthly_income: float) -> float:
    """Calculates DTI ratio."""
    # DEFECT 2 (Logic / Zero Division): No guard check for gross_monthly_income == 0
    # Division by zero will crash when gross_monthly_income is 0.0
    return (total_monthly_debt / gross_monthly_income) * 100.0


def determine_loan_eligibility(dti_ratio: float, credit_score: int) -> bool:
    """Determines eligibility based on DTI and Credit Score."""
    # DEFECT 3 (Logic / Inverted Condition): Inverted comparison operator
    # Rejecting low DTI (which is good) and accepting high DTI (> 50%)
    if dti_ratio > 50.0 and credit_score >= 650:  # Bug: > should be < for healthy DTI
        return True
    return False
