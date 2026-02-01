import os
import google.generativeai as genai
from app.utils.rate_limiter import rate_limited

class GenerationService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_KEY"))
        self.model = genai.GenerativeModel('gemini-flash-latest')

    @rate_limited
    def generate_code(self, intent, repo_context, file_path=None):
        """
        Generate code based on user intent and repository context.
        """
        prompt = f"""You are an expert software engineer. Generate production-ready code based on the following:

**User Intent**: {intent}

**Repository Context**:
{repo_context}

**Target File**: {file_path or 'Determine appropriate file based on intent'}

**Instructions**:
1. Generate clean, well-documented code
2. Follow best practices for the language
3. Include type hints/annotations where applicable
4. Add docstrings/comments
5. Return ONLY the code, no explanations

**Output Format**:
```
<code here>
```
"""
        
        try:
            response = self.model.generate_content(prompt)
            code = response.text
            
            # Extract code from markdown if present
            if "```" in code:
                # Find the code block
                start = code.find("```")
                end = code.rfind("```")
                if start != -1 and end != -1 and start < end:
                    code_block = code[start:end]
                    # Remove language identifier
                    lines = code_block.split('\n')
                    code = '\n'.join(lines[1:])  # Skip first line with ```language
            
            return code.strip()
        except Exception as e:
            print(f"Code generation error: {e}")
            return None

    @rate_limited
    def generate_tests(self, code, file_path, intent):
        """
        Generate tests for the given code.
        """
        prompt = f"""You are an expert test engineer. Generate comprehensive tests for the following code:

**Code**:
```
{code}
```

**File Path**: {file_path}
**Intent**: {intent}

**Instructions**:
1. Generate pytest-compatible tests
2. Cover edge cases and happy paths
3. Use descriptive test names
4. Include fixtures if needed
5. Return ONLY the test code, no explanations

**Output Format**:
```python
<test code here>
```
"""
        
        try:
            response = self.model.generate_content(prompt)
            test_code = response.text
            
            # Extract code from markdown if present
            if "```" in test_code:
                start = test_code.find("```")
                end = test_code.rfind("```")
                if start != -1 and end != -1 and start < end:
                    code_block = test_code[start:end]
                    lines = code_block.split('\n')
                    test_code = '\n'.join(lines[1:])
            
            return test_code.strip()
        except Exception as e:
            print(f"Test generation error: {e}")
            return None

    @rate_limited
    def determine_file_path(self, intent, repo_context):
        """
        Use Gemini to determine the appropriate file path for the code.
        """
        prompt = f"""Based on the following intent and repository structure, determine the best file path for the new code.

**Intent**: {intent}

**Repository Structure**:
{repo_context}

**Instructions**:
Return ONLY the file path (e.g., 'src/utils/helper.py' or 'components/Button.tsx').
If creating a new file, suggest an appropriate name and location.

**Output**: <file_path>
"""
        
        try:
            response = self.model.generate_content(prompt)
            file_path = response.text.strip()
            # Remove any markdown formatting
            file_path = file_path.replace('`', '').replace('**', '')
            return file_path
        except Exception as e:
            print(f"File path determination error: {e}")
            return None
