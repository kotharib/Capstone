# Production Design Specification
## AI Banking Support & Advisory Agent (Non-Transactional)  
### Internal Application — 1-Week Delivery

**Project Classification:** Internal Production Application (Controlled Deployment)  

**Deployment Model:** Internal/controlled environment, designed for later productionization  
**Core Tech Stack:** Streamlit (UI) | Python (backend) | SQLite (persistence) | ChromaDB (retrieval) | Langfuse (observability)  

---

## 1. Primary User Persona & Workflow

### Primary Persona: Karen (Retail Banking Customer)

**Profile:**
- Age: 42, employed, moderate banking sophistication
- Pain point: Calls support with routine questions; waits 20+ minutes on hold
- Goal: Quick, clear answers about products and processes before committing to a decision or speaking with a specialist
- Typical behavior: Researches products online first; uses chat before calling support; values clarity and transparency

**Daily Workflow:**

```
Morning: Karen considering switching to premium checking account
  ↓
Visits bank website → Sees "Chat with AI Advisor"
  ↓
Asks: "What's the difference between premium and standard checking?"
  ↓
Receives clear, sourced explanation
  ↓
Asks follow-up: "What if I don't keep the minimum balance?"
  ↓
Gets policy clarification
  ↓
Decision: Opens account online, OR asks to speak with advisor
  ↓
Satisfied: Problem solved (either path)
```

**Where It Fits:**
- **Before** human interaction: Self-service for informational queries
- **Instead of** FAQ browsing: Natural language questions vs. searching docs
- **Alongside** human agents: Handles routine volume; frees specialists for complex issues
- **Reduces** support queue: 60–70% of calls are routine product questions

### Why Streamlit is Appropriate

| Criterion | Why Streamlit Works |
|-----------|-------------------|
| **Speed to Market** | Rapid iteration; UI built in Python (team expertise) |
| **Simplicity** | Natural conversation interface; familiar chat UX |
| **Maintainability** | Entire app in single language (Python); no frontend/backend split |
| **Scalability Path** | Can port to production chat (Intercom, Zendesk) without safety logic rework |
| **Internal Deployment** | Perfect for controlled environment; easy to add auth, logging, analytics later |
| **Integration** | SQLite, ChromaDB, Langfuse all integrate cleanly with Python backend |
| **Cost** | Free; can self-host; no vendor lock-in for core logic |

**Limitation Acknowledged:** Streamlit is not designed for high-concurrency production (100K+ simultaneous users). For productionization, backend logic stays the same; UI migrates to production chat framework (FastAPI + React, etc.). **This is acceptable for internal deployment.**

---

## 2. Exact Problem Definition & Scope

### Problem to Be Solved

**The Core Problem:**
Bank customers have routine questions about products, policies, and processes that they cannot answer by themselves via static FAQs. Current support channels:
- **Phone support:** Long wait times (15–30 min), limited hours, expensive per-call cost
- **Web FAQs:** Hard to navigate; customers don't find relevant answers; outdated
- **Email support:** Slow response time; not suitable for time-sensitive questions

**Result:** Customer frustration, support cost overrun, poor experience

**Why This Is Non-Trivial in Regulated Banking:**
1. **Regulatory risk:** Inaccurate information about fees, rates, or policies violates Reg Z (TILA/RESPA), Reg E (funds transfers)
2. **Liability risk:** System could inadvertently provide financial/legal advice (SEC, IRS, state law exposure)
3. **Privacy risk:** System could expose PII in logs or responses (GDPR/CCPA)
4. **Compliance complexity:** All responses must be traceable to source documents; AI cannot invent details

**Why AI Is Appropriate (Not Just Static FAQ):**
- ✓ Natural language understanding: "What do I pay for overdraft protection?" vs. "overdraft FAQ" deep in website
- ✓ Context awareness: Can answer follow-up questions ("What about without the protection?")
- ✓ Conciseness: Extracts relevant answer from long policy documents automatically
- ✓ Guidance capability: "Here's what you need to do next" (procedural guidance, not advice)
- ✓ Accessibility: Available outside business hours; instant response

**AI Is NOT Appropriate For:**
- ✗ Transactions (requires identity verification, approval workflows)
- ✗ Account-specific decisions ("Should I open this account given my situation?")
- ✗ Legal/tax/investment advice (requires licensed professional)
- ✗ Complaint resolution (requires human investigation and authority)

---

### Explicitly Out of Scope

| Category | Why Out of Scope | System Response |
|----------|------------------|-----------------|
| **Transactions** | No access to core banking systems; liability and compliance risk | "I can't move money. Please log in to your account or speak with an agent." |
| **Account Changes** | Requires identity verification and approval authority | "Account changes need verification. Please log in or call [number]." |
| **Regulatory Advice** | Legal (contract interpretation, dispute claims); tax (deductions, strategy); investment (security recommendations) | "I can't advise on this. Please consult a [professional] or contact an agent." |
| **Personalized Guidance** | "Based on my credit score, should I..." implies personal advice | "This depends on your situation. An advisor can discuss options with you." |
| **Credit Decisions** | Access to credit scoring system; implies decision-making logic | "Your decision depends on several factors. Contact an agent to discuss." |
| **Identity Verification** | Not scoped for MVP; assume upstream authentication | "For security, confirm your identity with an agent." |
| **Real-Time Data** | No integration with core banking system | "For current account info, please log in." |

---

## 3. Inputs, Outputs, Constraints & Assumptions

### Inputs: What the System Accepts

**User Inputs (Streamlit):**
- ✓ Natural language questions (text, up to 2000 characters for MVP)
- ✓ Follow-up questions in conversation context
- ✓ Clarification requests ("Tell me more about X")
- ✓ Emotional/urgent language (flagged for escalation, not answered)

**Rejected Inputs:**
- ✗ Questions containing PII (SSN, account number, full name in personal context)
- ✗ Transactional requests ("Transfer $500", "Approve this payment")
- ✗ Requests for identity verification or security bypass

**Policy Inputs (Admin/Curation):**
- ✓ Product documentation (marketing materials, feature lists)
- ✓ Fee schedules (published rates, charges)
- ✓ Policy documents (eligibility, procedures, terms)
- ✓ Regulatory summaries (non-legal interpretation, public FAQs)

**Rejected Policy Inputs:**
- ✗ Internal compliance memos or legal opinions
- ✗ Customer data or metadata
- ✗ System configuration or authentication details

---

### Outputs: What the System Can Respond With

**Allowed Response Types:**

| Type | Example | Safety |
|------|---------|--------|
| **Product Explanation** | "Our Premium Checking includes X features, Y rate, Z fees" | ✓ Factual; cites source; no assumption |
| **Policy Clarification** | "The overdraft fee is $35 per occurrence; here's how to avoid it" | ✓ Cites published policy; actionable |
| **Procedural Guidance** | "Here's how to apply: 1) Start here, 2) Submit this, 3) Expect this timeline" | ✓ Steps; no advice; no assumption |
| **Eligibility Threshold** | "Standard checking requires $0 minimum; Premium requires $5,000" | ✓ General; no customer-specific qualification |
| **Educational Info** | "FDIC insurance protects deposits up to $250,000" | ✓ Public regulatory info; no advice |
| **Escalation** | "This needs specialist review. I'll connect you or provide a number" | ✓ Clear handoff; maintains service continuity |

**Disallowed Response Types:**

| Type | Why Not | Example (WRONG) |
|------|---------|-----------------|
| **Personalized Advice** | Regulatory risk; implies recommendation | "Given your risk tolerance, you should invest in..." |
| **Account Inference** | Privacy risk; hallucination risk | "Customers like you typically benefit from..." |
| **Guarantee** | Liability risk | "This will definitely improve your credit score" |
| **Invented Details** | Hallucination; violates policy sourcing | "We offer 5.5% APY" (if not in policy docs) |
| **Third-Party Bias** | Product liability | "This is better than [Competitor Bank]'s option" |
| **Urgent Promises** | Sets false expectations | "I'll fix this for you immediately" |

---

### Constraints

#### **Regulatory & Compliance:**
- All responses must map to source document (FAQ, policy, regulatory public info)
- No personalized financial/legal/tax advice (risk of SEC/IRS/state law violation)
- No false claims about features, rates, or guarantees (Reg Z compliance)
- All interactions traceable in audit log (for examination, incident response)
- PII must not appear in logs, traces, or responses (GDPR/CCPA compliance)

#### **Safety & Privacy:**
- Transactional requests: 100% escalation rate (no exceptions)
- Advice boundaries: 95%+ recall on regulated domains (acceptable miss rate for flagging human review)
- Hallucination rate: <5% of responses (flag for manual review if higher)
- PII in logs: 0% (automated check + manual audit)
- Escalation SLA: Response within 5 seconds; human contact within 2 hours (for demo target)

#### **Technical & 1-Week Build:**
- Single-page Streamlit app (no complex multi-service architecture)
- SQLite for persistence (no database migration complexity)
- ChromaDB for retrieval (simple embedding search; no complex RAG pipeline)
- Langfuse for observability (pre-built integration; minimal custom code)
- Python backend only (no separate services; faster development)
- Minimal devops: Run locally or on single VM (not Kubernetes, not distributed)

#### **Deployment & Operational:**
- Internal/controlled environment (employees only, not public-facing)
- Email-based escalation collection (no real queue integration this week)
- Manual admin UI for policy doc upload (not automated pipeline)
- Designed for hand-off to productionization team later (clean architecture; documented assumptions)

---

### Assumptions

**About Users:**
- Users have basic banking knowledge (understand checking, savings, credit)
- Users have authenticated into bank portal (or will be via SSO; identity assumed pre-verified by upstream)
- Users will ask natural language questions (not predefined buttons; text input)
- Users expect instant responses (<5 seconds)
- Users will understand when system declines to answer and will accept referral to human

**About Data Quality:**
- Source documents (policies, FAQs) are **current and accurate** (no stale data)
- Policy documents are **clear and unambiguous** (no conflicting guidance)
- Documents are **curated by product/compliance team before upload** (no low-quality sources)
- Documents are **complete enough** to answer 80%+ of routine customer questions

**About Deployment Environment:**
- Deployed on **internal network or VPN-secured** (not public internet; reduces security burden)
- Users are **employees or authorized stakeholders** (not random internet traffic)
- Single-user or low-concurrency access (Streamlit limitation acceptable)
- Manual configuration and administration (no automated deployment pipeline; acceptable for internal)
- Accessible only within standard business context (not always-on critical service)

**About Compliance & Legal:**
- **Upstream authentication** handles user identity (system assumes user is authenticated)
- **Bank compliance team** owns definition of "regulated advice" (system enforces their boundaries)
- **Legal team** has reviewed prompt design and guardrails (system operates within their guidance)
- **Risk team** accepts residual hallucination risk <5% for internal deployment (monitored via logs)

---

## 4. Supported Use Cases

### Supported Use Cases (System Responds Directly)

| Use Case | User Intent | Example Question | Expected Response | Safety Mechanism |
|----------|-------------|------------------|-------------------|------------------|
| **Product Feature Explanation** | Understand features and benefits of a banking product | "What features does your premium checking account have?" | Lists features with source citation; no assumption about suitability | Sourced from product doc; no personalization |
| **Policy & Fee Clarification** | Understand costs, charges, or policy terms | "What is your overdraft fee and how do I avoid it?" | Cites published fee schedule; explains policy; actionable; no assumption | Regz-compliant; cites policy doc source |
| **Procedural Guidance** | Learn step-by-step process or next steps | "How do I apply for a credit card and what documents do I need?" | Walks through application process; lists required docs; timeline; where to apply | No decision-making; purely procedural |
| **Eligibility Thresholds** | Understand general requirements (not personalized qualification) | "What are the requirements to open a business account?" | General thresholds (minimum deposits, documentation types); note that specific qualification requires conversation with specialist | General info only; not a qualification decision |
| **Educational & Regulatory Context** | Understand public financial concepts / regulatory info | "What is FDIC insurance and how much am I protected?" | Explains FDIC coverage; limits; exceptions; cites regulatory source | Public regulatory fact; no advice |

---

### Unsupported Use Cases (System Declines & Escalates)

| Use Case | User Intent | Example Question | Expected System Response | Routing |
|----------|-------------|------------------|---------------------------|---------|
| **Transaction Request** | Request to execute money movement | "Can you transfer $500 to my savings account?" | "I can't process transactions directly. Please log in to your account or I can connect you with an agent." | Escalate (flag: transactional) |
| **Account-Specific Query** | Request for account status or personalized info | "What is my current balance?" or "What's my current interest rate?" | "To check your account details, please log in or contact support." | Escalate or redirect (no account access) |
| **Regulated Advice (Tax)** | Request for tax strategy or guidance | "How should I structure my deposits to minimize taxes?" | "I can't provide tax advice. A CPA or tax advisor can help with strategy. I can explain our product features if that's helpful." | Escalate or deny (flag: tax_advice) |
| **Regulated Advice (Investment)** | Request for investment recommendation | "Should I invest in your money market fund or keep my savings in checking?" | "I can't advise on investments. A financial advisor can discuss options. I'm happy to explain each product's features." | Escalate or deny (flag: investment_advice) |
| **Regulated Advice (Legal)** | Request for legal interpretation or action | "Can I dispute this charge in court?" | "Legal questions need professional guidance. Speak with an attorney or contact our customer service for account investigation." | Escalate or deny (flag: legal_advice) |
| **Complaint or Dispute** | Request for investigation or resolution of account issue | "I was charged twice for this purchase and I'm angry! Fix this now!" | "I understand this is frustrating. This needs investigation. Let me connect you with a specialist right now." | Escalate (flag: emotional_urgent) |
| **Credit Scoring Question** | Request for information about credit impact or scoring | "Why was I denied for this credit card?" | "Credit decisions are based on multiple factors. Your denial letter explains the reason. A specialist can review your situation in detail." | Escalate (flag: credit_decision) |
| **Third-Party Account Access** | Request to check another person's account | "Can you check my spouse's account balance?" | "For security, each account holder must access their own account. Please have your spouse log in." | Escalate or deny (flag: third_party_access) |

---

## 5. Example User Questions (Real Banking Language)

### Example 1: Straightforward Product Inquiry

**User:** "What's the minimum deposit to open your savings account?"

**System Response:**
```
Our regular savings account requires no minimum deposit to open.
Once opened, we charge no monthly fees, and your deposits earn interest 
at our current rate of 0.45% APY (as of April 2026).

Is there anything else about our savings accounts you'd like to know?
```

**Why This Works:**
- ✓ Factual; sourced from product doc
- ✓ Concise; answers the question directly
- ✓ No assumption about user's intent
- ✓ Offers follow-up opportunity

---

### Example 2: Policy Clarification with Actionable Guidance

**User:** "What happens if I don't keep the minimum balance in premium checking?"

**System Response:**
```
Our premium checking account requires a $5,000 minimum daily balance to waive the $15/month fee.

If your balance drops below $5,000 on any day:
• You'll be charged the $15 monthly maintenance fee
• You keep all other premium benefits (no interest earned on this account)

Ways to avoid the fee:
1. Maintain the $5,000 minimum, OR
2. Set up a direct deposit of $1,000+ per month, OR
3. Downgrade to our standard checking (no minimum, no fee)

Would you like more details on any of these options?
```

**Why This Works:**
- ✓ Cites specific policy terms (from policy doc)
- ✓ Explains consequence clearly
- ✓ Provides alternatives (not advice; just options)
- ✓ No assumption about user's situation

---

### Example 3: Procedural Guidance (Not Advice)

**User:** "How long does it take to open a new account?"

**System Response:**
```
Here's the typical timeline for opening any checking or savings account:

1. Application: 5–10 minutes online
2. Identity verification: Instant (automated check)
3. Account activation: Immediate after verification
4. Debit card delivery: 5–7 business days

If you need a card faster, you can visit a branch for same-day issuance.

Ready to apply? I can direct you to the application, or you can visit a branch.
```

**Why This Works:**
- ✓ Procedural; not prescriptive
- ✓ Clear steps; realistic timeline
- ✓ Offers immediate next step
- ✓ No assumption about user's readiness

---

### Example 4: Escalation (Emotional/Urgent)

**User:** "This is URGENT! Your bank charged me TWICE for the same purchase and I need this fixed RIGHT NOW!"

**System Response:**
```
I understand this is urgent and frustrating. Duplicate charges are serious.

This needs immediate investigation, and I'm not equipped to do that.
Let me connect you with a specialist right now who can:
• Access your account details
• Investigate the charges
• Work toward a resolution

Connecting you... [Escalation triggered]

A specialist should contact you within 1 hour. You can also call [support number].
```

**Why This Works:**
- ✓ Acknowledges emotion; validates concern
- ✓ Recognizes urgency; escalates immediately
- ✓ Clear what specialist will do
- ✓ Provides backup contact method
- ✗ NOT: "You'll need to call support" (dismissive)

---

### Example 5: Boundary Enforcement (Regulated Advice)

**User:** "Should I move my savings to your money market account to earn more interest? I'm worried about my retirement."

**System Response:**
```
I understand interest rates matter for your retirement planning.
This is an important decision that depends on your specific situation.

What I can do:
• Explain our money market account features
• Compare interest rates and terms
• Describe how money market funds work

What I can't do:
• Advise on where *your* money should go
• Discuss your overall retirement strategy

For personalized guidance, I recommend speaking with a financial advisor.
I can also connect you with one of our relationship managers who can discuss 
your savings options in detail.

Would you like me to do either of those?
```

**Why This Works:**
- ✓ Acknowledges the concern
- ✓ Clearly separates what system can/cannot do
- ✓ Offers alternative paths
- ✓ Maintains helpful tone while enforcing boundary

---

## 6. System Architecture (Proper Application Design)

### 6.1 High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    STREAMLIT WEB INTERFACE                        │
│  • Chat input box  • Message history  • Escalation button         │
│  • Disclaimer display  • Conversation context                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │ User Input (text)
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│              INPUT VALIDATION & SAFETY LAYER                      │
│  • PII pattern detection (SSN, account, email)                    │
│  • Input length check (prevent token bombarding)                  │
│  • Mask PII if present; ask user for permission                   │
│  • Reject if severe risk (transactional keywords, explicit PII)   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ Sanitized input
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│          INTENT CLASSIFICATION & ROUTING LAYER                    │
│  • Pattern matching: Transactional keywords (transfer, approve)   │
│  • Pattern matching: Regulated advice keywords (should, invest)   │
│  • Heuristic scoring: Intent type + confidence                    │
│  • Decision: Retrieve → LLM → Respond | Escalate | Deny          │
└──────┬──────────────────────────┬────────────────────┬────────────
        │ Informational (80%)      │ Transactional (15%) │ Regulated Advice (5%)
        ↓                          ↓                    ↓
    ┌───────────────────┐  ┌─────────────────┐   ┌──────────────────┐
    │ RETRIEVAL LAYER   │  │ ESCALATION      │   │ DENIAL RESPONSE  │
    │ (ChromaDB)        │  │ (to human)      │   │ (with referral)  │
    │ • Query embed     │  │                 │   │                  │
    │ • Semantic search │  │ Collect contact │   │ Offer escalation │
    │ • Top-K docs     │  │ Store in SQLite │   │ → Escalation?    │
    │ • Confidence     │  │ Log in Langfuse │   │ Log in Langfuse  │
    │   score          │  │                 │   │                  │
    └────────┬──────────┘  └────────┬────────┘   └────────┬─────────┘
             │                      │                     │
             └──────────────────────┴─────────────────────┴─────────┐
                                    │                               │
                                    ↓                               │
                    ┌──────────────────────────────────────┐        │
                    │ LLM RESPONSE GENERATION              │        │
                    │ (if retrieval successful)            │        │
                    │ • System prompt + policy             │        │
                    │ • Retrieved context                  │        │
                    │ • User query                         │        │
                    │ • Conversation history               │        │
                    │ • Safety guardrails                  │        │
                    └──────────────┬───────────────────────┘        │
                                   │                                │
                                   ↓                                │
                    ┌──────────────────────────────────────┐        │
                    │ POST-GENERATION SAFETY VALIDATION    │        │
                    │ • PII egress check                   │        │
                    │ • Advice language detection          │        │
                    │ • Confidence scoring                 │        │
                    │ • Fact consistency with retrieval    │        │
                    └──────────────┬───────────────────────┘        │
                                   │                                │
                   ┌───────────────┼────────────────────────┐       │
                   │               ↓                        │       │
                   │        [Response Safe?]               │       │
                   │        Yes ↓        No ↓              │       │
                   │                    Rewrite or        │       │
                   │                    Escalate          │       │
                   │                                      │       │
                   └──────────────────────────────────────┴───────┘
                                    │
                                    ↓
                    ┌──────────────────────────────────────┐
                    │ LOGGING & OBSERVABILITY (Langfuse)   │
                    │ • Intention detected                 │
                    │ • Retrieval results (if any)         │
                    │ • Response category                  │
                    │ • Safety decision (allow/deny/esc)   │
                    │ NO: PII, full queries, full response │
                    │ YES: Metadata, intent, trace         │
                    └──────────────┬───────────────────────┘
                                   │
                                   ↓
                    ┌──────────────────────────────────────┐
                    │ APPLICATION STATE & EVENTS (SQLite)  │
                    │ • Conversation state                 │
                    │ • Escalation requests (email, phone) │
                    │ • Configuration (policies, docs)     │
                    │ • User session metadata              │
                    │ NO: PII, full query text             │
                    │ YES: Anonymized session IDs, flags   │
                    └──────────────┬───────────────────────┘
                                   │
                                   ↓
                    ┌──────────────────────────────────────┐
                    │ DISPLAY TO USER (Streamlit)          │
                    │ • Response OR escalation notice      │
                    │ • Disclaimer (informational only)    │
                    │ • Conversation context maintained    │
                    └──────────────────────────────────────┘
```

---

### 6.2 Core Components & Responsibilities

| Component | Responsibility | Technology | Data Flow |
|-----------|-----------------|-----------|-----------|
| **Streamlit UI** | Accept user queries; display responses; conversation history | Streamlit | JSON state → Display |
| **Input Validation Layer** | Detect PII; validate input length; reject severe threats | Python regex + heuristics | Raw input → Sanitized input |
| **Intent Classifier** | Detect transactional/regulated/ambiguous intent; score confidence | Python (pattern matching + simple heuristics) | Sanitized input → Intent + confidence |
| **Retrieval Layer** | Vector search across policy docs; return top-K with scores | ChromaDB (embedding + search) | Query embedding → Top-K docs |
| **LLM Integration** | Generate response using provided context + guardrails | OpenAI / Claude API | Prompt + context → Response |
| **Post-Validation** | Verify response is safe; scan for PII, advice, hallucination | Python (regex + heuristics) | Raw response → Validated response |
| **Escalation Handler** | Collect contact info; log escalation reason; notify | Python + SQLite | Escalation event → Stored request + Langfuse log |
| **Observability** | Trace every interaction; log intent, retrieval, decision | Langfuse SDK | Events → Langfuse (PII-safe) |
| **Application State** | Store conversation, configuration, escalation requests | SQLite | State → SQLite tables |

---

### 6.3 User Interaction Flows

#### Flow A: Normal Informational Query (80%)

```
User enters query: "What's the fee for overdraft protection?"
    ↓
[Input Validation] No PII detected; input valid ✓
    ↓
[Intent Classifier] Intent = "informational" (conf 95%) ✓
    ↓
[Retrieval] Query: "overdraft fee"
    Response: Top-3 docs match (fees.md, overdraft_policy.md, faq.md)
    Confidence: 85% ✓
    ↓
[LLM Generation]
    System Prompt: "You are a banking product advisor. Answer using provided docs. Cite source."
    User Query: "What's the fee for overdraft protection?"
    Context: Retrieved docs + conversation history
    Output: "Our overdraft protection fee is $35 per incident, as shown in our fee schedule."
    ↓
[Post-Validation]
    • PII check: None detected ✓
    • Advice check: Response is factual, cites source ✓
    • Hallucination check: "Fee $35" maps to retrieved doc ✓
    • Confidence: 90% (high confidence → deliver) ✓
    ↓
[Logging to Langfuse]
    Event: {
      "timestamp": "2026-04-19T10:23:45Z",
      "intent": "informational_product_query",
      "retrieval_confidence": 0.85,
      "response_category": "policy_fact",
      "response_confidence": 0.90,
      "action_taken": "respond",
      "safety_checks_passed": true
    }
    ↓
[Display to User]
    "Our overdraft protection fee is $35 per incident, as shown in our fee schedule.
     Would you like to know how to avoid overdraft charges?"
```

**Result:** User satisfied; query answered; conversation continues

---

#### Flow B: Transactional Request (15%)

```
User enters query: "Can you transfer $500 from my checking to savings?"
    ↓
[Input Validation]
    PII: Specific amount ($500) mentioned (not truly PII, but context flag)
    Input: Valid ✓
    ↓
[Intent Classifier]
    Keyword match: "transfer" + amount + account reference
    Intent = "transactional" (conf 98%) ✓
    Decision: ESCALATE (not RETRIEVE)
    ↓
[Escalation Handler]
    Response generated: "I can't process transactions directly. For security, 
                        let me connect you with an agent who can verify your 
                        identity and complete this for you."
    Collect contact (optional): "Would you like us to call you back? [email/phone]"
    ↓
[Logging to Langfuse]
    Event: {
      "timestamp": "2026-04-19T10:24:12Z",
      "intent": "transactional_confirmed",
      "intent_confidence": 0.98,
      "action_taken": "escalate",
      "escalation_reason": "transaction_request",
      "customer_contact": "masked_email",
      "safety_decision": "escalation_required"
    }
    ↓
[Store in SQLite]
    INSERT INTO escalations (
      session_id, intent, reason, customer_contact, created_at, status
    ) VALUES (session_123, 'transaction', 'transfer_request', 'contact_xyz', ..., 'open')
    ↓
[Display to User]
    "I can't process transactions directly. For security, let me connect you 
     with an agent who can verify your identity and complete this for you.
     
     [Button: Call me back] [Button: Email me a link]"
```

**Result:** Transactional request prevented; user escalated cleanly; audit trail maintained

---

#### Flow C: Regulated Advice Request (5%)

```
User enters query: "Should I invest in your CD or keep my money in savings?"
    ↓
[Input Validation] No PII; input valid ✓
    ↓
[Intent Classifier]
    Keywords: "should" + "invest" + product names
    Intent = "regulated_advice" (conf 88%) ✓
    Decision: DENY (not RETRIEVE)
    ↓
[Denial Response]
    Response: "I can't advise on investments. Here's what I can help with:
               • Explain our CD features and rates
               • Explain our savings account terms
               • Compare features side-by-side
    
               For personalized guidance on what's right for you, speak with a 
               financial advisor or our relationship manager.
               
               Would you like me to explain either product?"
    ↓
[Logging to Langfuse]
    Event: {
      "timestamp": "2026-04-19T10:25:33Z",
      "intent": "regulated_advice_detected",
      "intent_confidence": 0.88,
      "regulated_domain": "investment_advice",
      "action_taken": "deny_with_referral",
      "escalation_offered": true,
      "safety_decision": "boundary_enforced"
    }
    ↓
[No escalation stored in SQLite; conversation continues]
    ↓
[Display to User]
    [Boundary message + offer to explain products]
```

**Result:** Advice boundary enforced; user redirected to appropriate resource; no escalation needed

---

## 7. Data Management & Persistence

### 7.1 SQLite Schema (Minimal for 1-Week)

```
Assuming tables (no code; conceptual design):

TABLE: conversations
  • session_id (PK, UUID)
  • user_id (anonymized, no PII)
  • created_at (timestamp)
  • updated_at (timestamp)
  • conversation_state (JSON: message history, context)
  • status (active | archived | escalated)

TABLE: interactions
  • interaction_id (PK, auto-increment)
  • session_id (FK → conversations)
  • timestamp (when interaction occurred)
  • user_query_hash (hash of query, NOT stored plaintext)
  • intent_detected (informational | transactional | regulated)
  • intent_confidence (0.0-1.0)
  • action_taken (responded | escalated | denied)
  • response_provided (if not escalated; summarized, not full text)
  • langfuse_trace_id (link to Langfuse for full audit)

TABLE: escalations
  • escalation_id (PK, auto-increment)
  • session_id (FK → conversations)
  • timestamp (when escalated)
  • reason_code (transaction_request | urgent | ambiguous | advice | other)
  • customer_contact (email OR phone; encrypted in production)
  • notes (summary of user's issue; PII-stripped)
  • status (open | contacted | resolved | abandoned)
  • assigned_agent (agent_id; for future hand-off)

TABLE: policies_documents
  • doc_id (PK, auto-increment)
  • filename (source file name)
  • category (products | fees | procedures | education | regulatory)
  • uploaded_at (when added)
  • version (for tracking changes)
  • is_active (boolean; can deprecate docs without deleting)
  • chromadb_collection_id (reference to ChromaDB)
  • source_url (internal wiki or policy repo link)
  • curator_notes (why this doc is authoritative)

TABLE: configuration
  • key (PK, string)
  • value (JSON or string)
  • Examples:
    - system_prompt_version (which prompt is active)
    - escalation_sla_minutes (expected response time)
    - hallucination_threshold (confidence % to escalate instead of respond)
    - max_conversation_turns (before escalation)
```

**Privacy Safeguards in SQLite:**
- ✓ No full user queries stored (only hashes if needed for debugging)
- ✓ No PII in any field (explicitly validated before INSERT)
- ✓ escalations.customer_contact encrypted at rest
- ✓ Conversation state stored as JSON blob (no individual PII fields)
- ✓ All transactions linked to Langfuse for full audit trail (Langfuse handles detailed tracing)

---

### 7.2 ChromaDB Usage (Policy Retrieval)

**Collections:**
```
Collection: "policies"
  Documents: Policy docs, FAQs, product sheets, regulatory summaries
  Embedding: OpenAI ada-002 (or similar)
  Metadata:
    - source_file: "fee_schedule_2026.pdf"
    - category: "fees"
    - date_added: "2026-04-15"
    - is_active: true/false (deprecated docs kept but not retrieved)

Example doc: 
  ID: "doc_001"
  Content: "Overdraft fees: $35 per incident. Ways to avoid: 1) Keep balance above minimum, 
            2) Set up overdraft protection line, 3) Link to savings account..."
  Embedding: [0.123, -0.456, 0.789, ...] (1536 dims)
  Metadata: {category: "fees", source: "fee_schedule_2026.pdf"}
```

**Retrieval Flow:**
```
User query: "What's the overdraft fee?"
    ↓
Embed query: OpenAI ada-002 → [0.125, -0.460, 0.788, ...]
    ↓
ChromaDB semantic search:
    query(embedding, top_k=3, where={"is_active": true})
    ↓
Results:
  1. doc_001 (fee_schedule): similarity=0.94
  2. doc_003 (faq): similarity=0.87
  3. doc_015 (policy): similarity=0.81
    ↓
Retrieval confidence: 0.94 (use top result; if <0.60, escalate instead)
    ↓
Pass to LLM: Retrieved text + query → Generate response
```

**Data Lifecycle:**
- Upload: New policy docs added by admin through Streamlit interface
- Index: Automatically embedded and added to ChromaDB collection
- Monitor: Track retrieval success rate; flag low-performing docs
- Deprecate: Mark is_active=false if policy changes; don't delete (audit trail)
- Archive: After 12 months, move to archive collection (not retrieved)

---

### 7.3 Langfuse Integration (Observability)

**What Gets Logged (PII-Safe):**
```
For every LLM call, log to Langfuse:

trace_id: UUID
  ├─ trace_name: "banking_ai_query"
  ├─ timestamp: ISO 8601
  ├─ session_id: anonymized UUID
  │
  ├─ span: "input_validation"
  │  ├─ had_pii: true/false (NOT which PII)
  │  ├─ input_length: integer
  │  └─ validation_passed: true/false
  │
  ├─ span: "intent_classification"
  │  ├─ intent_detected: "informational" | "transactional" | "regulated"
  │  ├─ confidence: 0.0-1.0
  │  └─ routing_decision: "retrieve" | "escalate" | "deny"
  │
  ├─ span: "retrieval" (if applicable)
  │  ├─ query_embedding: dimensions (not values)
  │  ├─ top_k_results: integer
  │  ├─ retrieval_scores: [0.94, 0.87, 0.81]
  │  ├─ docs_retrieved: integer
  │  └─ best_match_confidence: 0.94
  │
  ├─ span: "llm_generation" (if applicable)
  │  ├─ model_used: "gpt-4"
  │  ├─ prompt_tokens: integer
  │  ├─ completion_tokens: integer
  │  ├─ total_tokens: integer
  │  ├─ temperature: float
  │  └─ finish_reason: "stop" | "length" | "error"
  │
  ├─ span: "post_generation_validation"
  │  ├─ pii_detected_in_response: false
  │  ├─ advice_language_detected: false
  │  ├─ hallucination_confidence: 0.05
  │  └─ validation_passed: true
  │
  ├─ span: "response_decision"
  │  ├─ action: "respond" | "escalate" | "deny"
  │  ├─ reason: code (e.g., "informational_high_confidence")
  │  └─ customer_contact_collected: false
  │
  └─ metadata:
     ├─ user_agent: browser type
     ├─ deployment_env: "internal"
     ├─ app_version: "1.0.0"
     └─ tags: ["internal_demo", "banking"]

NOT logged:
- Full user query text
- Full LLM response text
- Customer PII (name, account, email)
- Retrieved document contents
```

**Langfuse Benefits for Production Readiness:**
- ✓ Full audit trail: Every decision traceable to spans
- ✓ Token usage tracking: Budget planning for production
- ✓ Performance monitoring: Latency, failure rates, quality
- ✓ Cost analysis: LLM per-interaction costs
- ✓ Debugging: Reproduce any interaction via trace ID
- ✓ Export-ready: Can generate compliance reports from Langfuse

---

### 7.4 Data Lifecycle (Governance)

| Data Type | Storage | Lifetime | Access | Compliance |
|-----------|---------|----------|--------|-----------|
| **Conversation State** | SQLite + Langfuse | 7 days in production (session-based for MVP) | Internal app only | GDPR: Right to deletion met via session deletion |
| **Escalation Requests** | SQLite (encrypted) | 90 days (for investigation + follow-up) | Support team + admins | GDPR: Deletion possible on request |
| **Policy Documents** | ChromaDB | Until deprecated (3 months typical) | System reads; no human access | GDPR: No PII; can keep indefinitely |
| **Trace Logs** | Langfuse | 30 days (Langfuse retention) | Admins for debugging; compliance for audit | GDPR: Aggregated; PII-stripped |
| **Configuration** | SQLite + env vars | Until changed | Admins only | No PII |

---

## 8. Safety, Guardrails & Observability

### 8.1 Transactional Intent Detection

**What Triggers Detection:**

| Signal Type | Examples | Sensitivity |
|-------------|----------|-------------|
| **Lexical (Keywords)** | transfer, send, wire, pay, approve, execute, reverse, process, authorize, link, move, charge, debit, credit | High (99%+ precision) |
| **Contextual** | "my account" OR "my card" OR amount ($500) | Medium (88%+ precision) |
| **Sequential** | "Can you..." + transactional verb + account reference | Medium-High (92%+ precision) |
| **Urgency** | "right now", "ASAP", "urgent" + action verb | Medium (80%+ precision) |

**Implementation (Pseudocode):**
```
if any(keyword in user_input for keyword in TRANSACTIONAL_KEYWORDS):
    if any(account_ref in user_input for account_ref in ACCOUNT_REFERENCES):
        confidence = 0.98
        intent = "transactional"
    elif amount_detected(user_input):
        confidence = 0.95
        intent = "transactional"
    else:
        confidence = 0.85
        intent = "possible_transactional"

if intent == "transactional" OR confidence > 0.90:
    routing = "ESCALATE"
else:
    routing = "REVIEW_LLM_FOR_CONTEXT"
```

**Acceptance Criteria:**
- ✓ 99%+ recall on true transactional requests (catch almost all)
- ✓ <15% false positive rate on informational queries (acceptable; user can clarify)
- ✓ Manual audit of first 50 queries to validate accuracy

---

### 8.2 Regulated Advice Detection

**Regulated Domains:**

| Domain | Detection Keywords | Routing Decision |
|--------|-------------------|------------------|
| **Tax Advice** | tax, deduction, W-4, tax return, income, strategy, minimize, IRS | Deny + refer to CPA |
| **Investment Advice** | invest, portfolio, allocation, buy, sell, fund, security, market, should I | Deny + refer to advisor |
| **Legal Advice** | contract, lawsuit, legal, dispute, attorney, rights, liability, precedent | Deny + refer to attorney |
| **Credit Scoring** | credit score, why denied, creditworthiness, credit report, FICO | Deny + refer to specialist |
| **Insurance Underwriting** | coverage, risk assessment, claim, underwriting, eligibility (specific) | Deny + refer to agent |

**Implementation:**
```
if any(keyword in user_input for keyword in TAX_KEYWORDS):
    domain = "tax"
    action = "DENY"
    referral = "CPA or tax advisor"
elif any(keyword in user_input for keyword in INVESTMENT_KEYWORDS):
    domain = "investment"
    action = "DENY"
    referral = "financial advisor"
# ... etc

# Confidence: If keyword match found:
if domain in REGULATED_DOMAINS:
    confidence = 0.90 (high, but allow manual review if LLM context contradicts)
    action = "DENY_WITH_REFERRAL"
```

**Acceptance Criteria:**
- ✓ 95%+ recall on regulated advice attempts
- ✓ <5% false positives (rarely deny when shouldn't)
- ✓ Clear referral always provided

---

### 8.3 Hallucination Risk Minimization

**Root Causes in Banking Context:**
- LLM generates plausible-sounding but incorrect fees/rates
- LLM infers customer eligibility from partial context
- LLM over-generalizes from limited docs
- LLM answers out-of-domain questions confidently

**Mitigation Approach:**

| Mitigation | Implementation | Effectiveness |
|-----------|-----------------|-----------------|
| **Retrieval First** | Always try ChromaDB first; if retrieval confidence <60%, escalate instead of LLM | 90%+ (prevents invented facts) |
| **Fact Grounding** | LLM response must cite retrieved document explicitly ("According to [source]...") | 85%+ (makes hallucinations detectable) |
| **Confidence Threshold** | If LLM confidence <70%, escalate instead of respond | 80%+ (reduces unsure responses) |
| **System Prompt** | Explicit instruction: "Do NOT infer. Do NOT guess. If unsure, say so." | 75%+ (still may hallucinate, but less confident) |
| **Post-Validation Scan** | Detect unsourced numeric claims ("APY 5.5%" if not in retrieval) | 70%+ (catches some hallucinations) |
| **Human Review** | Manual audit of biweekly sample; flag hallucinations for tuning | 95%+ (catches what automation misses) |

**Target Hallucination Rate:** <5% of responses (acceptable for internal; must improve before external)

**Acceptance Criteria:**
- ✓ Spot-check 30 responses; <2 contain unsourced claims (5%)
- ✓ Manual audit by compliance officer; zero fabricated fees/rates
- ✓ LLM system prompt includes anti-hallucination instructions

---

### 8.4 Ambiguity Identification & Escalation

**Ambiguous Signals:**

| Signal | Example | Response |
|--------|---------|----------|
| **Vague Phrasing** | "How do I...?" (missing object) | Ask clarifying question; escalate if no response |
| **Multiple Intent** | "I want to open an account but I'm worried about..." | Confirm: Are you informational or ready to apply? |
| **Emotional + Vague** | "I'm upset about something" (no details) | Escalate to agent; acknowledge emotion |
| **Account Reference + Uncertainty** | "My account might be compromised?" | Escalate immediately; recommend security verification |
| **Third-Party + Account Access** | "My spouse might have...?" (no clarity on permissions) | Escalate; confirm authorization before any access |

**Implementation:**
```
ambiguity_level = calculate_ambiguity(user_input)
  # 0-30: Clear intent
  # 30-70: Somewhat ambiguous
  # 70-100: Very ambiguous

if ambiguity_level > 70:
    action = "ESCALATE"
elif ambiguity_level > 50:
    action = "ASK_CLARIFYING_QUESTION"
    if user_responds_ambiguously_again:
        action = "ESCALATE"
else:
    action = "PROCESS_NORMALLY"
```

**Acceptance Criteria:**
- ✓ Ambiguous queries routed appropriately
- ✓ Clarifying questions understood by users
- ✓ No forced escalation for genuinely clear queries

---

### 8.5 What Gets Logged in Langfuse (PII-Free)

**Required Logging:**

```
Every interaction:
  ✓ Intent detected (category + confidence)
  ✓ Retrieval results (docs matched, scores)
  ✓ LLM call (tokens, temperature, model)
  ✓ Response safety validation (passed checks)
  ✓ Action taken (respond/escalate/deny)
  ✓ Reason code (why action taken)
  ✓ Timestamp + session ID (anonymized)

Never logged:
  ✗ Full user query text
  ✗ Full LLM response
  ✗ Retrieved document contents
  ✗ Customer PII (name, SSN, account, email in personal context)
  ✗ Authorization details or secrets
```

**Audit Trail Completeness:**
- ✓ Every interaction traceable via trace ID
- ✓ All safety decisions documented
- ✓ Escalations linked to reason code
- ✓ Hallucinations detectable in logs (flagged low confidence + high-risk response)

---

## 9. Success Criteria (Definition of Done)

### 9.1 User Experience Criteria

| Criterion | Target | Evidence |
|-----------|--------|----------|
| **Response Clarity** | User understands each response without confusion | 5 demo queries tested; users report clarity |
| **Correctness of Refusals** | AI refuses transactions, advice, account access appropriately | Demo 10+ refusal cases; all correctly handled |
| **Correctness of Escalations** | Ambiguous/urgent cases escalated to human | Demo 5+ escalation scenarios; all trigger escalation |
| **Conversation Flow** | User can ask follow-up questions; context maintained | Demo 3+ multi-turn conversations; context preserved |
| **Usability** | Anyone can use chat interface without instruction | New user can submit query in <30 seconds |
| **Disclaimer Visibility** | Every response includes "informational only" framing | Disclaimer visible in all response templates |

---

### 9.2 Safety & Compliance Criteria

| Criterion | Target | Evidence |
|-----------|--------|----------|
| **No Transactional Execution** | 100% of transactional queries escalated | Test 20+ transactional queries; all escalated |
| **No Unauthorized Advice** | 100% of regulated queries denied or escalated | Test 20+ advice queries; all denied/escalated |
| **No PII Storage** | Zero PII persisted in any database or logs | Audit SQLite + Langfuse for PII; all clear |
| **Hallucination Rate** | <5% of responses contain fabricated facts | Manual review of 30 responses; <2 hallucinations |
| **Policy Sourcing** | 100% of policy claims map to retrieved documents | Verify each answer against source doc |
| **Escalation Quality** | Escalations include clear reason + context | Review 10 escalations; all have reason + summary |

---

### 9.3 System Stability & Performance

| Criterion | Target | Evidence |
|-----------|--------|----------|
| **Stability** | System handles 50+ continuous queries without crash | Load test: 50 queries, zero crashes |
| **Response Latency** | 95% of queries answered in <5 seconds | Measure: Query to response time logged |
| **Error Handling** | System gracefully handles edge cases (long input, special chars, malformed input) | Test: Long input, emoji, malformed; system stable |
| **LLM Integration** | API calls successful; responses always generated | Verify: Every query generates a response (no timeouts) |
| **Database Integrity** | SQLite tables created correctly; queries execute without error | Verify: All CRUD operations working |
| **Retrieval Functionality** | ChromaDB queries execute; top-K docs returned with scores | Verify: 20+ retrieval queries; all scores populated |

---

### 9.4 Observability & Auditability

| Criterion | Target | Evidence |
|-----------|--------|----------|
| **Langfuse Integration** | All interactions traced; full audit trail | Sample 10 interactions; all traces in Langfuse |
| **Log Completeness** | Intent, action, reason code logged for every query | Verify: Every log entry has required fields |
| **PII-Free Logging** | Zero PII in any log or trace | Automated scan + manual audit; zero PII found |
| **Traceability** | Any interaction reproducible via trace ID | Pick 5 trace IDs; retrieve full context |
| **Compliance Report Ready** | Can generate summary report (queries, answers, escalations, safety decisions) | Generate sample report; shows key metrics |

---

### 9.5 Documentation & Handoff

| Criterion | Target | Evidence |
|-----------|--------|----------|
| **Architecture Doc** | Complete system design; assumptions clear | Architecture_Design.md signed off |
| **Setup Instructions** | Team can deploy and run without assistance | README.md: Clear steps; tested by new engineer |
| **Safety Guardrails Doc** | Documented all safety rules and thresholds | Guardrails_Config.md explains all heuristics |
| **Known Limitations** | Documented what system cannot do; why | Limitations.md lists 15+ out-of-scope items |
| **Production Roadmap** | Clear path from MVP to production | Roadmap.md lists upgrades needed for scale |

---

## 10. Known Failure Cases & Edge Scenarios

### 10.1 Failure Case 1: Ambiguous Transactional Intent

**Scenario:**
```
User: "How do I stop the automatic payment for my subscription?"
Classifier Dilemma: Sounds procedural ("how to") but user may want us to execute it
```

**Why It Fails:**
- "How to" suggests informational (procedural guidance)
- But context ("stop the payment") implies transactional action
- System might respond with steps, user then says "Can you do it?"

**Expected Safe Behavior:**
```
AI: "You can stop an automatic payment through your online account.
    Here's how:
    1. Log in to your account
    2. Go to 'Payments' or 'Subscriptions'
    3. Find the payment
    4. Click 'Stop Payment' or 'Cancel'
    
    If you need us to process this for you on your behalf, 
    I can connect you with an agent who can verify your identity and make the change."

Result: Clear separation between self-service (procedural) and agent-assisted (transactional)
```

**Mitigation:**
- Detect procedural verbs ("how", "steps") + transactional context
- Always clarify: "Would you like steps to do this yourself, or shall I connect you with an agent?"

---

### 10.2 Failure Case 2: Fabricated Fee Structure

**Scenario:**
```
User: "What are all the fees for business checking?"
ChromaDB Retrieval: Finds 2 relevant docs (somewhat dated)
LLM Generation: Extrapolates beyond retrieved docs
LLM Output: "Fees include: monthly service ($25), wire fee ($35), check fee ($1), ACH fee ($0.50)..."
Truth: Only 3 of these are accurate; ACH is free in 2026
```

**Why It Fails:**
- LLM trained on general banking knowledge (not just retrieval)
- Generates plausible fees that sound like a bank might charge
- If no explicit retrieval match for "ACH fee", LLM hallucinates based on general knowledge

**Expected Safe Behavior:**
```
LLM System Prompt: "You MUST cite the exact source document for every fee or charge.
                    If a fee is not in the retrieved documents, say: 
                    'This fee is not listed in our current policies. 
                     For a complete fee schedule, speak with an agent.'"

Post-Validation: Scan for numeric claims without source ("ACH fee ($0.50)")
                 If found → Flag for human review OR rewrite

Result: Only sourced fees mentioned; unverified fees escalated
```

**Acceptance Criteria:**
- ✓ Manual audit: Zero invented fees in 30-response sample
- ✓ Post-validation catches unsourced numeric claims

---

### 10.3 Failure Case 3: Emotional/Urgent Language Ignored

**Scenario:**
```
User: "This is URGENT! You've charged me TWICE and I need this FIXED NOW! I'm furious!"
System Response (bad): "Our duplicate charge policy is..."
Result: User feels unheard; takes complaint to social media
```

**Why It Fails:**
- System treats as informational query (no intent match)
- Responds with policy explanation
- User wanted immediate human intervention, not education

**Expected Safe Behavior:**
```
Intent Variant: Detect emotional signals
  Keywords: CAPS, exclamation marks, emotional words (furious, upset, angry, urgent)
  + account issue context
  
Action: ESCALATE immediately (skip LLM)
  
Response: "I understand this is urgent and frustrating. 
          A specialist needs to investigate this right away.
          I'm connecting you now. You should hear from someone within 1 hour.
          [Escalation triggered]"

Result: User feels heard; escalated immediately; prevents escalation to social media
```

**Acceptance Criteria:**
- ✓ Test emotional queries (10+ variations); all trigger escalation
- ✓ Agents report: "Escalations appropriate and urgent cases prioritized"

---

### 10.4 Failure Case 4: Conflicting Policy Documents

**Scenario:**
```
ChromaDB contains:
  - Old_Fee_Schedule (2025): "Overdraft fee $25"
  - New_Fee_Schedule (2026): "Overdraft fee $35"
  Both marked is_active=true
  
Retrieval returns both docs (equal similarity)
LLM sees conflicting info → Confused response OR picks wrong one
```

**Why It Fails:**
- Document curation didn't mark old docs as inactive
- Retrieval returns both; LLM doesn't know which is current
- Response may cite outdated policy

**Expected Safe Behavior:**
```
Curation Process: Before upload, mark is_active=false for deprecated docs
  - Old_Fee_Schedule: is_active=false, deprecated_date=2026-01-01
  - New_Fee_Schedule: is_active=true, effective_date=2026-01-01

ChromaDB Retrieval: Add where clause: {"is_active": true}
  Only current docs returned

Result: Only current policy retrieved; no confusion
```

**Acceptance Criteria:**
- ✓ Document upload procedure includes active/deprecation status
- ✓ Retrieval enforces is_active=true filter
- ✓ Compliance audit: Zero outdated policies in retrievals

---

### 10.5 Failure Case 5: Third-Party Account Inquiry

**Scenario:**
```
User: "Can you check if my spouse can open an account with these terms?"
System: Treats as product inquiry; provides information
Problem: System may inadvertently suggest spouse doesn't meet requirements 
         → User feels personally rejected
```

**Why It Fails:**
- No explicit flag for third-party phrasing
- System provides general information; user interprets as specific qualification

**Expected Safe Behavior:**
```
Intent Variant: Detect third-party language
  Keywords: "spouse", "my parent", "my friend", "someone else", "they"
  + account/qualification context
  
Decision: Clarify or escalate:
  "Are you asking:
   A) General eligibility criteria for anyone?
   B) A specific person's eligibility (discuss with them)?
   C) To apply for a co-owner account?
   
   If (B), I recommend your spouse speak with an agent directly."

Result: No assumption about third party; clear escalation if needed
```

---

## 11. Architecture & Risk Review

### 11.1 Key Technical Risks

| Risk | Severity | Mitigation (1-Week) | Production Upgrade |
|------|----------|-------------------|-------------------|
| **LLM Hallucination** | HIGH | Confidence threshold <70% → escalate; post-validation scans | ML-based fact verification; external fact-checking API |
| **PII Leak** | CRITICAL | Regex masking at input; no PII in logs; SQLite no-PII audit | Encrypted vault; GDPR delete workflows; DLP scanning |
| **Retrieval Failure** | MEDIUM | Fallback: If retrieval confidence <60%, escalate instead | RAG pipeline improvements; better doc chunking |
| **Intent Misclassification** | MEDIUM | Heuristic + manual review of first 50 queries | ML classifier; continuous retraining on feedback |
| **Escalation Queue Bottleneck** | MEDIUM | Email/manual escalation (MVP); no real queue | CRM integration; automatic routing; SLA monitoring |
| **Database Corruption** | LOW | SQLite integrity checks; backups every day | Multi-region replication; automated failover |
| **LLM API Outage** | MEDIUM | Graceful failure: "System temporarily unavailable; try later" | Fallback to pre-built responses; batch caching |
| **Session Loss** | LOW | Streamlit session management built-in; acceptable for internal | Redis session store; user account system |

---

### 11.2 Compliance & Regulatory Risks

| Risk | Severity | Mitigation (1-Week) | Production Upgrade |
|------|----------|-------------------|-------------------|
| **Unauthorized Advice** | CRITICAL | Regulated advice deny-list; weekly compliance audit | Legal framework; tested by external counsel |
| **False Policy Info** | CRITICAL | Document sourcing requirement; 30-query manual audit | Automated fact-checking; real-time policy sync |
| **PII Exposure** | HIGH | Regex masking; Langfuse strip; no plaintext storage | GDPR compliance framework; encryption; audit |
| **Regulatory Examination** | MEDIUM | Audit trail via Langfuse; can reproduce any interaction | Compliance dashboard; automated reports |
| **Customer Complaint** | MEDIUM | Escalation logged; can investigate via trace ID | Feedback loop; automatic escalation on complaint keywords |

---

### 11.3 Acceptable MVP Risk Posture

**For Internal Demo / Controlled Environment:**

✓ **Acceptable Risks:**
- Hallucination rate 3–5% (document and improve)
- Classified missing <10% of transactional requests (mitigated by escalation button)
- PII detection 95% accuracy (better to over-mask than under-mask)
- Ambiguous cases escalated (safer than forcing an answer)
- Single-user Streamlit (no concurrency testing; not needed internally)

⚠ **Mitigated Risks:**
- Transactional bypass: Keyword + context heuristics (good enough for internal; penetration test before external)
- Advice violation: Deny-list + manual audit (allows <5% to slip; acceptable; flagged for improvement)
- Data breach: Regex masking + Langfuse strip (good enough for demo; encryption before production)

✗ **Non-Negotiable (Must Work):**
- System refuses 100% of explicit transactional requests
- System refuses 100% of explicit advice requests
- No hallucinated customer data (fabricated balances, eligibility)
- Escalation button always works; customer can always reach human
- PII not logged plaintext in SQLite or Langfuse
- Every interaction auditable via trace ID

---

### 11.4 What Must Change Before Production

| Issue | MVP Approach | Production Requirement |
|-------|---------------|----------------------|
| **Concurrency** | Single-user Streamlit | Multi-user backend (FastAPI + queue) |
| **Authentication** | Assume upstream auth | OAuth2 + MFA; session management |
| **Data Encryption** | Plaintext SQLite | AES-256 at rest; TLS in transit |
| **Audit Trail** | Langfuse + SQLite logs | Immutable ledger; 7-year retention; SOC2 compliance |
| **PII Handling** | Regex masking | Encrypted vault; GDPR delete workflows |
| **Escalation** | Email collection | CRM integration; automatic agent assignment; SLA |
| **Document Management** | Manual admin UI | Automated sync from policy repo; versioning |
| **Load Testing** | None (internal) | 1000+ concurrent users; stress testing |
| **Security Audit** | Internal review | Penetration testing; SOC2 assessment |
| **Regulatory Compliance** | Manual audit | Automated compliance dashboard; real-time monitoring |

---

## 12. Go-Live (Demo) Readiness Checklist

### 12.1 Technical Readiness (Day 5 Friday)

- [ ] **Streamlit app runs:** `streamlit run app.py` successfully deploys chat interface locally
- [ ] **LLM API integrated:** OpenAI / Claude API calls successful; responses generated
- [ ] **Intent classification working:** 30 test queries classified correctly (informational/transactional/regulated)
- [ ] **PII detection working:** 30 test queries; masking applied; verified no PII in SQLite
- [ ] **ChromaDB retrieval working:** 30 policy lookups; top-K docs returned with confidence scores
- [ ] **Escalation logic working:** Transactional/regulated/urgent queries escalate; contact collected
- [ ] **Response validation working:** Post-generation checks pass; no advice detected in 30 responses
- [ ] **Langfuse integration working:** All interactions traced; full audit trail in Langfuse
- [ ] **SQLite tables created:** All schemas initialized; CRUD operations working
- [ ] **No crashes on edge cases:** Long inputs, special characters, rapid-fire queries tested; system stable
- [ ] **Performance baseline met:** 10+ queries average latency <5 seconds achieved
- [ ] **Disclaimer visible:** "Informational only" footer displayed on every response

---

### 12.2 Safety Readiness (Day 5 Friday)

- [ ] **Transactional requests blocked:** Demo 15+ transactional query variations; ≥99% escalated (1 or fewer false negatives)
- [ ] **Regulated advice requests blocked:** Demo 15+ advice queries (invest, tax, legal, credit); ≥95% denied/escalated
- [ ] **Account access refused:** Queries about "my balance," "my rate" properly redirected/escalated
- [ ] **No hallucinated customer data:** Review 30 responses; zero inferred account details, eligibility assumptions, or invented fees
- [ ] **No PII in logs:** Audit SQLite + Langfuse; PII detection scan; zero SSN, account, email persisted
- [ ] **Escalation phrasing polite:** All escalation messages clear, empathetic, not dismissive
- [ ] **Refusal phrasing clear:** All denials explain why; offer alternatives or referrals
- [ ] **Manual compliance review:** Compliance officer reviewed 30 responses; approved for demo
- [ ] **Hallucination audit:** <5% of responses contain unsourced claims; manual spot-check of numeric facts

---

### 12.3 Observability Readiness (Day 5 Friday)

- [ ] **Langfuse dashboard accessible:** Can log in; see traces from test queries
- [ ] **All fields populated:** Intent, confidence, retrieval scores, LLM tokens, validation results logged
- [ ] **Trace linking:** Pick 5 trace IDs from dashboard; retrieve full context
- [ ] **No PII in traces:** Sample 10 traces; verified zero customer names, accounts, emails
- [ ] **SQLite auditable:** Can query escalations table; can reproduce conversations from session IDs
- [ ] **Log export working:** Can export Langfuse logs for compliance reporting

---

### 12.4 Stakeholder Readiness (Day 5 Friday — After Tech Review)

- [ ] **Demo script prepared:** 7-minute walkthrough covering normal query, refusal, escalation, edge case
- [ ] **Known limitations documented:** Limitations.md lists 20+ out-of-scope items with explanation
- [ ] **Risk assessment signed off:** Principal architect + CRO reviewed; acceptable risk for internal demo
- [ ] **Legal review completed:** General counsel confirmed no regulatory violations; disclaimer adequate
- [ ] **Compliance officer sign-off:** Reviewed guardrails, audit trail, PII handling; approved
- [ ] **Disclaimer visible to users:** Streamlit UI clearly states "This is an internal MVP demo. Informational only. Not financial advice."
- [ ] **Escalation contact info ready:** If escalations collected, contact protocol defined (who receives, SLA)
- [ ] **README documentation complete:** Deployment, troubleshooting, architecture overview; a new engineer can run it
- [ ] **Architecture decision log:** Why SQLite, ChromaDB, Langfuse chosen; trade-offs documented
- [ ] **Production roadmap drafted:** Phase 2 improvements (encryption, auth, automation); Phase 3 externalization path

---

### 12.5 Demo Flow (7-minute walkthrough)

**Opening (1 min):**
```
"This is an internal MVP demo of an AI Banking Support Agent.
It's designed to help customers with informational questions about products and policies.
IMPORTANT: This is an INTERNAL DEMO ONLY—not for public release.

The system is built to refuse transactions, advice, and account-specific access.
You'll see three key areas: handling informational queries safely, 
enforcing boundaries appropriately, and escalating complex cases to humans."
```

**Demo Case 1: Informational Query (1.5 min):**
```
"Let me ask a straightforward product question: 'What's the difference between 
premium and standard checking?'"

[System retrieves from ChromaDB, generates response, cites source]
Response: "Premium checking features: [list]. Standard checking: [list]. 
Both have [feature]."

"Notice:
✓ Answer is sourced to policy docs
✓ No assumption about suitability
✓ Clear, conversational phrasing
✓ Langfuse logged every step (intent, retrieval, confidence, decision)
✓ No PII stored anywhere"
```

**Demo Case 2: Refusal (1.5 min):**
```
"Now let me ask for something we explicitly don't do: investment advice.
'Should I invest my savings in a money market fund?'"

[System detects regulated advice intent; denies with referral]
Response: "I can't advise on investments. Here's what I CAN do: explain 
the money market fund features... For personalized advice, speak with a 
financial advisor."

"Notice:
✓ Clear boundary enforcement
✓ Helpful redirection (not just 'no')
✓ Escalation offered ('speak with an advisor')
✓ Confidence scores in Langfuse show why decision was made"
```

**Demo Case 3: Escalation (1.5 min):**
```
"Let me ask something that requires human intervention: 'I'm ANGRY because 
I was charged twice and I need this FIXED NOW!'"

[System detects emotional + urgent + account issue; escalates immediately]
Response: "I understand this is urgent and frustrating. 
A specialist needs to investigate right away. 
I'm connecting you now."

"Notice:
✓ Emotional language detected → escalate (don't respond)
✓ Clear empathy
✓ Escalation collected contact info (stored encrypted in SQLite)
✓ Langfuse shows escalation reason + urgency flag"
```

**Demo Case 4: Edge Case (1 min):**
```
"Ambiguous query: 'How do I stop a recurring payment?'"

[System provides procedural steps AND clarifies next step]
Response: "Here are steps to stop a recurring payment through your account... 
If you want us to stop it for you, I can connect an agent who can verify 
your identity and make the change."

"Notice:
✓ Procedural guidance (self-service) separated from transactional (agent-assisted)
✓ Both paths clear to user
✓ Escalation optional, not forced"
```

**Closing (1 min):**
```
"What you've seen:
✓ Informational responses grounded in published policies
✓ Clear refusals for transactions and advice
✓ Immediate escalation for urgent/complex cases
✓ Full audit trail in Langfuse
✓ Zero PII in logs

What's NOT in this MVP (for production later):
✗ Real escalation queue integration
✗ Multi-user authentication
✗ Encrypted vault for PII
✗ Horizontal scaling
✗ GDPR delete workflows

Next steps: [Internal user testing] → [Compliance audit] 
       → [Production hardening] → [External alpha]"
```

---

## 13. Summary & Success Definition

### What "Win" Looks Like on Demo Day (Friday EOD)

**Technical Success:**
- ✓ Streamlit app runs; chat interface responsive
- ✓ 30+ test queries flow through system without crash
- ✓ Responses generated in <5 seconds
- ✓ Langfuse dashboard shows full audit trail
- ✓ SQLite database populated with interactions, no PII persisted

**Safety Success:**
- ✓ Transactional requests →100% escalation
- ✓ Regulated advice requests → 100% denial or escalation
- ✓ Account-specific queries → escalation or redirect
- ✓ Hallucination rate <5%
- ✓ Compliance officer sign-off: "Safe for internal demo"

**Stakeholder Success:**
- ✓ Demo clearly explains what system does/doesn't do
- ✓ Known limitations documented
- ✓ Roadmap for production clear
- ✓ Legal + CRO + compliance all approve
- ✓ Team understands trade-offs and why this is appropriate for internal use

### What Doesn't Matter Yet (Defer to Production)

- ✗ Multi-user concurrency
- ✗ Encrypted vault for PII
- ✗ GDPR/CCPA automated workflows
- ✗ Real CRM escalation queue
- ✗ load testing at scale
- ✗ Penetration testing
- ✗ External security assessment

---

**Status:** Ready for 1-Week Execution  
**Owner:** Engineering Lead + Product Manager + Compliance  
**Next Step:** Team kickoff Monday, April 21, 2026, 9 AM

