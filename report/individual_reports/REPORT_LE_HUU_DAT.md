# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Hữu Đạt
- **Student ID**: 2A202600630
- **Date**: June 1, 2026

---

## I. Technical Contribution (15 Points)

*Describe the concrete code and design tasks you completed for this lab.*

- **Module(s) Worked On**:
  - `src/agent/agent.py`
  - `backend/agent/agent.py`
  - `backend/tools/`
  - `backend/agent/system_prompt.txt`
- **Implemented Features**:
  - Integrated ReAct reasoning into the agent loop so the model alternates between `Thought`, `Action`, and `Observation`.
  - Extended the backend tool set with concrete task handlers for itinerary, weather, prices, and VinWonders knowledge retrieval.
  - Added structured tool invocation handling, including argument validation and clear tool response formatting.
- **Key Code Changes**:
  - Refactored the agent prompt to enforce ReAct syntax and avoid free-form answers during planning.
  - Built ReAct tool dispatch support in `backend/agent/agent.py` so actions are executed by the correct backend tools.
  - Improved observation feedback loops so the agent can decide follow-up actions after receiving tool results.
- **Documentation / Collaboration**:
  - Updated the lab report and README sections to document the ReAct agent behavior and tool usage.
  - Coordinated with teammates to align tool definitions and keep the agent prompt consistent across backend and frontend.

---

## II. Debugging Case Study (10 Points)

*Choose one concrete failure from the lab, explain how you diagnosed it, and describe the fix.*

- **Problem Description**:
  - The ReAct agent sometimes generated invalid tool calls or repeated the same action, which prevented it from returning a final answer.
- **Log Source**:
  - The backend `main.py` and agent logs showed repeated `Action:` entries with the same tool name and missing or malformed JSON arguments.
- **Diagnosis**:
  - The prompt template allowed too much free-form reasoning output, so the LLM occasionally produced invalid `Action` syntax.
  - Tool input validation was incomplete, causing the agent to retry a tool instead of using the observation to proceed.
- **Solution**:
  - Tightened the system prompt in `backend/agent/system_prompt.txt` to require exact ReAct formatting and explicit tool selection.
  - Added argument validation for tool inputs and clear error observations so the agent could choose a different tool when needed.
  - Added a safety check in the agent loop to stop repeated actions after a small number of iterations and return a diagnostic response.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the difference between a plain chatbot and an agent that uses reasoning plus tools.*

1. **Reasoning**:
   - The ReAct structure forces the agent to think about whether a tool is needed and which one to use, instead of answering directly.
   - This makes the model more transparent and better suited for multi-step travel planning tasks.
2. **Reliability**:
   - A ReAct agent can handle compound queries by breaking them into tool calls, but it depends heavily on a well-defined tool interface.
   - A plain chatbot is often faster for simple questions, while the ReAct agent is more reliable for queries requiring external data or multi-step decisions.
3. **Observation Feedback**:
   - The agent uses `Observation` results to adapt its next action, which improves iterative reasoning and reduces hallucinations.
   - This feedback loop is a key advantage of ReAct, especially for cases where the first tool call does not fully solve the task.

---

## IV. Future Improvements (5 Points)

*Describe how you would extend this project toward a production-ready agent system.*

- **Scalability**:
  - Add a dynamic ReAct tool registry so new tools can be registered without modifying core agent logic.
  - Support parallel tool execution for independent actions when the task allows it.
- **Safety**:
  - Add a ReAct supervisor or validation layer that checks tool calls before execution to block invalid or unsafe actions.
  - Normalize and sanitize all tool inputs and outputs to prevent the agent from acting on bad data.
- **Performance**:
  - Cache frequent tool results and summarize repeated observations before sending them back to the agent.
  - Limit prompt length by summarizing prior tool outputs while preserving the ReAct reasoning context.

---
