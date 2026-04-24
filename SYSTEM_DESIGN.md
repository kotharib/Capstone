# Banking Support AI System Design

## System Overview

The system is designed as a regulated, customer-facing banking support assistant that provides guidance-only information while preventing any transaction or approval activity.

Core components:
- **LLM**: Generates natural language responses using the selected model and prompt strategy.
- **Policy Engine**: Applies safety rules for transactional, regulatory, and PII-sensitive requests.
- **Retrieval (RAG)**: Uses document embeddings and semantic search to ground answers in bank policy and product information.
- **Escalation**: Detects high-risk or ambiguous queries and routes them to human specialists.
- **Logging**: Captures interactions, decisions, and audits without storing PII.

Boundaries between AI and human agents:
- AI handles informational banking support only.
- Human agents are explicitly required for transaction requests, approvals, account changes, and legal/regulatory advice.
- The agent refuses or escalates when safety or scope is uncertain.

What the system explicitly does:
- Answers questions about banking products, account features, fees, documentation, and service processes.
- Provides guidance-only recommendations, not approvals.
- Uses retrieval to ground answers in authoritative documents.
- Keeps conversation context for better follow-up interactions.
- Collects user feedback for adaptive behavior.

What the system does not do:
- No money movement or funds transfers.
- No account approvals, credit underwriting, or loan decisions.
- No legal, tax, or investment advice.
- No disclosure of customer PII or sensitive account details.
- No automated changes to customer accounts.

## User Interaction Flow

1. User submits a question.
2. The system sanitizes input and checks for PII.
3. Safety rules are evaluated:
   - Transactional request detection
   - Regulated advice detection
   - Ambiguity and high-risk intent
4. If safe, the system constructs context from short-term memory and executes retrieval-enhanced response generation.
5. The system returns a concise, guidance-only answer.
6. If the request is high-risk or out-of-scope, the system refuses and escalates to a human specialist.
7. User feedback is optionally captured to refine future responses.

Decision points where safety rules are applied:
- Input sanitization and PII detection
- Transactional/regulatory keyword matching
- Escalation criteria before any LLM call
- Memory reset triggers and conversation context updates

Normal flow example:
- User asks: "What is the difference between checking and savings accounts?"
- System checks scope, builds conversation context, retrieves supporting docs, and answers with product guidance.

Escalated flow example:
- User asks: "Transfer $500 from my savings to checking."
- System flags the request as transactional and responds: "I can only provide informational guidance. Please contact a human specialist for transaction assistance."

## Safety & Guardrail Mechanisms

How transactional and regulated requests are detected and refused:
- Keyword-based detectors identify transfer, payment, approval, investment, legal, and tax-related requests.
- If matched, the system returns a refusal and marks the interaction for human review.

How hallucination risk is minimized:
- Use of RAG with retrieved documents reduces ungrounded responses.
- Prompt strategy emphasizes safety and honesty.
- The system avoids speculative language and returns safe refusals on uncertainty.

How ambiguity and high-risk intent are identified:
- Patterns for account numbers, personal identifiers, and regulatory terms trigger escalation.
- Ambiguous queries are evaluated for whether they contain transactional or out-of-scope concepts.
- When in doubt, the system prefers human escalation.

## Data Handling & Privacy

What data is allowed in prompts:
- Non-PII banking questions and product inquiries.
- Context from recent user turns when memory is enabled.
- Retrieved document excerpts from the knowledge base.

How PII is filtered, masked, or rejected:
- Input is scanned for SSN, card-number, phone-number, and account-number patterns.
- Identifiers are redacted from prompts and the user is asked to rephrase without sensitive data.
- The system never logs raw user input that contains PII.

Logging strategy that avoids PII storage:
- Logs include decision metadata, safety status, escalation reasons, and tool results.
- No raw PII is persisted in audit or telemetry logs.
- Feedback logs store ratings and comments only, without direct account details.

## Assumptions & Design Trade-offs

Assumptions:
- Upstream systems provide accurate product and policy documents for retrieval.
- Users seek guidance only and will not intend the agent to perform transactions.
- The LLM provider is available and secured with proper API credentials.
- Data sources are regularly updated for policy accuracy.

Trade-offs:
- Safety vs. helpfulness: The system errs on the side of escalation rather than risky answers.
- Memory vs. privacy: Short-term context improves follow-up quality, but long-term retention is deliberately limited.
- Grounding vs. latency: RAG improves accuracy at the cost of extra retrieval time, which is acceptable for regulated support.
- Simplicity vs. automation: The system intentionally avoids transactional automation to preserve safety boundaries.
