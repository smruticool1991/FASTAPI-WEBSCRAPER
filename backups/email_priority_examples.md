# 📧 Email Priority Feature Guide

The Website Analysis API now supports custom email priority to help you get the most relevant emails first.

## 🎯 How Email Priority Works

The `email_priority` parameter is an array that defines which email patterns should be prioritized. The API will score emails based on this priority list, with earlier patterns getting higher scores.

### Priority Pattern Types

1. **Username patterns**: `"info@"`, `"sales@"`, `"contact@"`
   - Matches emails starting with the specified username
   - Example: `"info@"` matches `info@company.com`, `info.support@business.org`

2. **Domain patterns**: `"@gmail.com"`, `"@yahoo.com"`, `"@company.com"`
   - Matches emails from specific domains
   - Example: `"@gmail.com"` matches `john@gmail.com`, `contact@gmail.com`

3. **Contains patterns**: `"support"`, `"business"`
   - Matches emails containing the specified text anywhere
   - Example: `"support"` matches `support@company.com`, `help.support@business.org`

## 📝 Request Examples

### Example 1: Default Priority
```json
{
  "domains": ["example.com"],
  "email_priority": ["info@", "sales@", "@gmail.com"]
}
```
**Priority order:**
1. `info@` emails (highest priority)
2. `sales@` emails 
3. `@gmail.com` emails (lowest priority)

### Example 2: Contact-Focused Priority
```json
{
  "domains": ["company.com"],
  "email_priority": ["contact@", "support@", "help@"]
}
```
**Result:** Contact and support emails will be ranked higher than generic business emails.

### Example 3: Personal Email Priority
```json
{
  "domains": ["website.org"],
  "email_priority": ["@gmail.com", "@yahoo.com", "@hotmail.com"]
}
```
**Result:** Personal email providers will be prioritized over business domains.

### Example 4: Business Domain Priority
```json
{
  "domains": ["startup.io"],
  "email_priority": ["@company.com", "ceo@", "founder@"]
}
```
**Result:** Company emails and executive emails will be ranked highest.

## 🚀 API Usage

### Standard Analysis
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["example.com", "business.org"],
    "email_priority": ["sales@", "info@", "@gmail.com"],
    "batch_size": 10,
    "timeout": 15
  }'
```

### Background Job Processing
```bash
curl -X POST "http://localhost:8000/jobs/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["company1.com", "company2.com", "company3.com"],
    "email_priority": ["contact@", "support@", "@business.com"],
    "batch_size": 20,
    "priority": 2
  }'
```

## 📊 Scoring System

The email priority system works by adding bonus points to emails that match your priority patterns:

- **1st priority pattern**: +100 points
- **2nd priority pattern**: +90 points  
- **3rd priority pattern**: +80 points
- **4th priority pattern**: +70 points
- (and so on...)

### Example Scoring
Given priority: `["info@", "sales@", "@gmail.com"]`

| Email | Base Score | Priority Bonus | Final Score |
|-------|------------|----------------|-------------|
| `info@company.com` | 100 | +100 (1st priority) | 200 |
| `sales@business.org` | 100 | +90 (2nd priority) | 190 |
| `john@gmail.com` | 100 | +80 (3rd priority) | 180 |
| `support@company.com` | 100 | +0 (no match) | 100 |

## ⚙️ Default Configuration

If no `email_priority` is specified, the default priority is:
```json
["info@", "sales@", "@gmail.com"]
```

This default configuration prioritizes:
1. Info emails (most common business contact)
2. Sales emails (business inquiries)
3. Gmail addresses (personal/accessible emails)

## 💡 Best Practices

### For B2B Lead Generation
```json
["sales@", "business@", "info@", "contact@"]
```

### For Customer Support
```json
["support@", "help@", "service@", "contact@"]
```

### For Personal Outreach
```json
["@gmail.com", "@yahoo.com", "@hotmail.com", "ceo@"]
```

### For Executive Contact
```json
["ceo@", "founder@", "president@", "director@"]
```

### For Technical Contact
```json
["tech@", "dev@", "engineering@", "admin@"]
```

## 🎯 Response Format

The API returns emails sorted by their priority score:

```json
{
  "domain": "example.com",
  "emails": [
    "info@example.com",     // Highest priority
    "sales@example.com",    // Second priority  
    "john@gmail.com",       // Third priority
    "support@example.com",  // Lower priority
    "admin@example.com"     // Lowest priority
  ],
  "emailCount": 5,
  // ... other fields
}
```

## 🔧 Advanced Usage

### Multiple Domain Types
```json
{
  "domains": ["startup.com", "enterprise.org", "personal.net"],
  "email_priority": [
    "@startup.com",    // Company-specific domains first
    "founder@",        // Executive emails
    "@gmail.com",      // Personal emails
    "info@"           // Generic business emails
  ]
}
```

### Industry-Specific Priorities
```json
{
  "domains": ["tech-company.com"],
  "email_priority": [
    "engineering@",
    "tech@", 
    "dev@",
    "cto@",
    "@company.com"
  ]
}
```

This feature gives you fine-grained control over email discovery and helps you find the most relevant contacts for your specific use case! 🎯