# Draft LinkedIn Post: Green Kitchen 🥗 💰 ⏳

Here is the final, high-impact, completely defensible LinkedIn post draft for your demo:

***

**Can a \$2/mo AI agent save a community meal program 12.5 hours of volunteer time and \$3,600 in food waste?** 🥗 💰 ⏳

I built **Green Kitchen** — a calibrated AI replenishment copilot designed specifically for community and institutional meal programs to cut food waste and recover lost budgets.

To build it, I pair-programmed with **Antigravity** (the agentic AI coding assistant from **@Google DeepMind**) using **LangChain** and **Gemini 2.5 Flash**, and deployed the service on **@Google Cloud** Run.

Non-profits operate on razor-thin grant budgets. Throwing away food due to over-ordering wastes scarce funds that could feed hungry families. Bulk ordering is usually done on messy spreadsheets, but simple recipe scaling fails in the real world because it ignores pantry inventory on hand and wholesale bulk packaging.

🎥 **Watch the 2-minute demo below to see how it works:**
*   🎙️ **Voice Logging (Hands-Free):** Volunteers log stock counts by voice while prepping food (Web Speech API).
*   🧠 **Allergen-Aware SKU Matching:** A Gemini 2.5 Flash agent maps ingredients to wholesale supplier items (like distinguishing gluten-free vs. normal buns) to prevent critical safety hazards.
*   🛡️ **Governance:** A Human-in-the-Loop gate for the Director, backed by a local **LLM-as-a-Judge** evaluation harness.
*   📊 **Observability & Tracing:** Full execution traces, token costs, and latency monitoring powered by **@Langfuse**.

📈 **The PM Business Case (Modeled):**
Running this Gemini 2.5 Flash agent daily costs just **\$2.01 a month** (hosting + tokens). Yet, modeled projections show it reduces order preparation time from **~30 minutes to under 5 minutes per cycle** (saving **12.5 hours/month** of staff time) and cuts food waste by **8%** (**\$3,600/month** on a \$45k food spend).

For a kitchen serving 500 meals/day, that recovered budget is enough to feed **40 additional people per day** (1,200/mo)!

Try the live dashboard here: https://chef-copilot-996894821314.us-central1.run.app

What do you think about using agentic workflows to solve real-world operational challenges? 👇

#AIAgents #GenerativeAI #NonProfitTech #Sustainability #TechForGood #GoogleCloud #Gemini #LangChain #Langfuse #GoogleDeepMind
