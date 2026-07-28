# APE — Product Vision
## Founding Manifesto v1.1

*This document is not a technical specification. It is the founding vision of a long-term software company. It exists to answer the single most important question any team member or tool can ask: "Why does APE exist?"*

---

## 1. What is APE?

APE is an **AI Product Operating System for the solo founder.**

It is the command center from which a single person discovers opportunities, validates ideas, builds products, and launches them — continuously, systematically, and faster than any team of five could a decade ago.

APE is not a productivity tool. It is not a framework. It is not a code generator.

APE is the operating layer between a human founder's intention and the market's response.

---

## 2. What Problems Does It Solve?

The solo founder faces a specific, painful constellation of problems that no existing tool was designed to solve together:

**Problem 1 — Opportunity Blindness**
The world generates thousands of solvable, profitable problems every day. A solo founder cannot monitor them. They build what they already know, not what the market needs today.

**Problem 2 — Validation Paralysis**
Even when an idea exists, validation is slow, manual, and expensive. Most ideas die not because they were bad, but because the cost of learning was too high.

**Problem 3 — Context Collapse**
A solo founder is simultaneously the product manager, engineer, marketer, and support team. They lose context constantly. Decisions made at 9am are forgotten by 3pm. Learnings from one product never transfer to the next.

**Problem 4 — Execution Friction**
The gap between "I have an idea" and "I have something deployed" is filled with repetitive, low-value work: setup, configuration, scaffolding, documentation, naming. This friction kills momentum.

**Problem 5 — Revenue Blindness**
Most technical founders cannot accurately see which product activity generates revenue and which one is noise. They optimize for engineering satisfaction instead of market feedback.

APE exists to solve all five of these problems simultaneously, for one person, without requiring a team.

---

## 3. Who Are the Primary Users?

APE is built for exactly one primary user archetype:

**The Technical Solo Founder** — A developer or engineer who wants to build profitable AI-adjacent products independently. They are comfortable with terminals and code. They are impatient with manual work. They are ambitious but resource-constrained. They want leverage, not manpower.

Secondary users who will benefit:
- Small founding teams (2-3 people) who want a shared operational system
- Indie hackers moving from hobbyist to commercial
- Developer-consultants who want to productize their expertise

---

## 4. Who Should NEVER Use APE?

APE is explicitly not designed for:

- **Large engineering organizations** who have dedicated product, data, and DevOps teams. APE's value is leverage for individuals; in large teams it becomes overhead.
- **Non-technical founders** who cannot reason about service design, configuration files, or structured data. APE assumes terminal fluency.
- **Founders seeking feature completeness before launching.** APE favors rapid market contact. Those seeking "perfection before ship" will find APE's philosophy hostile.
- **Teams requiring enterprise compliance, audit trails, or SOC-2 certification.** APE is a founder's cockpit, not an enterprise software platform.

---

## 5. What Can a User Accomplish?

### After One Day
- APE is installed and the workspace is initialized.
- The user has run their first environment health check (`ape doctor`).
- The user has seen their first market signal scan from a configured source (e.g., HackerNews, GitHub Trends).
- They have a clear picture of three unsolved problems in their chosen domain.

### After One Week
- The user has scored at least 10 opportunity signals using APE's Opportunity Scorer.
- They have selected one idea and generated a validation plan with APE's Research Engine.
- They have produced a micro-landing page skeleton from APE's Content Factory.
- They have published their first piece of product-relevant content drafted with APE assistance.

### After One Month
- The user has launched a minimal product (even if zero revenue).
- They have a working feedback loop: market signal → idea → validation → product → launch → feedback.
- APE has learned enough about the user's domain preferences to begin proactively surfacing relevant opportunities without being asked.
- The user has saved at least 10 hours of manual research and setup work.

### After Six Months
- The user has launched at least 2-3 products and measured their market response.
- APE's Intelligence layer has built a persistent knowledge base from the user's research and product history.
- The user can generate a new product concept, validate it against market data, and have a deployable scaffold in under 48 hours.
- APE is generating compounding leverage: each new product builds on the knowledge infrastructure of the previous ones.

---

## 6. Permanent Architectural Pillars

*These must never be violated regardless of how APE evolves:*

**Pillar 1 — Single Binary Entry Point**
All APE capabilities are accessible through one CLI command: `ape`. No separate tools, no fragmented executables, no parallel CLIs. Everything flows through one entry point.

**Pillar 2 — Local-First, Remote-Optional**
APE must work completely offline for all core features. Remote capabilities (API calls, web scanning, AI inference) are additive — never required for basic operation.

**Pillar 3 — Zero Configuration Required to Start**
A user must be able to run `ape init` and have a functional workspace within 60 seconds, with no external dependencies beyond a Python installation.

**Pillar 4 — No Vendor Lock-In at the Core**
The Core layer must never hardcode any specific AI provider, cloud platform, or SaaS service. All external integrations live in modules, not in Core.

**Pillar 5 — Transparent Data Ownership**
Everything APE learns, stores, or generates lives in the user's own filesystem in human-readable formats. No opaque databases. No cloud-required persistence.

---

## 7. Permanent Product Pillars

*Every future module, feature, and sprint must satisfy all of these:*

**Pillar A — Solves a Real Founder Pain**
Every addition must directly address one of the five core problems (Opportunity Blindness, Validation Paralysis, Context Collapse, Execution Friction, Revenue Blindness).

**Pillar B — Compounding Value**
Each module must make subsequent modules more powerful. A Research Engine finding must feed into the Opportunity Scorer. A product launch must update the Knowledge Base. APE must grow smarter with use.

**Pillar C — Speed Over Perfection**
APE biases toward giving the user a working answer in 30 seconds over a perfect answer in 30 minutes. Accuracy can be refined; momentum cannot be recovered.

**Pillar D — Revenue Proximity**
Every module must be at most two steps from generating or protecting revenue. Purely academic, visualization-for-visualization's-sake, or vanity features are rejected.

---

## 8. The Four Development Tracks

---

### Track 1: Core
**Mission:** Core exists only as long as it accelerates the other four tracks. The moment a Core sprint cannot be justified by its downstream impact on Intelligence, Products, Business, or Evolution — it must be rejected. Core is never the product. It is the foundation that makes every other product possible.

**Success Metrics:**
- Time from `ape init` to functional workspace: under 60 seconds.
- Zero breaking changes in the public API between versions.
- All tests passing. Zero regressions.
- No architectural debt carried across more than 2 sprints.

**Example Future Modules:**
- Workspace Manager (multi-project support)
- Plugin Loader (importlib-based discovery)
- Config Versioning (safe migrations)
- Structured Logging (machine-readable session traces)

---

### Track 2: Intelligence
**Mission:** Give APE eyes and memory. This track builds the systems that observe the world, learn from user history, and surface relevant signals without being explicitly asked.

**Success Metrics:**
- Number of relevant opportunities surfaced per week (relevance rated by user).
- Reduction in manual research time per product cycle.
- Accuracy of domain predictions after 30-day learning period.
- Knowledge base growth rate (new useful facts per session).

**Example Future Modules:**
- Market Scanner (GitHub, HackerNews, Product Hunt, Reddit monitors)
- Trend Engine (pattern recognition across data sources)
- Research Engine (structured competitive and audience research)
- Knowledge Base (persistent, queryable user knowledge store)
- Release Watcher (monitoring competitor product updates)
- Prompt Evolver (A/B testing and improvement of internal AI prompts)
- World Model (a current-state map of the AI and technology landscape — relating trends, API changes, competitor moves, and market shifts into a single queryable picture of the world as it stands today)

---

### Track 3: Products
**Mission:** Turn intelligence into deployable output. This track gives the user the tools to move from an insight to something that exists in the world.

**Success Metrics:**
- Time from idea to deployed MVP artifact (target: under 48 hours).
- Number of product artifacts generated per month.
- User-reported hours saved per product cycle.
- Percentage of generated scaffolds actually shipped.

**Example Future Modules:**
- Opportunity Scorer (automated idea scoring against market signals)
- SaaS Generator (scaffold a deployable product from a scored idea)
- Content Factory (blog posts, landing pages, product descriptions)
- Automation Builder (connect APIs and data sources without code)
- Launch Assistant (ProductHunt submission, email campaigns, announcement copy)
- Micro-SaaS Builder (end-to-end minimal product scaffolding)

---

### Track 4: Business
**Mission:** Close the loop between building and earning. This track makes revenue, competition, and market position visible and actionable.

**Success Metrics:**
- Accuracy of revenue tracking per product.
- Speed of competitor change detection.
- Number of actionable pricing decisions supported per quarter.
- ROI calculation accuracy for APE's own usage.

**Example Future Modules:**
- Revenue Tracker (aggregate revenue across multiple products)
- Competitor Monitor (track pricing, feature, and positioning changes)
- Pricing Engine (suggest optimal pricing based on market research)
- Marketing Asset Generator (produce sale-ready copy and visuals)
- Sales Automation (outreach templates, email sequences)

---

### Track 5: Evolution
**Mission:** Make APE learn from its own history. This track is not about observing the market — it is about observing APE itself and the user's track record. Every prompt, every product, every failure, and every success becomes evidence that shapes the next decision.

The key distinction: APE does not *remember*. APE *proves*.

A Knowledge Base stores facts: *"GPT-5 was released."*
An Evidence Base stores outcomes and causality: *"Prompt X was used 12 times. It succeeded 9 times. Claude succeeded. Gemini failed. Success rate has declined since July 2026."*

This transforms APE from a tool that recalls the past into a system that derives policy from evidence. The long-term arc of this track is:

> Evidence → Insight → Policy

APE collects data, forms evidence, and eventually updates its own behavior based on what has been proven to work.

**The questions this track must continuously answer:**
- Which prompts produced better results, and under what conditions?
- Which AI models performed best for which task types?
- Which tools or APIs have become obsolete or unavailable?
- Which workflows consistently fail and why?
- Which product ideas generated revenue and what made them different?
- Which ideas failed and what signals predicted the failure?

**Success Metrics:**
- Measurable improvement in opportunity scoring accuracy over time (baseline vs. 30/90-day performance).
- Reduction in repeated mistakes across product cycles.
- Increase in the percentage of surfaced ideas that the user acts on.
- Model selection accuracy: did APE recommend the right tool for the right task?

**Example Future Modules:**
- Experience Base (persistent, queryable record of outcomes — not just facts)
- Prompt Performance Tracker (evidence-based A/B tracking of prompt effectiveness)
- Model Intelligence Monitor (which AI model excels at which task type, proven by outcomes)
- Failure Analyst (structured post-mortem logging for products and ideas)
- Workflow Health Monitor (detect broken or degraded automation pipelines)
- Tool Freshness Scanner (detect deprecated APIs, abandoned libraries, dead endpoints)

---

## 9. Sprint Evaluation Scorecard

Every proposed sprint must be evaluated against four metrics before approval. A sprint that scores zero on two or more metrics should be rejected or deferred.

---

**Technical Value (★ 1-5)**
*Does this sprint reduce technical debt, improve testability, strengthen architectural boundaries, or make future development significantly easier?*
A score of 5 means the sprint unlocks or unblocks multiple future sprints. A score of 1 means the sprint is purely internal with no downstream effect.

---

**User Value (★ 1-5)**
*Does this sprint change what a user can accomplish with APE after it is completed?*
A score of 5 means a user can do something meaningful they could not do before. A score of 1 means the change is invisible to any user.

---

**Revenue Value (★ 1-5)**
*Does this sprint bring APE closer to a capability that can generate, protect, or measure revenue — for the user, or for APE as a product itself?*
A score of 5 means the sprint directly enables a monetizable workflow. A score of 1 means the sprint has no identifiable path to revenue impact.

---

**Learning Value (★ 1-5)**
*Does this sprint teach us something we do not yet know — about the market, the user, the technology, or APE's own product-market fit?*
A score of 5 means the sprint will produce falsifiable insights that change our next decision. A score of 1 means the sprint confirms only what we already know.

> **Rule:** No sprint may proceed if its combined score across all four metrics is below 8 out of 20. Sprints scoring only on Technical Value are explicitly deferred until they unlock a sprint that scores on User, Revenue, or Learning Value.

---

## 10. The APE Constitution

> **Every module must increase at least one of the following:**
> - Knowledge
> - Revenue
> - Decision Quality
>
> **If it increases none of them, it does not belong in APE.**

This is the filter applied before every sprint, every module, and every architectural decision. It is shorter than the North Star and faster to apply. When in doubt, use this first.

---

## 11. The Principle of Shipping

> **APE never earns value from unfinished perfection.**
>
> Every major capability should become usable before it becomes complete.
>
> Shipping creates evidence. Evidence improves APE. Improvement creates leverage.

The loop is:

```
Ship → Learn → Improve → Ship Again
```

This principle exists to permanently prevent the most common failure mode of technical founders: spending 12 months building infrastructure, emerging with nothing a user can touch, and calling it "foundational work."

There is no foundational work. There is only work that ships and work that doesn't.

---

## 12. Governance

APE's rules, architecture decisions, manifesto, and roadmap form a governance layer above the five development tracks. This layer changes slower than code, and only when experience provides sufficient evidence.

> *Governance defines how APE evolves. It is not a product. It is not a track. It is the system by which all other decisions are made — and it earns the right to change only when the Evidence Base demands it.*

---

## 13. The North Star

> **APE exists so that one person, with one machine, can find the right problem, build the right product, and reach the right customer — faster than a team of ten could five years ago.**

> *Every shipped product makes APE smarter. Every failure makes the next product more likely to succeed.*

When the team is lost, when the roadmap is unclear, when a debate about architecture or features reaches an impasse — return to this statement. If what you are building does not make this sentence more true, stop building it.

---

## Self-Critique: Challenging This Vision

**Is "AI Product Operating System" just a grandiose name for a CLI tool with some scrapers?**
Yes. At launch, that is exactly what it is. The danger is confusing the vision with the current reality. APE today is a CLI foundation. This document describes where it must go — but the path is through small, working, shipping sprints. The vision does not change; the build order must remain humble.

**Is the "six months" milestone realistic for one person?**
Partially. A "working feedback loop" in one month and "2-3 launched products" in six months assumes the Intelligence and Products tracks move quickly. Those tracks depend on the Core being stable. If Core sprints stall, the entire timeline slips. The Core Track must be ruthlessly lean — it exists only to enable the other three tracks.

**Is the scorecard too rigid?**
The "minimum 8 out of 20" rule could kill legitimate maintenance or critical bugfix sprints. Emergency sprints (security patches, breaking regressions) must be exempt from this scorecard by default.

**Does "No Vendor Lock-In at the Core" conflict with speed?**
Absolutely. Avoiding OpenAI in the Core means writing abstraction layers. Abstraction layers take time. This pillar will create real friction in the Intelligence track. The resolution is to allow vendor-specific code only inside module boundaries, never in Core. This is a discipline problem, not an architecture problem.

**Is the four-track system too heavy for a solo founder to maintain?**
In theory, yes. In practice, a solo founder does not work all four tracks simultaneously — they sprint in one track at a time. The tracks are strategic categories, not parallel workstreams. A solo founder can work one track per week without confusion.

**The biggest risk:** This document describes a vision that is genuinely ambitious. The failure mode is not that the vision is wrong — it is that the team spends all its time perfecting the Core while the Product and Intelligence tracks produce nothing for users. The Architecture Freeze Rule exists precisely to prevent this. It must be enforced aggressively.
