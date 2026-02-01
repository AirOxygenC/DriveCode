import google.generativeai as genai
import os
import json

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_KEY"))
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def analyze_intent(self, text, repo_context=None):
        """
        Analyze what the user wants to do.
        Returns a concise description or structured plan.
        """
        prompt = f"""
        You are an expert AI coding assistant.
        User Request: "{text}"
        
        Context: {repo_context if repo_context else "No repository context provided."}
        
        Task: Identify the user's intent. Is it a question, a code generation request, or a modification?
        Return a concise summary of the intent (max 1 sentence) starting with "Action:".
        """
        
        response = self.model.generate_content(prompt)
        return response.text.strip()
        
    def generate_code(self, prompt, context):
        """
        Generate code based on the prompt.
        """
        full_prompt = f"""
        Role: Senior Software Engineer.
        Context: {context}
        Task: {prompt}
        
        Output: valid code only.
        """
        response = self.model.generate_content(full_prompt)
        return response.text
