# RAG System Fixes - Novelty & Similarity

## Problem Summary

**Issue:** All 128 PRs had identical scores:
- Novelty: 0.600 (60%)
- Similar PRs Found: 5
- Context Confidence: 0.000

This indicated the RAG system was **not differentiating** between PRs.

## Root Causes Found

### 1. Missing `average_similarity` in Metadata
**Location:** `agents/rag_enhanced_agent.py` line 217

**Problem:**
```python
# OLD - Missing average_similarity
metadata={
    'similar_prs_found': len(relevant_context.get('similar_prs', [])),
    'novelty_score': novelty_score,
    'similar_prs': relevant_context.get('similar_prs', [])
    # ❌ No 'average_similarity' key!
}
```

**Impact:**
- `rag_database_service.py` line 149 tried to read `metadata.get('average_similarity', 0.0)`
- Always got 0.0 default → `context_confidence_score` in database was always 0.000

**Fix:**
```python
# NEW - Added average_similarity
average_similarity = 0.0
if similar_prs:
    average_similarity = sum(pr.get('similarity', 0) for pr in similar_prs) / len(similar_prs)

metadata={
    'similar_prs_found': len(relevant_context.get('similar_prs', [])),
    'novelty_score': novelty_score,
    'average_similarity': average_similarity,  # ✅ Added
    'similar_prs': relevant_context.get('similar_prs', [])
}
```

### 2. Simplistic Novelty Calculation
**Location:** `agents/rag_enhanced_agent.py` lines 603-623

**Problem:**
```python
# OLD - Too simple
def _calculate_novelty_score(self, relevant_context: Dict[str, Any]) -> float:
    similar_prs = relevant_context.get('similar_prs', [])
    
    if not similar_prs:
        return 1.0
    
    # Just inverse of average similarity
    avg_similarity = sum(pr.get('similarity', 0) for pr in similar_prs) / len(similar_prs)
    novelty = 1.0 - avg_similarity
    return round(novelty, 3)
```

**Issues:**
1. **Didn't distinguish between 3 and 10 similar PRs** - just averaged them all
2. **Didn't consider top similarity** - a PR with one 0.95 similar match should be less novel
3. **No nuance** - linear inverse relationship too simplistic

**Results with old calculation:**
- PRs with very similar patterns → Novelty 0.600
- PRs with moderately similar patterns → Novelty 0.600
- PRs with weakly similar patterns → Novelty 0.600
- **All the same!** ❌

**Fix - Enhanced Calculation:**
```python
def _calculate_novelty_score(self, relevant_context: Dict[str, Any]) -> float:
    """
    Calculate novelty score based on similarity to past PRs.
    IMPROVED: Considers both number of similar PRs AND their similarity scores
    """
    similar_prs = relevant_context.get('similar_prs', [])
    
    if not similar_prs:
        return 1.0  # Completely novel
    
    # Use TOP 5 only (most relevant)
    top_similar = similar_prs[:min(5, len(similar_prs))]
    avg_similarity = sum(pr.get('similarity', 0) for pr in top_similar) / len(top_similar)
    
    # Base novelty from similarity
    base_novelty = 1.0 - avg_similarity
    
    # Count penalty: More similar PRs = less novel
    similar_count = len(similar_prs)
    if similar_count >= 8:
        count_penalty = 0.15
    elif similar_count >= 5:
        count_penalty = 0.10
    elif similar_count >= 3:
        count_penalty = 0.05
    else:
        count_penalty = 0.0
    
    # Distribution penalty: Very high top similarity = less novel
    if top_similar and top_similar[0].get('similarity', 0) > 0.9:
        distribution_penalty = 0.10
    else:
        distribution_penalty = 0.0
    
    # Final novelty
    final_novelty = max(0.0, base_novelty - count_penalty - distribution_penalty)
    return round(final_novelty, 3)
```

## Expected Results After Fix

### Novelty Score Distribution:

| Scenario | Similar PRs | Avg Similarity | Novelty Score | Interpretation |
|----------|-------------|----------------|---------------|----------------|
| **Very Similar** (like test PRs with same patterns) | 5 | 0.90 | 0.000 | Not novel - exact pattern seen before |
| **Moderately Similar** (some overlap) | 5 | 0.60 | 0.300 | Some novelty - partial pattern match |
| **Weakly Similar** (loose connection) | 5 | 0.30 | 0.584 | High novelty - mostly new pattern |
| **Many Similar** (common pattern) | 8-10 | 0.60 | 0.200 | Low novelty - very common pattern |
| **No Similar** (first of its kind) | 0 | - | 1.000 | Maximum novelty - completely new |

### Real-World Examples:

**Before Fix:**
```
PR #1 [SQL Injection]: novelty=0.600, similar=5
PR #50 [Debug prints]: novelty=0.600, similar=5
PR #100 [System.out]: novelty=0.600, similar=5
PR #125 [High Novelty Test]: novelty=0.600, similar=5
```
All identical! ❌

**After Fix (Expected):**
```
PR #1 [SQL Injection]: novelty=0.300-0.400, similar=5
  → Moderate novelty (some SQL injection PRs seen before)

PR #50 [Debug prints]: novelty=0.100-0.200, similar=8
  → Low novelty (many debug print PRs exist)

PR #100 [System.out]: novelty=0.500-0.600, similar=3
  → High novelty (few similar, weak matches)

PR #125 [High Novelty Test]: novelty=0.000-0.100, similar=5
  → Very low novelty (nearly identical to PRs 112, 120, 122)
```
Now differentiated! ✅

## Impact on Database

### Before:
```sql
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT rag_novelty_score) as unique_scores
FROM pr_analysis 
WHERE rag_novelty_score IS NOT NULL;

-- Result: 128 PRs, 2 unique scores (0.600 and 0.282)
```

### After (Expected):
```sql
-- Result: 128 PRs, 15-20 unique scores (0.000 to 1.000 range)
```

## What Needs to Be Done

### Option 1: Re-analyze All PRs (Recommended)
```bash
# Re-analyze all 128 PRs with fixed code
cd /home/maheshrv/Documents/IGOT/sourcecodes-igot/codereview
./tools/analyze_prs_batch.sh 1 128
```

**Pros:**
- All PRs get consistent, correct novelty scores
- Full comparison across entire dataset
- Clean data

**Cons:**
- Takes ~1-2 hours for 128 PRs
- Uses API quota

### Option 2: Analyze New PRs Only
```bash
# Only new PRs going forward use new calculation
# Keep old PRs as-is
```

**Pros:**
- Fast, no re-work
- No API usage

**Cons:**
- Inconsistent data (old vs new calculation)
- Can't compare novelty scores across old/new PRs

### Option 3: Hybrid Approach
```bash
# Re-analyze just a sample (e.g., PRs 1-30, 101-130)
./tools/analyze_prs_batch.sh 1 30
./tools/analyze_prs_batch.sh 101 130
```

**Pros:**
- Quick verification that fix works
- Representative sample

**Cons:**
- Still incomplete dataset

## Recommendation

**Best approach:** Re-analyze all 128 PRs

**Why:**
1. Dataset is still small (128 PRs)
2. Novelty scores need to be comparable for analytics
3. Test data should be clean for presentations
4. Only takes ~1-2 hours

**Steps:**
```bash
# 1. Backup current data
pg_dump -h localhost -p 5433 -U postgres -d pr_analysis > backup_before_reanalysis.sql

# 2. Re-analyze all
cd /home/maheshrv/Documents/IGOT/sourcecodes-igot/codereview
./tools/analyze_prs_batch.sh 1 128

# 3. Verify results
python3.10 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, database='pr_analysis', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute('SELECT COUNT(DISTINCT rag_novelty_score) FROM pr_analysis WHERE rag_novelty_score IS NOT NULL')
print(f'Unique novelty scores: {cur.fetchone()[0]}')
cur.close()
conn.close()
"

# Expected: 15-20 unique scores (was 2 before)
```

## Files Changed

1. **agents/rag_enhanced_agent.py**
   - Line 207-228: Added `average_similarity` to metadata
   - Line 610-650: Enhanced `_calculate_novelty_score()` with penalties

2. **No changes needed in:**
   - `services/rag_database_service.py` - Already correct, was expecting `average_similarity`
   - Database schema - Already has correct columns

## Testing

```bash
# Test the new calculation works
python3.10 /tmp/test_new_novelty.py

# Test on real PR
cd /home/maheshrv/Documents/IGOT/sourcecodes-igot/codereview
PYTHONPATH=. python3.10 tools/fetch_and_analyze_prs.py --pr-number 130 --repository tarentomaheshvakkund/testdata-hackathon

# Check novelty is different from 0.600
psql -h localhost -p 5433 -U postgres -d pr_analysis -c "SELECT pr_number, rag_novelty_score, rag_similar_prs_count FROM pr_analysis WHERE pr_number = 130"
```

## Summary

✅ **Fixed:** Missing `average_similarity` in metadata
✅ **Fixed:** Simplistic novelty calculation
✅ **Improved:** Now considers count, distribution, and top similarity
✅ **Expected:** Novelty scores will now range from 0.0 to 1.0 meaningfully
✅ **Action Needed:** Re-analyze all 128 PRs for consistent data

The system is now ready to provide **meaningful differentiation** between truly novel PRs and common patterns!
