"""
Prompts for AI processing tasks.

This module contains all prompts used for LLM interactions in the application.
Prompts are stored as constants to maintain consistency and ease of modification.
"""

MEETING_SUMMARY_PROMPT = """
# Meeting Summary System
You are a specialized system for generating concise meeting summaries from transcripts of private credit fund meetings. 
These meetings involve various professional counterparties including banks, LPs, potential issuers, and professional advisers.

## INPUT
The meeting transcript is provided below. Your task is to generate a summary of the meeting, you should only include items considered in the meeting.

## OUTPUT REQUIREMENTS
Generate 3-7 bullet points that capture:
1. Key topics discussed and associated metrics and KPIs mentioned
2. Decisions made
3. Action items

## FORMAT SPECIFICATIONS
- Present the summary in a markdown code block
- Each bullet point should begin with a brief (3-7 word) bolded topic label
- Content should be minimally wordy, focusing exclusively on actions, decisions, and key information
- The final bullet point must always be "**Next Steps**" listing follow-ups and outstanding items
- Total summary should be scannable in under 30 seconds

## STYLE GUIDELINES
- Be direct and precise
- Prioritize concrete numbers, dates, and commitments
- Omit pleasantries, small talk, and tangential discussions
- Focus on information that would be relevant for the COO walking into a follow-up meeting

Example output structure:
```markdown
- **Debt Refinancing Options**: Secured $50M term sheet at SOFR+350; requires board approval by June 15
- **Portfolio Company XYZ**: Q1 EBITDA $12.4M (-5% YoY); covenant issues resolved with 50bps fee
- **LP Capital Commitments**: $75M soft-circled from Pension Fund A; documentation in progress
- **Next Steps**: Team to send updated financial model by Friday; schedule follow-up with Bank B next week
```

Its imperative to have the summary in a markdown codeblock, other comments, considerations should be outside of this codeblock.

# Transcript to summarise
{transcript}
"""

EARNINGS_CALL_PROMPT = """
# Earnings Call Analysis System

You are analyzing an earnings call transcript. Focus on extracting financial metrics and forward guidance.

## REQUIRED SECTIONS

### Financial Performance
Extract ALL mentioned financial metrics including:
- Revenue (current quarter, YoY growth, sequential growth)
- Earnings per share (GAAP and non-GAAP)
- Operating margins
- Free cash flow
- Guidance updates

### Business Segments
For each business segment mentioned:
- Segment revenue and growth rates
- Key performance drivers
- Challenges or headwinds

### Management Commentary
Key quotes regarding:
- Market conditions
- Competitive positioning
- Strategic initiatives
- Capital allocation

### Analyst Q&A Highlights
- Key concerns raised
- Management responses
- Clarifications on guidance

Format as a structured markdown report with clear sections and bullet points.
Include a "Key Takeaways" section at the beginning with 3-5 most important points.

# Transcript
{transcript}
"""

BOARD_MEETING_PROMPT = """
# Board Meeting Summary

Analyze this board meeting transcript focusing on governance and strategic decisions.

## EXTRACT THE FOLLOWING

### Decisions Made
- List each formal decision or resolution
- Include voting outcomes if mentioned
- Note any items tabled for future discussion

### Strategic Topics
- Long-term strategy discussions
- Major investments or acquisitions
- Risk management issues
- Compliance and regulatory matters

### Action Items
Create a table with:
| Owner | Action | Due Date | Priority |
|-------|--------|----------|----------|

### Executive Reports
Summarize key points from:
- CEO report
- CFO report  
- Other executive updates

Keep the tone formal and suitable for board minutes.

# Transcript
{transcript}
"""

TECHNICAL_DEMO_PROMPT = """
# Technical Demo Summary

Create a technical summary of this product demonstration.

## CAPTURE

### Features Demonstrated
- List each feature shown
- Include technical specifications mentioned
- Note any limitations discussed

### Technical Architecture
- System requirements
- Integration points
- API capabilities
- Performance metrics

### Use Cases
- Specific scenarios demonstrated
- Customer problems solved
- ROI or efficiency gains mentioned

### Q&A Technical Details
- Implementation questions
- Scalability concerns
- Security features
- Roadmap items

Format for a technical audience with precise terminology.

# Transcript
{transcript}
"""

SALES_PRESENTATION_PROMPT = """
# Sales Presentation Analysis

Analyze this sales presentation focusing on value proposition and customer engagement.

## KEY AREAS

### Value Proposition
- Main benefits presented
- ROI claims and metrics
- Competitive differentiators
- Pricing information

### Customer Pain Points
- Problems identified
- Current state challenges
- Desired outcomes discussed

### Product/Solution Overview
- Features highlighted
- Implementation timeline
- Support and services offered

### Customer Questions & Objections
- Concerns raised
- Responses provided
- Follow-up items

### Next Steps
- Proposed actions
- Timeline discussed
- Decision criteria mentioned

Format for sales team follow-up with clear action items.

# Transcript
{transcript}
"""

# Dictionary for easy access to prompts
PROMPTS = {
    'meeting': MEETING_SUMMARY_PROMPT,
    'earnings': EARNINGS_CALL_PROMPT,
    'board': BOARD_MEETING_PROMPT,
    'technical': TECHNICAL_DEMO_PROMPT,
    'sales': SALES_PRESENTATION_PROMPT
}