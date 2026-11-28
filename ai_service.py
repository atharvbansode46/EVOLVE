
import os
import json
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Get Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API Key not found!")

# Initialize Gemini Client
client = genai.Client(api_key=api_key)


# Generate normal AI response
def generate_ai_response(prompt):

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text


# Generate personalized learning roadmap
def generate_learning_roadmap(skill_name, current_level, target_level, motivation):

    prompt = f"""
    You are EVOLVE's expert AI Learning Architect.

    Create a personalized learning roadmap using these details:

    Skill: {skill_name}
    Current Level: {current_level}
    Target Level: {target_level}
    Motivation: {motivation}

    Requirements:
    1. Create 5 progressive learning levels.
    2. Each level must contain 3-5 practical tasks.
    3. Include real-world projects.
    4. Start according to the user's current knowledge.
    5. Avoid repeating concepts the user already knows.

    Return the roadmap in JSON format:

    {{
        "skill": "{skill_name}",
        "levels": [
            {{
                "level": 1,
                "title": "Level Title",
                "tasks": [
                    {{
                        "title": "Task Title",
                        "description": "Task Description"
                    }}
                ]
            }}
        ]
    }}

    Return only valid JSON. No markdown.
    """

    response = generate_ai_response(prompt)

    try:
        roadmap = json.loads(response)
        return roadmap

    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON. Please try again.")
