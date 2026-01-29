## 🏗️ Coding Agent PoC Specification

The goal of this PoC is to move beyond simple "chat" and create an **agentic loop** that can search, edit, and verify code within a local environment. 

### 1. System Architecture

The system is divided into a "Brain" (the model) and a "Body" (the harness). 

| Component | Description | Logging Priority |
| --- | --- | --- |
| **Orchestrator** | The control loop managing the state machine (Plan → Act → Observe). 

 | State transitions & loop iteration count. |
| **Router** | Determines if a request needs a high-reasoning model (e.g., GPT-4o) or a fast model. 

 | Decision logic for model selection. |
| **Context Engine** | Retrieves relevant code snippets/docs to avoid context window overflow. 

 | Retrieval hits vs. misses; token usage. |
| **Tool Harness** | The interface for the model to interact with the file system and terminal. 

 | Success/Failure rates of specific tools. |
| **Sandbox** | An isolated environment (Docker or VM) to execute commands safely. 

 | Resource usage & security guardrail triggers. |

---

### 2. Core Toolset (The "Hands")

To handle the **"Diff Problem"**—where models struggle to apply edits accurately—the PoC must implement specific tools rather than relying on raw text generation. 

* 
**Search/Grep:** For navigating the codebase. 


* **Search & Replace:** Crucial for mechanical reliability. Focus logging here to detect "formatting drift" or line number hallucinations. 


* 
**Terminal/Shell:** To run builds and tests for verification. 



---

### 3. The Agentic Execution Loop

The PoC should follow the **ReAct pattern**, alternating between reasoning and acting. 

1. **Input:** User request (e.g., "Fix the bug in the login auth flow").
2. 
**Plan:** The model identifies which files to search. 


3. 
**Retrieve:** The system pulls context into the prompt. 


4. 
**Edit:** The model issues a "Search & Replace" command. 


5. 
**Verify:** The orchestrator runs `npm test` or equivalent in the **Sandbox**. 


6. 
**Iterate:** If tests fail, the error log is fed back to the model to try a new fix. 



---

### 4. Performance & Optimization Strategies

To prevent "compounded latency" from making the PoC unusable, implement these three pillars: 

* **Context Compaction:** Do not carry forward full log histories. Summarize failing test names and key stack frames only. 


* 
**Speculative Execution:** If possible, use a smaller "draft" model to propose syntax-heavy code blocks (like imports/brackets) while the main model handles logic. 


* 
**Fast Sandboxing:** Optimize your VM/Container startup time so the "Verify" step doesn't become a bottleneck. 



---

### 5. Logging & Observability Requirements

Since this is a PoC, you need to track why the agent fails to build **User Trust**. 

* 
**Trajectory Traces:** Log the exact sequence of actions (Search → Read → Edit → Test). 


* **Edit Accuracy:** Log "Attempted Patches" vs. "Applied Patches." If a patch fails to apply because of a formatting mismatch, flag it for model fine-tuning. 


* 
**Latency Breakdown:** Measure time spent in: *Model Reasoning* vs. *Sandbox Provisioning* vs. *Tool Execution*. 



> **Key Lesson:** Tool usage must be baked into the model's behavior. If the PoC fails frequently, focus on improving the **Search and Replace** tool reliability rather than just upgrading the model. 