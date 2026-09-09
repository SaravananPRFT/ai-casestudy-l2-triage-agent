# Reflection — Order Triage Agent

## 1. What was built

A LangGraph triage agent for NorthPeak Commerce that processes support tickets end-to-end. The graph has five nodes: `classify` (LLM — issue category), `route` (pure Python — priority ladder and escalation rules), `draft` (LLM — reply for Marcus), `escalate` (LLM — internal summary for Priya), and `audit` (structured JSONL record per decision). Routing is deliberately kept outside the LLM: a deterministic function of category and tier in `policy_engine.py`, covered by 45 unit tests.

The agent processed all 54 tickets with 0 errors and scored 12/12 (100%) on category, priority, and route against the labeled dev set: 18 escalated to Priya, 36 to Marcus with draft replies. Observability: structured JSONL audit records and Portkey gateway traces (prompt, response, tokens, latency per run).

## 2. Why this approach

The policy has one non-obvious property: priority must be computed before routing is evaluated, because the premium tier bump can push a ticket over the escalation threshold. ORD-10015 (`premium` + `address_change`) is the clearest example — base priority MEDIUM, bumped to HIGH, then routed to Priya because premium + HIGH triggers rule 2. Evaluating routing at the base priority would produce the wrong answer. Encoding this in pure Python with an explicit test (`test_triage_premium_address_change`) makes the ordering a hard constraint rather than a convention.

The LLM scope was kept narrow on purpose. Classification is genuinely a language task — the model must read "someone used my saved card" and infer `fraud_alert` rather than `payment_issue` or `cancel_request`. Drafting a reply also benefits from language generation. But routing is a rule table. Asking an LLM to apply the escalation rules creates a path to inconsistency and makes the system harder to test. The separation means the policy can be updated by editing one Python file, and the change is immediately covered by the existing test suite.

## 3. What failed

**Wrong LLM client for the gateway.** The initial implementation used `ChatAnthropic` from `langchain-anthropic`. Perficient's Portkey gateway exposes an OpenAI-compatible endpoint (`/v1/chat/completions`), not Anthropic's native messages endpoint. `ChatAnthropic` sent requests in Anthropic format, the gateway returned a response in OpenAI format, and the client tried to iterate over a null `content` field — crashing with `TypeError: 'NoneType' object is not iterable`. The error gave no hint that the root cause was a format mismatch.

**Test mocking was too deep.** The first version of `test_agent_loop.py` tried to mock at the `ChatPromptTemplate` and `with_structured_output` level. Because the draft tool imports `get_llm` from `src.llm.client` (not from `src.agent.nodes`), the patch at `src.agent.nodes.get_llm` did not intercept the draft node's LLM call — the real `ChatAnthropic` client was instantiated and failed on missing API credentials. The mocking approach was too fragile for a multi-module chain.

**Windows console encoding.** Both `run_triage.py` and `eval/evaluate.py` used Unicode arrows and tick marks in `print` statements. On a Windows terminal with cp1252 encoding these raised `UnicodeEncodeError` and aborted the run after all the actual work had completed — so the results were computed but not displayed.

## 4. How each failure was fixed

**LLM client**: Examined how CertMasterAI (another project using the same Portkey gateway) calls the API. It uses `AsyncOpenAI` with `base_url=PORTKEY_BASE_URL` and `api_key=PORTKEY_API_KEY`, then calls `client.chat.completions.create(model=CLAUDE_MODEL, ...)`. Replaced `ChatAnthropic` with `ChatOpenAI` using the same parameters. The gateway returned a valid response on the first test call.

**Test mocking**: Moved the mock boundary up to the graph node functions themselves (`classify_node`, `draft_node`, `escalate_node`, `audit_node`), using `patch("src.agent.graph.classify_node", side_effect=mock_fn)`. This tests graph wiring and state propagation — which is what the loop tests should verify — without touching the LLM stack at all. The LLM calls are tested separately in `test_nodes.py` with focused mocks.

**Encoding**: Added `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at the top of both scripts, and replaced Unicode symbols with ASCII equivalents (`->` instead of `→`, `OK`/`FAIL` instead of `✓`/`✗`) in the progress output.

## 5. What I would do differently

The classification prompt currently asks the LLM to return a single category with no explicit handling for tickets that genuinely sit between two categories. The `multi_issue` flag and the `resolve_multi_issue` function in `policy_engine.py` handle the downstream routing, but the classify node still returns only one category — the LLM's best guess at the highest-priority one. A better design would ask the LLM to return all plausible categories and let the policy engine select from them using the documented rule. This would make the multi-issue logic fully transparent in the audit trail rather than partially inferred.

I would also run the full queue before writing the policy engine unit tests rather than after. Several edge cases (ORD-10044's dual-issue note, ORD-10054's minimal-text ticket) only became visible when the actual ticket text was seen. Writing tests against the real data, even just the labeled subset, earlier would have caught the multi-issue gap sooner.

## 6. Business impact

The agent removes approximately 3–4 minutes of triage time per ticket — roughly 3 hours of Marcus's time redirected from reading and categorising to actual customer interaction across the 54-ticket queue. For Priya, every money-movement and fraud ticket arrives with a pre-written escalation summary and a documented rationale, reducing the cognitive load of reviewing an urgent queue.

The audit log is the more durable output. Every routing decision is recorded with category, confidence, priority, route, flags, and a one-line reason. Dev can query it to measure queue composition, spot consistently low-confidence categories, and verify policy application on any ticket without asking Marcus or Priya to reconstruct what happened.

The most important constraint enforced is the one the policy document states explicitly: `text_note` is data, not an instruction. Customers who write "this is urgent, escalate now" get the same classification as those who do not. The `customer_directed` flag makes every such attempt visible to Dev in the audit trail.

---

**Declared effort**: approximately 11 hours across four sessions. Items cut to stay within scope: async concurrent processing of the queue (sync is sufficient for 54 tickets), RAG over the policy document (fits in context), and application-level retry logic (handled by the Portkey gateway).
