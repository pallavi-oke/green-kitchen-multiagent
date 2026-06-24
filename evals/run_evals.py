import json
import os
import sys

# Add parent directory to path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from copilot.engine import run_ordering_pipeline

def run_evaluations():
    print("\n==============================================")
    print("      CLOUD KITCHEN EVALUATION HARNESS")
    print("==============================================\n")
    
    # Check if Langfuse is configured
    langfuse_active = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
    if langfuse_active:
        print("🔗 Langfuse Integration: ACTIVE. Every LLM matching call will be traced to your dashboard.")
    else:
        print("💡 Langfuse Integration: INACTIVE (Local execution only). Add Langfuse keys to sync traces.")
    print("-" * 80)
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data")
    eval_path = os.path.join(data_dir, "eval_dataset.json")
    
    with open(eval_path, "r") as f:
        eval_cases = json.load(f)
        
    total_test_cases = len(eval_cases)
    passed_cases = 0
    
    sku_matching_successes = 0
    sku_matching_attempts = 0
    stockout_incidents = 0
    
    for idx, case in enumerate(eval_cases, 1):
        case_id = case["id"]
        desc = case["description"]
        day = case["forecast_day"]
        stock = case["starting_stock"]
        expected_orders = case["expected_orders"]
        
        print(f"Test Case {idx}: [{case_id}] - {desc}")
        
        # Run the copilot pipeline (will trigger Langfuse trace callback inside matcher.py if keys are set)
        actual_order = run_ordering_pipeline(day, stock, data_dir=data_dir)
        
        # Build dictionary of {SKU: actual_cases} from agent output
        actual_order_dict = {}
        for item in actual_order:
            if item["cases"] > 0:
                actual_order_dict[item["sku"]] = item["cases"]
                
        all_match = True
        case_errors = []
        
        # Check all expected SKUs are matched and have the correct case counts
        for expected_sku, expected_cases in expected_orders.items():
            sku_matching_attempts += 1
            actual_cases = actual_order_dict.get(expected_sku, 0)
            
            if actual_cases == expected_cases:
                sku_matching_successes += 1
            else:
                all_match = False
                if actual_cases == 0:
                    case_errors.append(f"Missing SKU {expected_sku} entirely in draft order")
                    stockout_incidents += 1
                elif actual_cases < expected_cases:
                    case_errors.append(f"Under-ordered SKU {expected_sku} (Ordered {actual_cases}cs instead of {expected_cases}cs)")
                    stockout_incidents += 1
                else:
                    case_errors.append(f"Over-ordered SKU {expected_sku} (Ordered {actual_cases}cs instead of {expected_cases}cs)")
                    
        # Check for any extra SKUs
        for actual_sku, actual_cases in actual_order_dict.items():
            if actual_sku not in expected_orders:
                all_match = False
                case_errors.append(f"Unnecessary SKU {actual_sku} added to draft order ({actual_cases}cs)")
                
        # Print status for this test case
        if all_match:
            print(" -> STATUS: PASSED ✅")
            passed_cases += 1
        else:
            print(" -> STATUS: FAILED ❌")
            for err in case_errors:
                print(f"    - {err}")
                
        print("-" * 80)
        
    sku_accuracy = (sku_matching_successes / sku_matching_attempts) * 100 if sku_matching_attempts > 0 else 0.0
    pass_rate = (passed_cases / total_test_cases) * 100
    
    print("==============================================")
    print("              EVALUATION SUMMARY")
    print("==============================================")
    print(f"Total Test Cases Run:   {total_test_cases}")
    print(f"Passed Test Cases:      {passed_cases} ({pass_rate:.1f}%)")
    print(f"SKU Matching Accuracy:  {sku_accuracy:.1f}%")
    print(f"Stockout Incidents:     {stockout_incidents} (Critical Operational Risk)")
    print("==============================================")
    
    if pass_rate >= 90.0:
        print("🎉 SUCCESS: The agent passed the evaluation benchmark!")
    else:
        print("⚠️ WARNING: Agent failed to meet the 90% evaluation bar. Review prompt logs.")
    print("==============================================\n")

if __name__ == "__main__":
    run_evaluations()
