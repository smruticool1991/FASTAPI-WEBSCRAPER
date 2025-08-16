# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains an n8n workflow for website analysis and scraping that has been experiencing high server load issues. The main goal is to create a Python API alternative that provides similar functionality with better performance characteristics.

## Current Architecture

### n8n Workflow (code.txt)
The existing n8n workflow (`code.txt`) implements comprehensive website analysis functionality:

- **Input Processing**: Receives domains via webhook and splits them into batches for processing
- **Web Scraping**: Fetches website content using HTTP requests with proper headers and timeouts
- **Analysis Engine**: Extensive JavaScript-based analysis including:
  - Platform detection (WordPress, Shopify, Wix, etc.)
  - SEO analysis (title, meta descriptions, structured data)
  - Contact information extraction (emails, phone numbers, contact pages)
  - Social media link detection
  - Security header analysis
  - Performance and accessibility checks

- **Batch Processing**: Uses "Split In Batches" with batch size of 50 and wait periods to manage load
- **Rate Limiting**: Implements delays and limits to prevent overwhelming target servers
- **Data Flow**: Complex node connections handling different analysis paths based on content availability

### Key Components
1. **Webhook Input**: Entry point for domain lists
2. **HTTP Request Nodes**: Multiple fetch operations with different configurations
3. **Analysis Nodes**: Custom JavaScript code for content parsing and analysis
4. **Conditional Logic**: IF nodes to handle different analysis paths
5. **Response Merging**: Combines results from different analysis branches

## Performance Issues

The current n8n implementation has high server load due to:
- Heavy JavaScript processing in browser environment
- Complex workflow orchestration overhead
- Multiple HTTP request nodes with potential inefficient batching
- Large amounts of data being processed in memory simultaneously

## Migration Strategy

When creating the Python API alternative:

1. **Maintain Compatibility**: Preserve the same analysis features and output format
2. **Optimize Processing**: Use efficient Python libraries for web scraping and content analysis
3. **Implement Proper Rate Limiting**: Use connection pooling and async processing
4. **Reduce Memory Usage**: Process data in streams rather than loading everything in memory
5. **Add Caching**: Cache frequently accessed data to reduce redundant processing

## Key Analysis Features to Preserve

- Platform detection logic (WordPress, Shopify, Wix, Squarespace, etc.)
- Comprehensive email extraction with quality scoring and filtering
- Phone number validation and extraction
- Contact page URL detection with multiple strategies
- Social media link extraction for all major platforms
- SEO metrics calculation and scoring
- Security header analysis
- Content structure analysis (H1, H2, meta tags, etc.)

## Development Commands

Since this is an n8n workflow file, there are no traditional build/test commands. When developing the Python API:

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Run tests (when implemented)
pytest tests/

# Check code quality
flake8 src/
black src/
```