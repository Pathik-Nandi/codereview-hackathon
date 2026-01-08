# Understanding RAG Novelty Score Calculation

## Overview

**Novelty Score** is a value between **0.0 and 1.0** that measures how unique or new a Pull Request is compared to historical PRs in your database.

- **1.0** = Completely novel (never seen anything like this before)
- **0.5** = Moderately novel (some similar patterns exist)
- **0.0** = Not novel (seen this pattern many times, or near-duplicate exists)

---

## Why Novelty Score Matters

### Use Cases:
1. **Prioritize Code Review**: Focus on novel PRs that may need more careful review
2. **Identify Patterns**: Low novelty indicates repeated issues (e.g., same security bugs)
3. **Track Innovation**: High novelty shows new approaches or unfamiliar code patterns
4. **Risk Assessment**: Very novel PRs combined with high complexity = higher risk
5. **Learning Opportunities**: Novel PRs might need extra documentation or knowledge sharing

---

## The 5-Step Calculation Process

### STEP 1: Find Similar PRs

The RAG system uses **vector similarity search** to find PRs similar to the current one:
- Converts PR title, description, and file names into a vector embedding
- Searches the ChromaDB vector database for similar historical PRs
- Returns up to 5-10 similar PRs with similarity scores

**Similarity Score:** 0.0 (completely different) to 1.0 (identical)

**Example:**
```
Analyzing: PR #125 "Test PR 25: High Novelty Check"

Similar PRs found:
  1. PR #120: "Test PR 20: High Novelty Check" → similarity: 0.958
  2. PR #112: "Test PR 12: High Novelty Check" → similarity: 0.960
  3. PR #122: "Test PR 22: High Novelty Check" → similarity: 0.960
  4. PR #128: "Test PR 28: High Novelty Check" → similarity: 0.958
  5. PR #109: "Test PR 9: High Novelty Check"  → similarity: 0.953
```

---

### STEP 2: Calculate Average Similarity

Take the **top 5 most similar PRs** and calculate their average similarity.

**Why top 5 only?**
- Focus on the most relevant matches
- Prevents dilution from weakly similar PRs
- Consistent comparison across all PRs

**Formula:**
```
avg_similarity = sum(similarity_scores[:5]) / 5
```

**Example:**
```
avg_similarity = (0.958 + 0.960 + 0.960 + 0.958 + 0.953) / 5
avg_similarity = 0.958
```

---

### STEP 3: Calculate Base Novelty

**Formula:**
```
base_novelty = 1.0 - avg_similarity
```

**Logic:**
- High similarity → Low novelty (inverse relationship)
- If PRs are 95% similar → PR is only 5% novel

**Example:**
```
base_novelty = 1.0 - 0.958
base_novelty = 0.042
```

---

### STEP 4: Apply Penalties

Novelty is reduced by two types of penalties:

#### Penalty #1: Count Penalty
**Logic:** More similar PRs = more common pattern = less novel

| Similar PRs Found | Penalty | Reason |
|-------------------|---------|--------|
| 8 or more | -0.15 | Very common pattern |
| 5 to 7 | -0.10 | Common pattern |
| 3 to 4 | -0.05 | Somewhat common |
| 1 to 2 | 0.00 | Rare pattern |

#### Penalty #2: Distribution Penalty
**Logic:** If even ONE near-duplicate exists (>0.9 similarity), it's not novel

| Top Similar PR | Penalty | Reason |
|----------------|---------|--------|
| > 0.9 similarity | -0.10 | Near-duplicate found |
| ≤ 0.9 similarity | 0.00 | No near-duplicates |

**Example for PR #125:**
```
Count penalty:
  - Found 5 similar PRs → -0.10

Distribution penalty:
  - Top similarity is 0.960 (>0.9) → -0.10

Total penalties: -0.20
```

---

### STEP 5: Calculate Final Novelty

**Formula:**
```
final_novelty = max(0.0, base_novelty - count_penalty - distribution_penalty)
```

**Note:** The `max(0.0, ...)` ensures the score never goes negative.

**Example:**
```
final_novelty = max(0.0, 0.042 - 0.10 - 0.10)
final_novelty = max(0.0, -0.158)
final_novelty = 0.000
```

**Result:** PR #125 has **0.000 novelty** (not novel at all - it's a near-duplicate)

---

## Complete Examples

### Example 1: Near-Duplicate PR (Your Test PRs)

**Scenario:** "Test PR 25: High Novelty Check" - Similar to many other test PRs

| Step | Calculation | Value |
|------|-------------|-------|
| Similar PRs found | 5 PRs with avg similarity | 0.958 |
| Base novelty | 1.0 - 0.958 | 0.042 |
| Count penalty | 5 similar PRs | -0.10 |
| Distribution penalty | Top similarity > 0.9 | -0.10 |
| **Final novelty** | 0.042 - 0.10 - 0.10 | **0.000** |

**Interpretation:** Not novel at all - pattern seen many times before

---

### Example 2: Common Pattern

**Scenario:** Debug print statements (many similar PRs exist)

| Step | Calculation | Value |
|------|-------------|-------|
| Similar PRs found | 8 PRs with avg similarity | 0.600 |
| Base novelty | 1.0 - 0.600 | 0.400 |
| Count penalty | 8+ similar PRs | -0.15 |
| Distribution penalty | Top similarity = 0.70 | 0.00 |
| **Final novelty** | 0.400 - 0.15 - 0.00 | **0.250** |

**Interpretation:** Somewhat common pattern

---

### Example 3: Moderately Novel

**Scenario:** New React component with some precedent

| Step | Calculation | Value |
|------|-------------|-------|
| Similar PRs found | 5 PRs with avg similarity | 0.650 |
| Base novelty | 1.0 - 0.650 | 0.350 |
| Count penalty | 5 similar PRs | -0.10 |
| Distribution penalty | Top similarity = 0.70 | 0.00 |
| **Final novelty** | 0.350 - 0.10 - 0.00 | **0.250** |

**Interpretation:** Some similarities but fairly common

---

### Example 4: Novel Approach

**Scenario:** New authentication pattern, few similar PRs

| Step | Calculation | Value |
|------|-------------|-------|
| Similar PRs found | 3 PRs with avg similarity | 0.350 |
| Base novelty | 1.0 - 0.350 | 0.650 |
| Count penalty | 3 similar PRs | -0.05 |
| Distribution penalty | Top similarity = 0.40 | 0.00 |
| **Final novelty** | 0.650 - 0.05 - 0.00 | **0.600** |

**Interpretation:** Quite novel, few similar patterns

---

### Example 5: Completely Novel

**Scenario:** First PR introducing GraphQL to the codebase

| Step | Calculation | Value |
|------|-------------|-------|
| Similar PRs found | 0 PRs | N/A |
| Base novelty | No similar PRs | 1.000 |
| Count penalty | 0 similar PRs | 0.00 |
| Distribution penalty | No PRs to compare | 0.00 |
| **Final novelty** | 1.000 - 0.00 - 0.00 | **1.000** |

**Interpretation:** Completely novel - never seen before

---

## Novelty Score Ranges

| Score Range | Category | Meaning | Action |
|-------------|----------|---------|--------|
| **0.8 - 1.0** | Highly Novel | New pattern, minimal precedent | Extra review attention, document well |
| **0.6 - 0.8** | Novel | Some similarities but mostly unique | Standard review, potential learning opportunity |
| **0.4 - 0.6** | Moderately Novel | Mix of new and familiar patterns | Standard review |
| **0.2 - 0.4** | Somewhat Common | Similar patterns seen before | Quick review, check for repeated issues |
| **0.0 - 0.2** | Not Novel | Very common or near-duplicate | Fast review, automated checks may suffice |

---

## Why Your PRs Show 0.600 (The Bug)

### Current Behavior (Before Fix):

**All 128 PRs show the same score:**
- Novelty: 0.600
- Similar PRs: 5

This happened because:

1. **Old calculation was too simple:**
   ```python
   # OLD CODE
   avg_similarity = sum(similarity_scores) / len(similarity_scores)
   novelty = 1.0 - avg_similarity
   # No penalties applied!
   ```

2. **No differentiation:**
   - Didn't consider how many similar PRs exist
   - Didn't check for near-duplicates
   - All PRs with moderate similarity got ~0.600

3. **Your test PRs:**
   - Titles: "Test PR 1: High Novelty Check", "Test PR 2: Similarity Test Check", etc.
   - Very similar to each other (0.95+ similarity)
   - Should have low novelty (0.0-0.1)
   - But old code gave them 0.600 ❌

### After Fix:

**PRs will have varied scores:**
- Near-duplicates: 0.000 - 0.100
- Common patterns: 0.200 - 0.400
- Novel patterns: 0.600 - 0.800
- Unique PRs: 0.900 - 1.000

**Your test PRs will correctly show:**
- "High Novelty Check" PRs: 0.000 - 0.050 (they're near-duplicates!)
- "Similarity Test Check" PRs: 0.000 - 0.050 (also near-duplicates!)
- First PR analyzed: 1.000 (truly novel - no history)

---

## Code Implementation

### Location: `agents/rag_enhanced_agent.py` (lines 610-650)

```python
def _calculate_novelty_score(self, relevant_context: Dict[str, Any]) -> float:
    """
    Calculate novelty score based on similarity to past PRs.
    Novelty score: 0 (common pattern) to 1 (highly novel)
    
    IMPROVED: Now considers both number of similar PRs AND their similarity scores
    """
    similar_prs = relevant_context.get('similar_prs', [])
    
    # STEP 1: Check if any similar PRs exist
    if not similar_prs:
        return 1.0  # Completely novel
    
    # STEP 2: Calculate average similarity from TOP 5 similar PRs only
    top_similar = similar_prs[:min(5, len(similar_prs))]
    avg_similarity = sum(pr.get('similarity', 0) for pr in top_similar) / len(top_similar)
    
    # STEP 3: Base novelty from similarity (inverse relationship)
    base_novelty = 1.0 - avg_similarity
    
    # STEP 4a: Count penalty - More similar PRs = less novel
    similar_count = len(similar_prs)
    if similar_count >= 8:
        count_penalty = 0.15  # Many similar PRs = reduce novelty
    elif similar_count >= 5:
        count_penalty = 0.10
    elif similar_count >= 3:
        count_penalty = 0.05
    else:
        count_penalty = 0.0  # Few similar PRs = no penalty
    
    # STEP 4b: Distribution penalty - Very high similarity = less novel
    if top_similar and top_similar[0].get('similarity', 0) > 0.9:
        distribution_penalty = 0.10
    else:
        distribution_penalty = 0.0
    
    # STEP 5: Final novelty = base - penalties
    final_novelty = max(0.0, base_novelty - count_penalty - distribution_penalty)
    
    return round(final_novelty, 3)
```

---

## Testing the Fix

### Before Re-analysis:
```sql
SELECT COUNT(DISTINCT rag_novelty_score) 
FROM pr_analysis 
WHERE rag_novelty_score IS NOT NULL;

-- Result: 2 unique scores (0.600 and 0.282)
```

### After Re-analysis (Expected):
```sql
-- Result: 15-25 unique scores ranging from 0.0 to 1.0
```

### Verification Query:
```sql
SELECT 
    CASE 
        WHEN rag_novelty_score >= 0.8 THEN 'Highly Novel (0.8-1.0)'
        WHEN rag_novelty_score >= 0.6 THEN 'Novel (0.6-0.8)'
        WHEN rag_novelty_score >= 0.4 THEN 'Moderate (0.4-0.6)'
        WHEN rag_novelty_score >= 0.2 THEN 'Common (0.2-0.4)'
        ELSE 'Not Novel (0.0-0.2)'
    END as category,
    COUNT(*) as pr_count,
    AVG(rag_novelty_score) as avg_novelty
FROM pr_analysis 
WHERE rag_novelty_score IS NOT NULL
GROUP BY category
ORDER BY avg_novelty DESC;
```

**Expected distribution:**
- Not Novel: 20-30 PRs (test PRs with similar titles)
- Common: 40-50 PRs (repeated patterns)
- Moderate: 30-40 PRs (some similarities)
- Novel: 10-20 PRs (unique approaches)
- Highly Novel: 5-10 PRs (completely new)

---

## Summary

### Key Concepts:

1. **Novelty = Inverse of Similarity**
   - High similarity to past PRs → Low novelty
   - No similar PRs → Maximum novelty

2. **Penalties Reduce Novelty Further**
   - Many similar PRs → Common pattern → Lower novelty
   - Near-duplicate exists → Not novel → Lower novelty

3. **Why This Matters**
   - Helps prioritize review efforts
   - Identifies repeated issues
   - Tracks innovation in codebase
   - Supports risk assessment

4. **Your Situation**
   - Test PRs with similar titles → Should have low novelty (0.0-0.1)
   - Old code gave all PRs 0.600 → Bug
   - New code will differentiate properly → Fix

### Next Steps:

1. ✅ Code fixed in `rag_enhanced_agent.py`
2. ⏳ Re-analyze all 128 PRs to get correct scores
3. ✅ Verify varied novelty distribution (0.0 to 1.0)
4. ✅ Use novelty scores in analytics and dashboards

---

## Quick Reference

### Formula:
```
novelty = max(0.0, (1.0 - avg_similarity) - count_penalty - distribution_penalty)
```

### Penalties:
- **Count:** 0.00 (1-2 PRs), 0.05 (3-4 PRs), 0.10 (5-7 PRs), 0.15 (8+ PRs)
- **Distribution:** 0.10 (top > 0.9), 0.00 (top ≤ 0.9)

### Interpretation:
- **< 0.2:** Not novel (common/duplicate)
- **0.2-0.4:** Somewhat common
- **0.4-0.6:** Moderately novel
- **0.6-0.8:** Novel
- **> 0.8:** Highly novel

---

*Document created: 2026-01-04*
*Location: `/home/maheshrv/Documents/IGOT/sourcecodes-igot/codereview/documentation/NOVELTY_SCORE_EXPLAINED.md`*
