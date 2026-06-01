
Group Report: Lab 3 - Production-Grade Agentic System
Team Name: VinWonders AI Navigators
Team Members:
Công Thái - 2A202600949
Lê Hữu Đạt - 2A202600630
Nguyễn Đông Anh - 2A202600760
Lê Trí Nguyên - 2A202600651
Trảo An Huy - 2A202600819

Deployment Date: 2024-05-22
1. Executive Summary
The goal of this project was to develop a specialized ReAct Agent to serve as a smart concierge for VinWonders Wave Park & Water Park. Unlike a traditional chatbot, this agent can access real-time weather data, retrieve specific park regulations from a Vector Database (RAG), and perform precise ticket pricing calculations.
Success Rate: 88% on 25 complex test cases.
Key Outcome: Our agent solved 60% more multi-step queries than the chatbot baseline, particularly in scenarios requiring cross-referencing weather conditions with pricing logic and park policies.
2. System Architecture & Tooling
2.1 ReAct Loop Implementation
We implemented the Thought-Action-Observation loop using LangGraph to maintain state and control flow:
Thought: The LLM analyzes the user's intent (e.g., "It's sunny, how much for 2 adults?").
Action: The agent selects and calls the relevant tools (get_weather and ticket_calculator).
Observation: The system returns tool outputs (e.g., "36°C" and "500,000 VND").
Final Response: The agent synthesizes a helpful, natural language answer for the user.
2.2 Tool Definitions (Inventory)
Tool Name	Input Format	Use Case
get_weather	json {"location": "string"}	Retrieves real-time weather to suggest outdoor/indoor activities.
search_vin_info	string	RAG-based search for park rules, height requirements, and schedules.
ticket_calc	json {"adults": int, "kids": int}	Calculates total price based on current seasonal rates and age groups.
2.3 LLM Providers Used
Primary: GPT-4o-mini (High tool-calling accuracy and low latency).
Secondary (Backup): Gemini 1.5 Flash (Used for fallback reasoning if rate limits are hit).
3. Telemetry & Performance Dashboard
Metrics collected during the final evaluation of 50 varied user prompts:
Average Latency (P50): 2100ms (Includes RAG retrieval and API tool execution).
Max Latency (P99): 6200ms (Occurred during deep multi-turn reasoning loops).
Average Tokens per Task: 480 tokens.
Total Cost of Test Suite: $0.12.
4. Root Cause Analysis (RCA) - Failure Traces
Case Study: Type Mismatch in Tool Argument
Input: "My family has 2 adults and one child who is 1.2m tall."
Observation: The agent attempted to call ticket_calc(adults=2, kids="1.2m"). The tool failed because the kids argument expected an integer (count), not a string (height).
Root Cause: The system prompt and tool docstrings did not explicitly instruct the agent on how to map "height" to "ticket count" based on park policy.
Resolution: Updated the tool description to: "Input the number of children only. If the user mentions height, apply policy: <1m = free, >1m = 1 child ticket."
5. Ablation Studies & Experiments
Experiment 1: Prompt v1 (Basic) vs Prompt v2 (Few-Shot)
Diff: Added 3 Few-Shot examples demonstrating correct JSON formatting for tool calls.
Result: Reduced "Invalid Tool Argument" errors by 45%.
Experiment 2 (Bonus): Chatbot vs Agent
Case	Chatbot Result	Agent Result	Winner
Refund Policy	General/Generic info	Specific policy from VectorDB	Agent
Total Price Calc	Often made math errors	100% accurate via Python Tool	Agent
Simple Greeting	Fast & Friendly	Slightly slower (overhead)	Chatbot
6. Production Readiness Review
Steps required to transition from Lab to Production:
Security: Implement Input Sanitization to prevent Prompt Injection attempts aimed at bypassing ticket fees.
Guardrails: Hard-coded a Max 5-loop limit in LangGraph to prevent infinite loops and runaway API costs.
Scaling: Migrate from local ChromaDB to Pinecone for high-concurrency vector searches.
Monitoring: Integration of LangSmith for real-time trace monitoring and hallucination detection in production.