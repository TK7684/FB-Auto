# 🔍 Security Audit Report
## D Plus Skin Facebook AI Bot
**Agent:** Gamma (The Auditor)  
**Date:** 2026-02-11  
**Status:** REQUEST CHANGES

---

## Executive Summary

Agent Beta has implemented significant improvements to the D Plus Skin Facebook Bot including:
- Comprehensive error handling with Facebook error taxonomy
- Circuit breaker pattern for cascade failure prevention  
- Thai language enhancement with few-shot prompting
- Response quality validation

**Overall Assessment:** The code is well-structured and follows good practices, but **3 critical security issues** must be addressed before deployment.

---

## Audit Results

| Category | Status | Issues |
|----------|--------|--------|
| No Hardcoded Secrets | ✅ PASS | 0 issues |
| SQL/XSS Injection | ✅ PASS | 0 issues |
| Rate Limits (85% safety) | ⚠️ WARNING | Needs verification |
| Circuit Breaker | ✅ PASS | Properly implemented |
| Token Expiration | ⚠️ WARNING | 1 issue |
| Thai Text Encoding | ✅ PASS | Properly handled |
| Async/Await Patterns | ⚠️ WARNING | 1 issue |
| Input Validation | ✅ PASS | Good coverage |
| Error Handling | ✅ PASS | Comprehensive |

---

## Critical Issues (Must Fix Before Deployment)

### 🔴 CRITICAL-1: Race Condition in Circuit Breaker
**File:** `services/circuit_breaker.py`  
**Line:** 103, 167, 172, 177

**Issue:** The `_on_success()` and `_on_failure()` methods modify shared state (`_failure_count`, `_success_count`, `_half_open_calls`) **after** releasing the lock, creating a race condition:

```python
# Line 103-107 (PROBLEMATIC)
with self._lock:
    # Check state...
    if self._state == CircuitState.OPEN:
        if self._should_attempt_reset():
            self._transition_to_half_open()  # Inside lock ✓
        else:
            # ... raise error

# Execute OUTSIDE lock - race condition starts here
result = await func(*args, **kwargs)  # Line 117
self._on_success()  # Line 120 - state modified OUTSIDE lock ✗
```

**Impact:** Under high concurrency, multiple threads can:
1. Increment `_half_open_calls` beyond limit
2. Miscount successes/failures 
3. Cause premature circuit state transitions

**Fix Instructions:**
```python
# BEFORE (line 117-122):
result = await func(*args, **kwargs)
self._on_success()  # Race condition!
return result

# AFTER:
result = await func(*args, **kwargs)
with self._lock:  # Re-acquire lock before state changes
    self._on_success()
return result

# ALSO FIX _on_failure() pattern (lines 124-127)
```

---

### 🔴 CRITICAL-2: Async vs Sync Mismatch in Gemini Embeddings
**File:** `services/gemini_service.py`  
**Line:** 531-565

**Issue:** The `_get_embeddings_openrouter_sync()` method uses **synchronous** `httpx.Client()` inside a method that can be called from **async** contexts:

```python
def _get_embeddings_openrouter_sync(self, text):  # Not async!
    # ...
    with httpx.Client(timeout=15.0) as client:  # Blocking! ✗
        response = client.post(...)
```

This method is called from `get_embeddings()` which is also sync, but can block the event loop when used in async contexts.

**Impact:** Can cause event loop blocking, degrading bot responsiveness under load.

**Fix Instructions:**
```python
# OPTION 1: Make method async
async def _get_embeddings_openrouter_async(self, text):
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(...)
        
# OPTION 2: Run sync method in thread pool
def get_embeddings(self, text, ...):
    if self.openrouter_key:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # Run sync method in executor to avoid blocking
            result = await loop.run_in_executor(
                None, 
                self._get_embeddings_openrouter_sync, 
                text
            )
        except RuntimeError:
            # No running loop, safe to call directly
            result = self._get_embeddings_openrouter_sync(text)
```

---

### 🔴 CRITICAL-3: Token Validation Exposes Secrets in Logs
**File:** `services/facebook/token_manager.py`  
**Line:** 143

**Issue:** The `inspect_token()` method returns raw token data including potentially sensitive information. While not directly logged, the return value could be accidentally logged by callers.

```python
async def inspect_token(self) -> Dict[str, Any]:
    # Returns raw Facebook API response including token scopes, issued_at, etc.
    # If caller logs this: logger.info(f"Token info: {await inspect_token()}")
    # Secrets could leak to logs
```

**Impact:** Potential credential exposure in logs if caller logs the return value.

**Fix Instructions:**
```python
async def inspect_token(self) -> Dict[str, Any]:
    """Inspect token details using Facebook's debug endpoint."""
    url = f"{self.base_url}/debug_token"
    params = {
        "input_token": self._token_info.token,
        "access_token": f"{self.app_id}|{self.app_secret}"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # SANITIZE: Remove sensitive fields before returning
        if "data" in data:
            data["data"].pop("access_token", None)
            data["data"].pop("input_token", None)
        
        return data
```

---

## Warnings (Should Address)

### ⚠️ WARNING-1: Rate Limit Safety Margin Not Explicitly Verified
**File:** `services/enhanced_rate_limiter.py`, `config/constants.py`

**Observation:** The constants show 85% safety margins in settings, but the actual file-based rate limiter in `services/rate_limiter.py` (referenced from original codebase) uses:
```python
MAX_COMMENTS_PER_HOUR = 60  # Safe limit for human-like behavior
```

This is not explicitly tied to the 85% of Facebook's documented limits.

**Recommendation:** Add a comment or constant explicitly showing the 85% calculation:
```python
# Facebook limit: 200 calls/hour for page-level
# Safety margin: 85% → 170 calls/hour
# Further reduced for human-like behavior: 60 calls/hour
MAX_COMMENTS_PER_HOUR = 60
```

---

### ⚠️ WARNING-2: Token Refresh Not Fully Automated
**File:** `services/facebook/token_manager.py`  
**Line:** 181-184

**Observation:** The code acknowledges that Page Access Tokens cannot be automatically refreshed:
```python
if self.is_near_expiration():
    logger.warning("Token is near expiration!")
    # Note: Page access tokens typically can't be refreshed automatically
    # without a long-lived user token. Log for manual intervention.
```

**Recommendation:** 
1. Add alerting mechanism when token is near expiration
2. Document manual refresh procedure
3. Consider implementing user token exchange flow for automatic refresh

---

### ⚠️ WARNING-3: Error Handler Suppresses All Exceptions
**File:** `services/facebook/error_handler.py`  
**Line:** 211-226

**Observation:** The `@with_error_handler` decorator suppresses exceptions and returns `False`:
```python
except Exception as e:
    context = {"operation": operation_name, ...}
    action = await handler.handle(e, context)
    
    if action.action == ActionType.RETRY:
        raise  # Only re-raises for retry
    elif action.action == ActionType.FAIL:
        raise FacebookAPIError(action.safe_message)
    elif action.action == ActionType.REAUTH:
        raise AuthenticationError(action.safe_message)
    else:
        # Other actions - log and return failure
        logger.error(f"Error in {operation_name}: {action.safe_message}")
        return False  # Silent failure!
```

**Impact:** Callers may not realize an error occurred since `False` is returned instead of raising an exception.

**Recommendation:** Document this behavior clearly or make silent failure opt-in:
```python
def with_error_handler(operation_name: str, silent_fail: bool = False):
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # ...
            else:
                if silent_fail:
                    logger.error(...)
                    return False
                else:
                    raise FacebookAPIError(action.safe_message)
        return wrapper
    return decorator
```

---

### ⚠️ WARNING-4: Quality Validator Uses Simple Keyword Matching
**File:** `services/prompts/quality_validator.py`  
**Line:** 298-312

**Observation:** The `_check_question_answered()` method uses simple keyword overlap which may not accurately determine if a question was answered:
```python
def _check_question_answered(self, response: str, original_question: str):
    # Simple check: does response address question keywords?
    # This is a basic heuristic - can be improved with semantic matching
```

**Recommendation:** Consider using sentence embeddings for semantic similarity checking in future iterations.

---

## Suggestions (Improvements)

### 💡 SUGGESTION-1: Add Request ID for Tracing
Add unique request IDs to all operations for better debugging:
```python
import uuid

async def handle_webhook_payload(payload: Dict[str, Any], request_id: str = None):
    request_id = request_id or str(uuid.uuid4())[:8]
    logger.bind(request_id=request_id).info("Processing webhook...")
```

### 💡 SUGGESTION-2: Circuit Breaker Persistence
Consider persisting circuit breaker state to survive restarts:
```python
# In CircuitBreaker.__init__
self._state = self._load_persisted_state() or CircuitState.CLOSED
```

### 💡 SUGGESTION-3: Add Metrics Collection
Add Prometheus metrics for monitoring:
```python
from prometheus_client import Counter, Histogram

circuit_transitions = Counter('circuit_breaker_transitions_total', ...)
api_latency = Histogram('facebook_api_latency_seconds', ...)
```

### 💡 SUGGESTION-4: Response Caching
Cache validated responses for common questions to reduce API calls:
```python
@lru_cache(maxsize=100)
def get_cached_response(question_hash: str) -> str:
    return cache.get(question_hash)
```

---

## Positive Findings

### ✅ Security Strengths

1. **No Hardcoded Secrets**: All API keys, tokens loaded from environment/settings
2. **No SQL Injection Risk**: No database queries using string interpolation
3. **Input Validation**: Comprehensive validation in `ResponseValidator`
4. **Safe Error Messages**: Thai error messages don't leak internal details
5. **XSS Prevention**: No user input rendered as HTML
6. **Proper Async Patterns**: Most methods correctly use `async/await`
7. **Good Error Classification**: 18 Facebook error codes properly mapped
8. **Circuit Breaker Pattern**: Properly prevents cascade failures
9. **Thai Text Encoding**: UTF-8 encoding explicitly set on all file operations
10. **Forbidden Words Filter**: Prevents medical claims and inappropriate content

---

## Facebook API Compliance

| Requirement | Status | Notes |
|-------------|--------|-------|
| Rate Limit Handling | ✅ | Proper handling of X-App-Usage headers |
| Token Expiration | ✅ | Proactive validation with debug endpoint |
| Error Code Mapping | ✅ | 18 error codes mapped |
| Retry Logic | ✅ | Exponential backoff for rate limits |
| App Secret Proof | ✅ | HMAC verification for API calls |
| Thai Language | ✅ | UTF-8 encoding throughout |

---

## Deployment Checklist (After Fixes)

- [ ] Fix circuit breaker race condition (CRITICAL-1)
- [ ] Fix async/sync mismatch in embeddings (CRITICAL-2)  
- [ ] Add token data sanitization (CRITICAL-3)
- [ ] Run full test suite: `pytest tests/unit/ -v`
- [ ] Test circuit breaker under concurrent load
- [ ] Verify token expiration alerts work
- [ ] Review log output for any credential exposure
- [ ] Load test with 100+ concurrent requests
- [ ] A/B test Thai response quality
- [ ] Document manual token refresh procedure

---

## Conclusion

The implementation by Agent Beta is **well-architected and production-ready** after addressing the 3 critical issues:

1. **Race condition in circuit breaker** - Could cause incorrect behavior under load
2. **Async/sync mismatch** - Could block event loop  
3. **Token data exposure risk** - Could leak credentials to logs

All other findings are warnings or suggestions for improvement. The code follows best practices for:
- Error handling and classification
- Thai language support
- Facebook API integration
- Response quality validation

**Recommendation:** REQUEST CHANGES - Fix the 3 critical issues, then APPROVE for deployment.

---

**Audited by:** Agent Gamma (The Auditor)  
**Audit Scope:** 21 files, ~4,000 lines of code  
**Methodology:** Static code analysis, OWASP Top 10 review, Facebook API compliance check
