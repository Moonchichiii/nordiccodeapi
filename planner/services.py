import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_summaries(submission_data: dict) -> dict:
    """
    Given the submission data, generate:
      - client_summary: a client-friendly summary
      - developer_worksheet: a detailed technical specification and visual mockup description for developers.
    """
    # Build a detailed, structured prompt
    prompt = f"""
    You are an expert in web application planning and UI design.

    The following is a set of project requirements:
    -----------------------------------
    Project Overview:
    {submission_data.get("projectOverview")}
    
    Business Goals:
    {submission_data.get("businessGoals")}
    
    Functional Requirements:
    {submission_data.get("functionalRequirements")}
    
    Design Preferences:
    {submission_data.get("designPreferences")}
    
    Technical Context:
    {submission_data.get("technicalContext")}
    
    Website Content:
    {submission_data.get("websiteContent")}
    -----------------------------------

    Your tasks:
    1. Generate a concise, friendly summary for the client that highlights the key business goals and overall vision.
    2. Generate a detailed developer worksheet that includes technical specifications, architectural guidelines, and a description for a visual mockup of the website design.
    3. Output the response as valid JSON with two keys: "client_summary" and "developer_worksheet".

    The output must follow this JSON schema exactly:
    {{
      "client_summary": "<string>",
      "developer_worksheet": "<string>"
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are a helpful planning assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        output_text = response.choices[0].message.content.strip()
        # Here you can optionally add JSON parsing with error handling
        import json
        result = json.loads(output_text)
        return result
    except Exception as e:
        # Log error details in production
        raise e

