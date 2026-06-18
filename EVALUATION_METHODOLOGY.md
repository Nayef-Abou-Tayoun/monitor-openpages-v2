# WXO Agent Evaluation Methodology
## Three-Tier Consistency & Validation Framework

---

## 📋 Overview

This evaluation framework uses a **three-tier approach** to validate WXO Agent outputs without requiring pre-existing ground truth for every domain:

1. **Self-Consistency Evaluation** (Same Agent, Multiple Runs)
2. **Cross-Model Consistency** (Multiple Judge Agents)
3. **Ground Truth Validation** (Consensus vs Similar Use Cases)

---

## 🎯 Evaluation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              THREE-TIER EVALUATION FRAMEWORK                     │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │ Concept Document│
                    └────────┬────────┘
                             │
                             ▼
    ┌────────────────────────────────────────────────────────┐
    │         TIER 1: SELF-CONSISTENCY EVALUATION            │
    │              (Same Agent - 5 Runs)                     │
    └────────────────────────────────────────────────────────┘
                             │
                             ▼
    ┌────────────────────────────────────────────────────────┐
    │      TIER 2: CROSS-MODEL CONSISTENCY EVALUATION        │
    │         (Two Judge Agents with different               |
    |               LLM models - 3 Runs Each)                │
    └────────────────────────────────────────────────────────┘
                             │
                             ▼
    ┌────────────────────────────────────────────────────────┐
    │        TIER 3: GROUND TRUTH VALIDATION (Golden Dataset)│
    │             (Combined Consensus from Judges            |
    |                       vs                               |
    |              Similar Use Case 75%+)                    │
    └────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Final Report   │
                    │  & Confidence   │
                    │     Score       │
                    └─────────────────┘
```

---

## 🔄 TIER 1: Self-Consistency Evaluation

**Objective**: Verify that the same agent produces consistent results across multiple runs.

### Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              TIER 1: SELF-CONSISTENCY (5 RUNS)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Concept Document → WXO Agent (Run 5 Times)                      │
│                                                                  │
│  Run 1: [RSK-01, RSK-02, RSK-03] + [CTL-A, CTL-B, CTL-C]       │
│  Run 2: [RSK-01, RSK-02, RSK-03] + [CTL-A, CTL-B, CTL-C]  ✓    │
│  Run 3: [RSK-01, RSK-02, RSK-04] + [CTL-A, CTL-B, CTL-D]  ⚠    │
│  Run 4: [RSK-01, RSK-02, RSK-03] + [CTL-A, CTL-B, CTL-C]  ✓    │
│  Run 5: [RSK-01, RSK-02, RSK-03] + [CTL-A, CTL-B, CTL-C]  ✓    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ CONSISTENCY ANALYSIS                                      │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Risk Consistency:                                         │  │
│  │   RSK-01: 5/5 runs (100%) ████████████████████████       │  │
│  │   RSK-02: 5/5 runs (100%) ████████████████████████       │  │
│  │   RSK-03: 4/5 runs (80%)  ████████████████░░░░           │  │
│  │   RSK-04: 1/5 runs (20%)  ████░░░░░░░░░░░░░░░           │  │
│  │                                                           │  │
│  │ Control Consistency:                                      │  │
│  │   CTL-A: 5/5 runs (100%) ████████████████████████        │  │
│  │   CTL-B: 5/5 runs (100%) ████████████████████████        │  │
│  │   CTL-C: 4/5 runs (80%)  ████████████████░░░░            │  │
│  │   CTL-D: 1/5 runs (20%)  ████░░░░░░░░░░░░░░░            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ CONSENSUS SELECTION (Majority Voting)                     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Threshold: >50% (3+ out of 5 runs)                        │  │
│  │                                                           │  │
│  │ ✅ Consensus Risks:    RSK-01, RSK-02, RSK-03            │  │
│  │ ❌ Excluded:           RSK-04 (only 1/5 runs)             │  │
│  │                                                           │  │
│  │ ✅ Consensus Controls: CTL-A, CTL-B, CTL-C               │  │
│  │ ❌ Excluded:           CTL-D (only 1/5 runs)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  OUTPUT: Tier 1 Consensus (Self-Consistent Results)             │
│  • 3 Risks with 80%+ consistency                                 │
│  • 3 Controls with 80%+ consistency                              │
│  • Self-Consistency Score: 85%                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Metrics
- **Item Consistency**: % of runs where each item appears
- **Overall Consistency**: Average consistency across all items
- **Stability Score**: Variance in results across runs

---

## ⚖️ TIER 2: Cross-Model Consistency Evaluation

**Objective**: Validate results using two different LLM judge agents, each running 3 times.

### Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│         TIER 2: CROSS-MODEL CONSISTENCY (2 JUDGES)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tier 1 Consensus → Two Judge Agents (Different LLMs)            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ JUDGE AGENT A (e.g., GPT-4) - 3 Runs                   │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ Run A1: [RSK-01✓, RSK-02✓, RSK-03✓]                   │    │
│  │ Run A2: [RSK-01✓, RSK-02✓, RSK-03✓]                   │    │
│  │ Run A3: [RSK-01✓, RSK-02✓, RSK-03⚠]                   │    │
│  │                                                         │    │
│  │ Judge A Consensus: RSK-01, RSK-02, RSK-03              │    │
│  │ Judge A Consistency: 94%                                │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ JUDGE AGENT B (e.g., Claude) - 3 Runs                  │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ Run B1: [RSK-01✓, RSK-02✓, RSK-03✓]                   │    │
│  │ Run B2: [RSK-01✓, RSK-02✓, RSK-03✓]                   │    │
│  │ Run B3: [RSK-01✓, RSK-02⚠, RSK-03✓]                   │    │
│  │                                                         │    │
│  │ Judge B Consensus: RSK-01, RSK-02, RSK-03              │    │
│  │ Judge B Consistency: 89%                                │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ INTER-JUDGE AGREEMENT                                   │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │         Judge A    Judge B    Agreement                 │    │
│  │ RSK-01:   ✓         ✓         ✅ 100%                  │    │
│  │ RSK-02:   ✓         ✓         ✅ 100%                  │    │
│  │ RSK-03:   ✓         ✓         ✅ 100%                  │    │
│  │                                                         │    │
│  │ Inter-Judge Agreement: 100%                             │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ COMPARISON WITH TIER 1                                  │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │         Tier 1    Judge A    Judge B    Consensus       │    │
│  │ RSK-01:   ✓         ✓         ✓         ✅ STRONG      │    │
│  │ RSK-02:   ✓         ✓         ✓         ✅ STRONG      │    │
│  │ RSK-03:   ✓         ✓         ✓         ✅ STRONG      │    │
│  │                                                         │    │
│  │ Three-Way Agreement: 100%                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  OUTPUT: Tier 2 Validated Consensus                              │
│  • All 3 risks validated by both judges                          │
│  • Cross-Model Consistency: 92%                                  │
│  • Confidence Level: HIGH                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Metrics
- **Intra-Judge Consistency**: Each judge's self-consistency (3 runs)
- **Inter-Judge Agreement**: Agreement between Judge A and Judge B
- **Three-Way Consensus**: Agreement across Tier 1 + Both Judges
- **Confidence Score**: Combined consistency metric

---

## 🎯 TIER 3: Ground Truth Validation

**Objective**: Compare combined consensus against a similar use case (75%+ match) from historical data.

### Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│           TIER 3: GROUND TRUTH VALIDATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Generate Combined Consensus from Tier 1 & 2             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Combined Consensus Output:                              │    │
│  │ • RSK-01: Privacy Risk (100% agreement)                 │    │
│  │ • RSK-02: Security Risk (100% agreement)                │    │
│  │ • RSK-03: Regulatory Risk (95% agreement)               │    │
│  │ • CTL-A, CTL-B, CTL-C (validated controls)              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Step 2: Find Similar Use Case (75%+ Match)                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Search OpenPages for Similar Documents:                 │    │
│  │                                                         │    │
│  │ Current Doc: "Payment Processing System Upgrade"        │    │
│  │                                                         │    │
│  │ Similar Cases Found:                                    │    │
│  │ 1. "Payment Gateway Implementation" - 82% match ✓       │    │
│  │ 2. "Digital Payment Platform" - 78% match ✓             │    │
│  │ 3. "Transaction Processing Update" - 76% match ✓        │    │
│  │                                                         │    │
│  │ Selected: "Payment Gateway Implementation" (82%)        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Step 3: Compare Against Historical Assessment                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ COMPARISON TABLE                                        │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │ Risk/Control    │ AI Consensus │ Historical │ Match?   │    │
│  │ ─────────────────────────────────────────────────────  │    │
│  │ Privacy Risk    │      ✓       │     ✓      │  ✅      │    │
│  │ Security Risk   │      ✓       │     ✓      │  ✅      │    │
│  │ Regulatory Risk │      ✓       │     ✗      │  ❌      │    │
│  │ Third Party Risk│      ✗       │     ✓      │  ❌      │    │
│  │                                                         │    │
│  │ CTL-A          │      ✓       │     ✓      │  ✅      │    │
│  │ CTL-B          │      ✓       │     ✓      │  ✅      │    │
│  │ CTL-C          │      ✓       │     ✗      │  ❌      │    │
│  │ CTL-E          │      ✗       │     ✓      │  ❌      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Step 4: Calculate Ground Truth Metrics                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ GROUND TRUTH VALIDATION METRICS                         │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │ Risk Matching:                                          │    │
│  │   Precision = 2/3 = 66.7%  (2 correct, 1 extra)        │    │
│  │   Recall    = 2/3 = 66.7%  (2 found, 1 missed)         │    │
│  │   F1 Score  = 66.7%                                     │    │
│  │                                                         │    │
│  │ Control Matching:                                       │    │
│  │   Precision = 2/3 = 66.7%                               │    │
│  │   Recall    = 2/3 = 66.7%                               │    │
│  │   F1 Score  = 66.7%                                     │    │
│  │                                                         │    │
│  │ Overall Alignment: 66.7%                                │    │
│  │ Use Case Similarity: 82%                                │    │
│  │                                                         │    │
│  │ Weighted Score: (66.7% × 0.7) + (82% × 0.3) = 71.3%    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  OUTPUT: Ground Truth Validation Score                           │
│  • Alignment with historical data: 66.7%                         │
│  • Use case similarity: 82%                                      │
│  • Confidence: MEDIUM-HIGH                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Similarity Matching Criteria
- **Document Content**: Text similarity (TF-IDF, embeddings)
- **Domain/Topic**: Same business area
- **Process Type**: Similar process characteristics
- **Minimum Threshold**: 75% similarity required

---

## 📊 Final Evaluation Report

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPREHENSIVE EVALUATION REPORT                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Document: "Payment Processing System Upgrade"                   │
│  Evaluation Date: 2026-06-18                                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ TIER 1: SELF-CONSISTENCY                                │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ Runs: 5                                                 │    │
│  │ Risk Consistency:    85% ████████████████░░░░          │    │
│  │ Control Consistency: 82% ████████████████░░░░          │    │
│  │ Overall Score:       83.5% ⭐⭐⭐⭐☆                    │    │
│  │ Status: ✅ PASS (>80% threshold)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ TIER 2: CROSS-MODEL CONSISTENCY                         │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ Judge A Consistency: 94% ██████████████████░░          │    │
│  │ Judge B Consistency: 89% █████████████████░░░          │    │
│  │ Inter-Judge Agreement: 100% ████████████████████████   │    │
│  │ Three-Way Consensus: 92% ██████████████████░░          │    │
│  │ Overall Score:       93.8% ⭐⭐⭐⭐⭐                   │    │
│  │ Status: ✅ PASS (>85% threshold)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ TIER 3: GROUND TRUTH VALIDATION                         │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ Similar Case: "Payment Gateway Implementation"          │    │
│  │ Similarity Score: 82%                                   │    │
│  │ Risk F1 Score:    66.7% █████████████░░░░░░░           │    │
│  │ Control F1 Score: 66.7% █████████████░░░░░░░           │    │
│  │ Weighted Score:   71.3% ██████████████░░░░░░           │    │
│  │ Overall Score:    71.3% ⭐⭐⭐⭐☆                       │    │
│  │ Status: ✅ PASS (>70% threshold)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ FINAL CONFIDENCE SCORE                                  │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │ Tier 1 Weight: 30% × 83.5% = 25.1%                     │    │
│  │ Tier 2 Weight: 40% × 93.8% = 37.5%                     │    │
│  │ Tier 3 Weight: 30% × 71.3% = 21.4%                     │    │
│  │                                                         │    │
│  │ TOTAL SCORE: 84.0% ████████████████░░░░                │    │
│  │                                                         │    │
│  │ ⭐⭐⭐⭐☆ HIGH CONFIDENCE                                │    │
│  │                                                         │    │
│  │ Recommendation: ✅ ACCEPT AI OUTPUT                     │    │
│  │ Manual Review: Recommended for 1 risk (Regulatory)     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ KEY FINDINGS                                            │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ ✅ Strong self-consistency (83.5%)                      │    │
│  │ ✅ Excellent cross-model agreement (93.8%)              │    │
│  │ ⚠️  Moderate alignment with historical data (71.3%)     │    │
│  │ 💡 Consider reviewing Regulatory Risk selection         │    │
│  │ 💡 Third Party Risk was missed (in historical data)     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Confidence Levels & Thresholds

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIDENCE SCORING MATRIX                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Final Score Range    │ Confidence Level │ Recommendation       │
│  ──────────────────────────────────────────────────────────────│
│  90% - 100%          │ ⭐⭐⭐⭐⭐ VERY HIGH │ Auto-Accept         │
│  80% - 89%           │ ⭐⭐⭐⭐☆ HIGH      │ Accept w/ Spot Check│
│  70% - 79%           │ ⭐⭐⭐☆☆ MEDIUM    │ Review Flagged Items│
│  60% - 69%           │ ⭐⭐☆☆☆ LOW       │ Manual Review Needed│
│  < 60%               │ ⭐☆☆☆☆ VERY LOW   │ Reject / Redo       │
│                                                                  │
│  Individual Tier Thresholds:                                     │
│  • Tier 1 (Self-Consistency):     >80% to pass                  │
│  • Tier 2 (Cross-Model):          >85% to pass                  │
│  • Tier 3 (Ground Truth):         >70% to pass                  │
│                                                                  │
│  Weighting:                                                      │
│  • Tier 1: 30% (baseline consistency)                            │
│  • Tier 2: 40% (cross-validation strength)                       │
│  • Tier 3: 30% (real-world alignment)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Guide

### Step-by-Step Process

```
1. TIER 1 EXECUTION
   ├─ Run WXO Agent 5 times on same document
   ├─ Extract risks, controls, ratings from each run
   ├─ Calculate consistency metrics
   ├─ Apply majority voting (>50% threshold)
   └─ Generate Tier 1 consensus output

2. TIER 2 EXECUTION
   ├─ Select 2 different LLM judge agents
   ├─ Run Judge A 3 times on Tier 1 consensus
   ├─ Run Judge B 3 times on Tier 1 consensus
   ├─ Calculate intra-judge consistency
   ├─ Calculate inter-judge agreement
   └─ Generate Tier 2 validated consensus

3. TIER 3 EXECUTION
   ├─ Search OpenPages for similar use cases (75%+ match)
   ├─ Retrieve historical risk/control associations
   ├─ Compare AI consensus vs historical data
   ├─ Calculate Precision, Recall, F1 scores
   └─ Generate ground truth validation metrics

4. FINAL REPORT
   ├─ Combine all three tier scores
   ├─ Apply weighted scoring
   ├─ Determine confidence level
   ├─ Generate recommendations
   └─ Flag items for manual review
```

---

## 📈 Benefits of This Approach

### ✅ Advantages

1. **No Pre-Existing Ground Truth Required**
   - Works across different domains and topics
   - Adapts to new use cases automatically

2. **Multi-Layer Validation**
   - Self-consistency catches random errors
   - Cross-model validation reduces model bias
   - Historical comparison provides real-world check

3. **Quantifiable Confidence**
   - Clear metrics at each tier
   - Weighted final score
   - Actionable thresholds

4. **Scalable & Automated**
   - Can run automatically for each document
   - Minimal manual intervention needed
   - Continuous improvement through feedback

5. **Transparent & Explainable**
   - Clear reasoning at each tier
   - Identifies specific areas of concern
   - Provides evidence for decisions

---

## 🚀 Usage Example

```python
# Pseudo-code for evaluation framework

evaluator = ThreeTierEvaluator()

# Tier 1: Self-Consistency
tier1_result = evaluator.run_tier1(
    document="concept_doc.docx",
    agent=wxo_agent,
    num_runs=5
)
# Output: 83.5% consistency, consensus of 3 risks, 3 controls

# Tier 2: Cross-Model Consistency
tier2_result = evaluator.run_tier2(
    tier1_consensus=tier1_result.consensus,
    judge_a=gpt4_judge,
    judge_b=claude_judge,
    runs_per_judge=3
)
# Output: 93.8% cross-model agreement

# Tier 3: Ground Truth Validation
tier3_result = evaluator.run_tier3(
    combined_consensus=tier2_result.consensus,
    similarity_threshold=0.75,
    openpages_client=op_client
)
# Output: 71.3% alignment with historical data

# Final Report
final_report = evaluator.generate_report(
    tier1=tier1_result,
    tier2=tier2_result,
    tier3=tier3_result
)
# Output: 84.0% overall confidence, HIGH confidence level
```

---

## 📝 Summary

This three-tier evaluation methodology provides:

- **Tier 1**: Internal consistency validation (same agent, multiple runs)
- **Tier 2**: External validation (different models, cross-checking)
- **Tier 3**: Real-world validation (historical similar cases)

**Result**: A robust, scalable evaluation framework that doesn't require pre-existing ground truth for every domain, while still providing quantifiable confidence scores and actionable insights.

---

*This methodology ensures reliable AI agent performance across diverse domains and use cases through multi-layered validation.*
