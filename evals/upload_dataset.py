import json
import os
from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables from .env
load_dotenv()

def upload_dataset():
    # 1. Initialize Langfuse Client
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
    
    if not (public_key and secret_key):
        print("❌ Langfuse keys are missing. Please add them to your .env file.")
        return
        
    print(f"🔗 Connecting to Langfuse at: {host}")
    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )
    
    # 2. Read evaluation dataset from local JSON
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    dataset_path = os.path.join(base_dir, "data", "eval_dataset.json")
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset file not found at: {dataset_path}")
        return
        
    with open(dataset_path, "r") as f:
        eval_cases = json.load(f)
        
    dataset_name = "community-kitchen-replenishment-benchmark"
    print(f"📦 Creating or fetching dataset: '{dataset_name}'")
    
    # Fetch or create the dataset
    try:
        dataset = langfuse.get_dataset(dataset_name)
        print(f"✨ Found existing dataset '{dataset_name}'.")
    except Exception:
        # If dataset doesn't exist, create it
        dataset = langfuse.create_dataset(
            name=dataset_name,
            description="Benchmark Dataset for Green Kitchen Replenishment Copilot"
        )
        print(f"🆕 Created new dataset: '{dataset_name}'")
        
    # Get existing item IDs to avoid duplicates
    existing_items = set()
    try:
        for item in dataset.items:
            if item.metadata and "id" in item.metadata:
                existing_items.add(item.metadata["id"])
    except Exception as e:
        print(f"⚠️ Could not load existing items: {e}")

    # 3. Upload dataset items
    uploaded_count = 0
    for case in eval_cases:
        case_id = case["id"]
        
        # Check if already uploaded
        if case_id in existing_items:
            print(f"⏭️ Case '{case_id}' already exists in Langfuse dataset. Skipping.")
            continue
            
        print(f"📤 Uploading case '{case_id}': {case['description']}")
        
        # Input parameters for the run
        input_data = {
            "forecast_day": case["forecast_day"],
            "starting_stock": case["starting_stock"]
        }
        
        # Expected outputs for comparison
        expected_output = {
            "expected_orders": case["expected_orders"]
        }
        
        # Additional metadata
        metadata = {
            "id": case_id,
            "description": case["description"]
        }
        
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=input_data,
            expected_output=expected_output,
            metadata=metadata
        )
        uploaded_count += 1
        
    print(f"\n🎉 Successfully verified/uploaded {uploaded_count} dataset items to Langfuse!")
    print(f"👉 View your dataset in Langfuse Cloud Console: {host}/project/.../datasets/{dataset_name}")

if __name__ == "__main__":
    upload_dataset()
