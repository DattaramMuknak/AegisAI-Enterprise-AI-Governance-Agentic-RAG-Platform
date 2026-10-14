"""
Router Agent — the orchestrator that implements the pipeline from the
architecture diagram:

  User -> Governance Layer (pre-check) -> Retrieval Agent -> Compliance Agent
       -> Response Agent (LLM) -> Risk Agent (post-check) -> Audit Log

If a pre-generation gate trips (blocked-severity prompt injection, or a
policy violation on the prompt itself) the pipeline short-circuits before
ever calling the LLM, saving cost and guaranteeing the bad prompt never
reaches the model.
"""
import time
import uuid
from typing import List

from app.agents import compliance_agent, response_agent, retrieval_agent, risk_agent


def run_pipeline(prompt: str, top_k: int = 4) -> dict:
    trace_id = str(uuid.uuid4())
    start = time.perf_counter()
    agent_path = ["router"]

    # 1. Pre-generation compliance gate
    compliance = compliance_agent.review_prompt(prompt)
    agent_path.append("compliance")

    pii_count = len(compliance.pii_entities)
    hard_block = compliance.injection_detected and len(compliance.injection_matches) >= 2

    if hard_block or compliance.policy_violation:
        latency_ms = int((time.perf_counter() - start) * 1000)
        reason = (
            compliance.policy_reason
            if compliance.policy_violation
            else "Multiple prompt-injection patterns detected in input."
        )
        return {
            "trace_id": trace_id,
            "answer": None,
            "sources": [],
            "agent_path": agent_path + ["blocked"],
            "governance": {
                "risk_score": 90 if compliance.policy_violation else 70,
                "grounding_score": 0.0,
                "pii_detected": compliance.pii_detected,
                "pii_entities": compliance.pii_entities,
                "toxicity_score": 0.0,
                "prompt_injection_detected": compliance.injection_detected,
                "policy_violation": compliance.policy_violation,
                "policy_violation_reason": reason,
                "hallucination_flag": False,
                "governance_decision": "blocked",
                "block_reason": reason,
                "confidence": "Low",
            },
            "latency_ms": latency_ms,
            "token_usage": {},
            "sanitized_prompt": compliance.sanitized_prompt,
        }

    # 2. Retrieval Agent
    retrieved = retrieval_agent.run(compliance.sanitized_prompt, top_k=top_k)
    agent_path.append("retrieval")
    context_chunks: List[str] = [r["chunk"] for r in retrieved]

    # 3. Response Agent (LLM call)
    gen = response_agent.run(compliance.sanitized_prompt, context_chunks)
    agent_path.append("response")
    answer = gen["answer"]
    token_usage = gen.get("token_usage", {})

    # 4. Post-generation policy re-check (answer might introduce a violation
    #    even if the prompt didn't)
    post_violation, post_reason = compliance_agent.review_response(prompt, answer)
    policy_violation = compliance.policy_violation or post_violation
    policy_reason = compliance.policy_reason or post_reason

    # 5. Risk Agent — aggregate scoring + governance decision
    risk = risk_agent.assess(
        prompt=prompt,
        response=answer,
        retrieved_chunks=context_chunks,
        injection_detected=compliance.injection_detected,
        injection_matches=compliance.injection_matches,
        pii_count=pii_count,
        policy_violation=policy_violation,
    )
    agent_path.append("risk")

    # If risk agent decides to block post-generation, withhold the answer
    final_answer = answer
    if risk["governance_decision"] == "blocked":
        final_answer = None
        agent_path.append("blocked")

    latency_ms = int((time.perf_counter() - start) * 1000)

    return {
        "trace_id": trace_id,
        "answer": final_answer,
        "sources": retrieved,
        "agent_path": agent_path,
        "governance": {
            "risk_score": risk["risk_score"],
            "grounding_score": risk["grounding_score"],
            "pii_detected": compliance.pii_detected,
            "pii_entities": compliance.pii_entities,
            "toxicity_score": risk["toxicity_score"],
            "prompt_injection_detected": compliance.injection_detected,
            "policy_violation": policy_violation,
            "policy_violation_reason": policy_reason,
            "hallucination_flag": risk["hallucination_flag"],
            "governance_decision": risk["governance_decision"],
            "block_reason": risk["block_reason"],
            "confidence": risk["confidence"],
        },
        "latency_ms": latency_ms,
        "token_usage": token_usage,
        "sanitized_prompt": compliance.sanitized_prompt,
    }
