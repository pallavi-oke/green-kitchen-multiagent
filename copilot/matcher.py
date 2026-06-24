import os
import json
from pydantic import BaseModel, Field
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class MatchingResult(BaseModel):
    ingredient: str = Field(description="The input ingredient name")
    matched_sku: Optional[str] = Field(description="The matched supplier SKU, or null if no match exists")
    confidence_score: float = Field(description="Confidence from 0.0 to 1.0")
    reasoning: str = Field(description="Reasoning for the match or lack thereof")

def deterministic_fallback_match(ingredient: str, catalog: dict) -> MatchingResult:
    """A robust local string-matching fallback in case API keys are missing."""
    ing_clean = ingredient.lower().replace("_", " ").strip()
    
    best_sku = None
    best_score = 0.0
    best_match_len = 0
    reason = "No matching keyword found in catalog."
    
    # 1. Try exact match first
    for key, item in catalog.items():
        key_clean = key.lower().replace("_", " ").strip()
        if ing_clean == key_clean:
            return MatchingResult(
                ingredient=ingredient,
                matched_sku=item["sku"],
                confidence_score=1.0,
                reasoning=f"Deterministic exact match found on catalog key: '{key}'"
            )
            
    # 2. Try substring match (longest matching key wins to handle gf/sub-category specificity)
    for key, item in catalog.items():
        key_clean = key.lower().replace("_", " ").strip()
        desc_clean = item["description"].lower()
        
        if key_clean in ing_clean or ing_clean in key_clean:
            if len(key_clean) > best_match_len:
                best_sku = item["sku"]
                best_match_len = len(key_clean)
                best_score = 0.9
                reason = f"Deterministic best substring match found on catalog key: '{key}'"
                
        elif ing_clean in desc_clean:
            if len(desc_clean) > best_match_len:
                best_sku = item["sku"]
                best_match_len = len(desc_clean)
                best_score = 0.8
                reason = f"Deterministic match found in description: '{item['description']}'"
                
    return MatchingResult(
        ingredient=ingredient,
        matched_sku=best_sku,
        confidence_score=best_score,
        reasoning=reason
    )

def match_ingredient(ingredient: str, catalog: dict, api_key: Optional[str] = None, trace_id: Optional[str] = None) -> MatchingResult:
    """Uses Gemini to fuzzy match a recipe ingredient to a supplier catalog item, with Langfuse tracing support."""
    effective_api_key = api_key or os.getenv("GOOGLE_API_KEY")
    
    if not effective_api_key:
        return deterministic_fallback_match(ingredient, catalog)
        
    try:
        catalog_summary = []
        for key, val in catalog.items():
            catalog_summary.append(f"SKU: {val['sku']} | Description: {val['description']} | Pack: {val['case_size']} {val['case_unit']}")
        catalog_str = "\n".join(catalog_summary)
        
        # Configure Langfuse tracing if keys are present
        callbacks = []
        handler = None
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            from langfuse.callback import CallbackHandler
            handler = CallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
            )
            callbacks.append(handler)
            
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=effective_api_key,
            temperature=0.0
        ).with_structured_output(MatchingResult)
        
        prompt = f"""
        You are the cloud kitchen inventory agent. 
        Map this recipe ingredient: "{ingredient}" to the single best matching SKU in our B2B Supplier Catalog.
        
        Catalog Options:
        {catalog_str}
        
        If no item in the catalog makes sense, set 'matched_sku' to null.
        """
        
        config = {"callbacks": callbacks} if callbacks else {}
        if trace_id:
            config["run_id"] = trace_id
            
        res = llm.invoke(prompt, config=config)
        if handler:
            handler.flush()
        return res
        
    except Exception as e:
        fallback = deterministic_fallback_match(ingredient, catalog)
        fallback.reasoning = f"API Error ({str(e)}). Fell back to string match: {fallback.reasoning}"
        return fallback
