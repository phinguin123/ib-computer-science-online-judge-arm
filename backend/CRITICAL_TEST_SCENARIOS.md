# Critical Test Scenarios Documentation

## Overview

This document explains the critical test scenarios covered in `critical_scenarios_test.py`. Each scenario represents a potential failure point that could break the system or compromise security.

## How to Run the Tests

```bash
cd backend
python manage.py test critical_scenarios_test
```

Or run specific test classes:
```bash
python manage.py test critical_scenarios_test.AccountCriticalScenariosTest
python manage.py test critical_scenarios_test.SubmissionCriticalScenariosTest
python manage.py test critical_scenarios_test.ProblemCriticalScenariosTest
python manage.py test critical_scenarios_test.ContestCriticalScenariosTest
```

---

## Account Module Critical Scenarios

### 1. Registration with Duplicate Username/Email
**Why Critical:** 
- Prevents account hijacking attempts
- Ensures data integrity in the user database
- Case-insensitive matching prevents bypassing uniqueness constraints

**What Could Break:**
- Multiple users with same credentials
- Password reset emails going to wrong users
- Authentication confusion

### 2. Login with Disabled Account
**Why Critical:**
- Disabled accounts should be completely blocked
- Security measure to prevent banned users from accessing the system
- Must be enforced at authentication level

**What Could Break:**
- Banned users can still access the system
- Security policies are bypassed

### 3. 2FA Validation Failures
**Why Critical:**
- Two-factor authentication is a critical security layer
- Invalid codes should be rejected
- Missing codes should trigger 2FA requirement

**What Could Break:**
- Security bypass if 2FA is not properly enforced
- Brute force attacks on 2FA codes

### 4. Password Reset Token Expiration
**Why Critical:**
- Expired tokens should not be usable
- Prevents token reuse attacks
- Time-limited security tokens must expire

**What Could Break:**
- Old tokens could be used indefinitely
- Security vulnerability if tokens don't expire

### 5. Email Change with Duplicate Email
**Why Critical:**
- Email uniqueness is critical for password reset
- Prevents email hijacking
- Data integrity requirement

**What Could Break:**
- Password reset emails going to wrong accounts
- Email-based account recovery broken

### 6. Avatar Upload Validation
**Why Critical:**
- Prevents DoS attacks through large file uploads
- Prevents security issues from malicious file types
- Storage abuse prevention

**What Could Break:**
- Server storage exhaustion
- Security vulnerabilities from malicious files
- System performance degradation

### 7. Registration When Disabled
**Why Critical:**
- Admins need control over system access
- Prevents unauthorized account creation
- System maintenance capability

**What Could Break:**
- Admins lose control over user registration
- System cannot be locked down when needed

### 8. Password Change Without 2FA
**Why Critical:**
- Sensitive operations should require 2FA when enabled
- Prevents unauthorized password changes
- Security best practice

**What Could Break:**
- 2FA can be bypassed for sensitive operations
- Security policy not enforced

### 9. Reset Password When Already Logged In
**Why Critical:**
- Prevents token hijacking attacks
- Logged-in users shouldn't need password reset
- Security best practice

**What Could Break:**
- Token hijacking vulnerability
- Unnecessary password reset flows

---

## Submission Module Critical Scenarios

### 1. Submission to Non-Existent Problem
**Why Critical:**
- Prevents invalid submissions from being created
- Prevents data corruption
- System integrity

**What Could Break:**
- Orphaned submissions
- Database integrity issues
- Judging system errors

### 2. Submission with Disallowed Language
**Why Critical:**
- Problem-specific language restrictions must be enforced
- Prevents invalid submissions
- Problem configuration integrity

**What Could Break:**
- Submissions in wrong languages are judged
- Problem configuration ignored
- User confusion

### 3. Submission to Invisible Problem
**Why Critical:**
- Hidden problems should not accept submissions
- Problem visibility control
- System integrity

**What Could Break:**
- Hidden problems can be solved
- Visibility settings ignored
- Unfair advantage

### 4. Submission During Ended Contest
**Why Critical:**
- Contest integrity - no submissions after contest ends
- Fair competition requirement
- Contest rules enforcement

**What Could Break:**
- Users can submit after contest ends
- Contest results invalidated
- Unfair competition

### 5. Submission Permission Checks
**Why Critical:**
- Privacy and security
- Users should only see allowed submissions
- Contest rules enforcement

**What Could Break:**
- Private submissions leaked
- Cheating during contests
- Privacy violations

### 6. Share Submission During Active Contest
**Why Critical:**
- Prevents cheating during contests
- Contest integrity
- Fair competition

**What Could Break:**
- Users can share solutions during contest
- Cheating enabled
- Contest fairness compromised

---

## Problem Module Critical Scenarios

### 1. Duplicate Display ID
**Why Critical:**
- Display IDs are user-facing identifiers
- Must be unique for proper problem identification
- User experience depends on unique IDs

**What Could Break:**
- Users confused by duplicate IDs
- Problem lookup failures
- System integrity issues

### 2. Invalid Test Case Scores (Negative/Zero for OI)
**Why Critical:**
- Scoring system integrity
- OI problems require valid scoring
- Prevents scoring system corruption

**What Could Break:**
- Scoring system breaks
- Invalid scores awarded
- Competition fairness compromised

### 3. SPJ Validation
**Why Critical:**
- Special judge code must be valid
- Uncompiled SPJ code breaks judging
- System reliability

**What Could Break:**
- Judging system crashes
- Submissions judged incorrectly
- System reliability issues

### 4. Problem Permission Checks
**Why Critical:**
- Users should only manage allowed problems
- Permission system integrity
- Security requirement

**What Could Break:**
- Unauthorized problem modification
- Permission system bypassed
- Security vulnerability

### 5. Problem Deletion by Non-Owner
**Why Critical:**
- Prevents unauthorized problem deletion
- Data integrity
- Security requirement

**What Could Break:**
- Problems deleted by unauthorized users
- Data loss
- System integrity compromised

### 6. Problem Update with Duplicate Display ID
**Why Critical:**
- Display ID uniqueness must be maintained
- Update operations must validate uniqueness
- Data integrity

**What Could Break:**
- Duplicate IDs after updates
- Problem identification confusion
- System integrity issues

---

## Contest Module Critical Scenarios

### 1. Contest with Invalid Time Range (end_time <= start_time)
**Why Critical:**
- Contests must have valid duration
- Scheduling system depends on valid times
- System logic breaks with invalid times

**What Could Break:**
- Contest scheduling breaks
- Status calculation errors
- System logic failures

### 2. Invalid CIDR IP Ranges
**Why Critical:**
- IP filtering depends on valid CIDR notation
- Invalid ranges cause errors
- Security feature must work correctly

**What Could Break:**
- IP filtering breaks
- System errors from invalid IP ranges
- Security feature disabled

### 3. Contest Status Checks
**Why Critical:**
- Contest state determines allowed actions
- Status must be calculated correctly
- System behavior depends on status

**What Could Break:**
- Wrong actions allowed/blocked
- Contest logic breaks
- User experience issues

### 4. Contest Problem Rule Type Mismatch
**Why Critical:**
- Contest and problem rule types must match
- Scoring depends on consistent rule types
- System integrity

**What Could Break:**
- Scoring system breaks
- Contest results invalid
- System logic errors

### 5. Contest Permission Checks
**Why Critical:**
- Only contest admins should manage contests
- Security requirement
- System integrity

**What Could Break:**
- Unauthorized contest modification
- Security vulnerability
- System integrity compromised

---

## Test Coverage Summary

- **Account Module:** 13 critical scenarios
- **Submission Module:** 8 critical scenarios  
- **Problem Module:** 8 critical scenarios
- **Contest Module:** 7 critical scenarios

**Total: 36 critical test scenarios**

---

## Best Practices for Adding New Tests

1. **Focus on Edge Cases:** Test boundary conditions and invalid inputs
2. **Security First:** Always test security-related scenarios
3. **Data Integrity:** Test scenarios that could corrupt data
4. **User Experience:** Test scenarios that would confuse users
5. **System Reliability:** Test scenarios that could crash the system

## Maintenance

These tests should be run:
- Before every deployment
- After major code changes
- As part of CI/CD pipeline
- When fixing bugs (add regression tests)

---

## Notes

- All tests use the `APITestCase` base class from `utils.api.tests`
- Tests mock external dependencies (like `judge_task.send`) when appropriate
- Tests use helper methods for creating test data
- Each test includes a docstring explaining why it's critical


