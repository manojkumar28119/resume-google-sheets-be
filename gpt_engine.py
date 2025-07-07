from openai import OpenAI
import os
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gpt_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load OpenAI API key from .env file
logger.info("Loading environment variables...")
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OpenAI API key is required")

logger.info("Initializing OpenAI client...")
client = OpenAI(api_key=api_key)
logger.info("OpenAI client initialized successfully")

def build_json_prompt(user_data: dict) -> str:
    """Builds the GPT prompt to generate JSON resume output."""
    logger.info("Building JSON prompt for user data")
    logger.debug(f"User data keys: {list(user_data.keys())}")
    
    prompt = f"""
You are an expert AI-powered resume writer. Your task is to take the user's raw input and generate a highly polished, professional, ATS-friendly resume. Use action verbs, measurable impact (if available), and clear formatting.

Respond ONLY in this structured JSON format:
{{
  "full_name": "",
  "email": "",
  "phone": "",
  "linkedin": "",
  "github": "",
  "career_objective": "",
  "education": "",
  "skills": [
    "Skill 1",
    "Skill 2",
    "Skill 3",
    "Skill 4",
    "Skill 5"
  ],
  "projects": [
    {{
      "title": "",
      "technologies": "",
      "description": ""
    }},
    {{
      "title": "",
      "technologies": "",
      "description": ""
    }}
  ],
  "experience": [
    "Point 1",
    "Point 2",
    "Point 3",
    "Point 4"
  ],
  "certifications": [
    {{
      "title": "",
      "provider": "",
      "date": ""
    }}
  ]
}}

Instructions for Enhancement:

- **Career Objective**: Write a strong 2–3 line objective focused on motivation, learning attitude, and role aspiration.
- **Education**: Include degree, stream, university name, and graduation year.
- **Skills**: Return at least 5 technical skills as a list of strings.
- **Projects**: Return 2 academic/personal projects as a list of objects. Each project must have:
  - A meaningful title
  - A short list of technologies used
  - A 2–3 sentence description of what was built and what it achieved
- **Experience**: For freshers, include any lab work, internships, coding practice, teamwork, etc. as 3–4 bullet points (list of strings).
- **Certifications**: Include relevant certificates, workshops, or online courses as a list of structured entries with provider and year.
- Preserve the **email**, **phone**, **GitHub**, and **LinkedIn** as provided in input.
- Do NOT include extra commentary or explanations — just valid JSON.

User Input:
Full Name: {user_data.get("full_name")}
Email: {user_data.get("email")}
Phone: {user_data.get("phone")}
Career Objective: {user_data.get("career_objective")}
Education: {user_data.get("education")}
Skills: {user_data.get("skills")}
Projects: {user_data.get("projects")}
Experience: {user_data.get("experience")}
Certifications: {user_data.get("certifications")}
LinkedIn: {user_data.get("linkedin")}
GitHub: {user_data.get("github")}
Job Description (optional): {user_data.get("job_description", "Not provided")}

Please ensure the final JSON is well-formatted, complete, and resume-ready.
"""

    logger.debug("JSON prompt built successfully")
    return prompt

def generate_resume_json(user_data: dict) -> dict:
    """Calls GPT API to generate structured resume content in JSON."""
    logger.info("Starting resume JSON generation")
    logger.debug(f"Input user data: {user_data}")
    
    prompt = build_json_prompt(user_data)
    logger.debug(f"Generated prompt length: {len(prompt)} characters")

    try:
        logger.info("Making API call to OpenAI GPT-4o-mini")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert resume writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        logger.info("Successfully received response from OpenAI API")
        logger.debug(f"Response usage: {response.usage}")

        content = response.choices[0].message.content.strip()
        logger.debug(f"Raw response content length: {len(content)} characters")
        logger.debug(f"Raw response content: {content[:200]}...")  # Log first 200 chars

        # Attempt to load JSON directly
        logger.info("Attempting to parse JSON response")
        parsed_json = json.loads(content)
        logger.info("Successfully parsed JSON response")
        logger.debug(f"Parsed JSON keys: {list(parsed_json.keys())}")
        
        return parsed_json

    except json.JSONDecodeError as je:
        logger.error(f"Invalid JSON from GPT: {je}")
        logger.error(f"Raw GPT Output:\n{content}")
        # You could optionally sanitize/fix the string here
        return {}

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        logger.exception("Full exception details:")
        return {}

# Save output to JSON file
def save_json(data, filename="output/gpt_resume_data.json"):
    os.makedirs("output", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved GPT resume output to {filename}")


if __name__ == "__main__":
    logger.info("Starting GPT Engine script execution")
    
    sample_input = {
        "full_name": "Manjunath",
        "email": "manjunathtest0@gmail.com",
        "phone": "7788878878",
        "career_objective": "To obtain a challenging role in a reputable organization.",
        "education": "B.Tech in CSE, JNTU, 2024",
        "skills": "Python, Java, HTML, CSS, SQL",
        "projects": "Ecommerce Clone - Built a clone of Amazon with product filtering, cart, etc.",
        "experience": "Fresher",
        "certifications": "AWS Workshop by Nxtwave",
        "linkedin": "https://linkedin.com/in/teja",
        "github": "https://github.com/teja",
        "job_description": ""
    }
    
    logger.info("Processing sample input data")
    output = generate_resume_json(sample_input)
    
    if output:
        logger.info("Resume generation completed successfully")
         # ✅ Add back essential contact info (GPT doesn't return these)
        output["full_name"] = sample_input["full_name"]
        output["email"] = sample_input["email"]
        output["phone"] = sample_input["phone"]
        save_json(output, filename=f"output/resume_{sample_input['full_name'].replace(' ', '_')}.json")
        print(json.dumps(output, indent=2))
    else:
        logger.warning("Resume generation returned empty result")
        print("Failed to generate resume")
    
    logger.info("GPT Engine script execution completed")
