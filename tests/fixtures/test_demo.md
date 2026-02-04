
# Conversational Orchestration Demo Script

A demo script for validating prompt confirmation, execution, and output.

## Setup Section

### 💬 COPILOT CHAT PROMPT:
```
What is the current date and time?
```
### 🎯 Expected Outcome:
Should return the current date and time.

## Main Demo Section

### 💬 COPILOT CHAT PROMPT:
```
List files in the current directory
```
### 🎯 Expected Outcome:
Should return a list of files, including 'test_demo.md'.

### 💬 COPILOT CHAT PROMPT:
```
Show me information about file [FILENAME]
```
### 🎯 Expected Outcome:
Should return file details for the substituted filename.

## Completion Section

### 💬 COPILOT CHAT PROMPT:
```
What directory am I currently in?
```
### 🎯 Expected Outcome:
Should return the current working directory path.

---

**Demo Complete!** This simple test demonstrates:
- Loading and parsing a demo script
- Sequential prompt presentation
- Variable detection in prompts
- State management
