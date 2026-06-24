import json
import math
import os
import sys

# Add parent directory to path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from copilot.matcher import match_ingredient

def load_data(data_dir=None):
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data")
    
    with open(os.path.join(data_dir, "recipes.json"), "r") as f:
        recipes = json.load(f)["recipes"]
        
    with open(os.path.join(data_dir, "supplier_catalog.json"), "r") as f:
        catalog = json.load(f)["supplier_catalog"]
        
    with open(os.path.join(data_dir, "menu_forecast.json"), "r") as f:
        forecasts = json.load(f)["forecasts"]
        
    return recipes, catalog, forecasts

def calculate_forecast_requirements(day, recipes, forecasts):
    day_forecast = forecasts.get(day.lower())
    if not day_forecast:
        return {}
        
    required_ingredients = {}
    for dish, expected_portions in day_forecast.items():
        recipe = recipes.get(dish.lower())
        if not recipe:
            continue
        base_portions = recipe["base_portions"]
        multiplier = expected_portions / base_portions
        
        for ing, base_qty in recipe["ingredients"].items():
            required_ingredients[ing] = required_ingredients.get(ing, 0.0) + (base_qty * multiplier)
            
    return required_ingredients

def run_ordering_pipeline(day, stock_dict, api_key=None, data_dir=None, trace_ids=None):
    recipes, catalog, forecasts = load_data(data_dir)
    
    # Step 1: Scale forecast to ingredients
    required_ingredients = calculate_forecast_requirements(day, recipes, forecasts)
    if not required_ingredients:
        return []
        
    order_plan = []
    
    # Step 2: Match & Round (with stock subtraction)
    for ing, gross_qty in required_ingredients.items():
        # Match SKU using LLM/fallback
        ing_trace_id = trace_ids.get(ing) if trace_ids else None
        matching_res = match_ingredient(ing, catalog, api_key, trace_id=ing_trace_id)
        sku = matching_res.matched_sku
        
        if not sku:
            continue
            
        # Retrieve catalog packaging rules
        sku_info = next((item for item in catalog.values() if item["sku"] == sku), None)
        if not sku_info:
            continue
            
        unit_per_case = sku_info["unit_per_case"]
        case_unit = sku_info["case_unit"]
        case_price = sku_info["case_price"]
        desc = sku_info["description"]
        
        # Deduct starting stock
        stock = stock_dict.get(ing, 0.0)
        net_needed = max(0.0, gross_qty - stock)
        
        # Case rounding calculations
        if net_needed > 0:
            cases_to_order = math.ceil(net_needed / unit_per_case)
            total_ordered = cases_to_order * unit_per_case
            surplus = total_ordered - net_needed
            cost = cases_to_order * case_price
        else:
            cases_to_order = 0
            total_ordered = 0.0
            surplus = 0.0
            cost = 0.0
            
        order_plan.append({
            "ingredient": ing,
            "description": desc,
            "sku": sku,
            "gross": gross_qty,
            "stock": stock,
            "net": net_needed,
            "cases": cases_to_order,
            "unit": case_unit,
            "surplus": surplus,
            "cost": cost,
            "reasoning": matching_res.reasoning,
            "confidence": matching_res.confidence_score
        })
        
    return order_plan

def main():
    print("\n==============================================")
    print("      CLOUD KITCHEN ORDERING ENGINE")
    print("==============================================")
    
    recipes, catalog, forecasts = load_data()
    days = list(forecasts.keys())
    
    print("Available Forecast Days:")
    for idx, d in enumerate(days, 1):
        print(f"{idx}) {d.title()}")
        
    choice = input("\nSelect day index (1-3): ").strip()
    try:
        day = days[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid choice, defaulting to Monday.")
        day = "monday"
        
    required_ingredients = calculate_forecast_requirements(day, recipes, forecasts)
    
    print(f"\n--- Checking Stock for {day.title()} Menu ---")
    stock_dict = {}
    for ing, gross in required_ingredients.items():
        catalog_info = next((v for v in catalog.values() if v["sku"] == match_ingredient(ing, catalog).matched_sku), {})
        unit = catalog_info.get("case_unit", "units")
        print(f"Gross required for {ing.replace('_', ' ').title()}: {gross:.1f} {unit}")
        stock_val = input(f" -> Enter starting stock on hand ({unit}): ").strip()
        try:
            stock_dict[ing] = float(stock_val) if stock_val != "" else 0.0
        except ValueError:
            stock_dict[ing] = 0.0
            
    order_plan = run_ordering_pipeline(day, stock_dict)
    
    print("\n==========================================================================================")
    print("                               CLOUD KITCHEN DRAFT ORDER")
    print("==========================================================================================")
    print(f"{'Ingredient':<22} | {'Gross':<6} | {'Stock':<6} | {'Net':<6} | {'Supplier SKU (Match)':<32} | {'Order':<8} | {'Surplus':<8} | {'Cost':<7}")
    print("-" * 106)
    
    total_cost = 0.0
    for item in order_plan:
        total_cost += item["cost"]
        ing_name = item["ingredient"].replace("_", " ").title()
        if len(ing_name) > 22:
            ing_name = ing_name[:19] + "..."
            
        sku_desc = f"{item['description']} ({item['sku']})"
        if len(sku_desc) > 32:
            sku_desc = sku_desc[:29] + "..."
            
        order_str = f"{item['cases']}cs" if item['cases'] > 0 else "None"
        surplus_str = f"{item['surplus']:.1f} {item['unit']}" if item['cases'] > 0 else "0.0"
        print(f"{ing_name:<22} | {item['gross']:<6.1f} | {item['stock']:<6.1f} | {item['net']:<6.1f} | {sku_desc:<32} | {order_str:<8} | {surplus_str:<8} | ${item['cost']:<6.2f}")
        
    print("-" * 106)
    print(f"{'TOTAL ESTIMATED ORDER COST':<88} | ${total_cost:.2f}")
    print("==========================================================================================")

if __name__ == "__main__":
    main()
