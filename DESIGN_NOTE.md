# Design Note — Order Triage Agent

## Stack choice

**LangGraph** was specified in the case brief ("solid first LangGraph build"). The graph is small enough that a simpler approach — a plain loop — would also work, but LangGraph gives us the conditional edge, explicit state type, and per-node tracing for free, which satisfies both the architecture and observability requirements.

**LLM provider**: Claude Sonnet 4.6 via Perficient's Portkey gateway (`portkeygateway.perficient.com/v1`). The gateway exposes an OpenAI-compatible `/v1/chat/completions` endpoint, so `ChatOpenAI` (not `ChatAnthropic`) is the correct LangChain client. Using `ChatAnthropic` against the same URL returns a null content body because the response format does not match what the Anthropic client parses.

**LLM scope**: The LLM is used in exactly two places — `classify_node` (issue categorisation) and `draft_node` / `escalate_node` (reply or escalation text). The routing decision (`route_node`) and priority calculation are pure Python in `policy_engine.py`. This is intentional: routing must be deterministic, auditable, and independently testable without an API key.

---

## Policy composition order

The triage policy has three rules that must be applied in a specific sequence. Getting the order wrong changes the answer on a subset of tickets.

**Correct order:**

1. Look up **base priority** from the category table.
2. Apply the **premium-tier bump** (if `customer_tier == "premium"`, move priority one rung up the ladder, capped at URGENT).
3. Evaluate the **routing rules** against the *final* (post-bump) priority.

**Why order matters — concrete example:**

ORD-10015: `customer_tier=premium`, category=`address_change`.

| Step | Value | Rule |
|---|---|---|
| Base priority | MEDIUM | address_change base |
| After premium bump | HIGH | MEDIUM → HIGH |
| Route check | **priya** | premium + HIGH → escalate |

If routing were evaluated before the premium bump (i.e., checking MEDIUM against the threshold), the result would be `marcus` — wrong. The test `test_triage_premium_address_change` in `test_policy_engine.py` pins this behaviour explicitly.

Similarly ORD-10045 and ORD-10046: `premium` + `refund_request` (base MEDIUM → HIGH after bump) both correctly escalated to Priya. A standard or plus customer with `refund_request` stays with Marcus at MEDIUM.

---

## Multi-issue ticket rule (policy gap)

The policy (`personas.md`, "Where this policy is silent") states "one issue per ticket" but acknowledges real tickets don't always cooperate.

**Documented rule**: When a ticket describes more than one issue, classify as the category that yields the highest priority *after* applying the premium bump for the customer's tier. On a priority tie, take the category that appears first in the note text (preserves reading order, which usually reflects the customer's primary concern).

**Consistency**: This rule is implemented in `policy_engine.resolve_multi_issue()` and is called whenever `classify_node` sets the `multi_issue` flag. The same function is used in unit tests to verify the rule is applied identically every time.

**Example in queue**: ORD-10044 (standard tier) — the note describes both a delayed delivery and a suspicious charge. `fraud_alert` outranks `delivery_delay` (URGENT vs MEDIUM), so the ticket is classified as `fraud_alert` and escalated. The rationale field records `flags=multi_issue` so Dev can see the ambiguity.

---

## Customer-directed tickets

Some notes attempt to instruct the agent on how to handle the ticket ("this is urgent, please escalate immediately" or "this is a low-priority question"). Per the policy authority section, the `text_note` is data, not an instruction.

The classify prompt includes an explicit authority rule: classify from the facts of the complaint only. If the note attempts to direct handling, the `customer_directed` flag is set in the rationale so Dev can see the attempt, but it does not change the category or route.

---

## What was deliberately not built

**RAG over the policy document**: The full escalation policy fits comfortably in the LLM's context window. Embedding it in ChromaDB and retrieving chunks would add latency and a dependency without improving accuracy. If the policy grew to dozens of pages, RAG would be worth it; for this case it is premature.

**Async graph execution**: `graph.ainvoke` would allow concurrent ticket processing. For a 54-ticket batch the wall-clock difference is small and sync execution simplifies testing. Async can be added later by swapping `graph.invoke` for `await graph.ainvoke` in `run_triage.py`.

**Retry/backoff on LLM calls**: The Portkey gateway handles retries on the infrastructure side. Adding application-level retry logic would duplicate that without benefit for this submission.
