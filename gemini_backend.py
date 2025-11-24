import os
import json
import tempfile
import google.generativeai as genai
from config import API_KEY

# Configure Gemini
genai.configure(api_key=API_KEY)

def analyze_resume(file_bytes, mime_type):
    """
    Analyzes the resume using Gemini.
    Returns a structured dictionary.
    """
    prompt = """
    You are an expert HR Resume Screener. Analyze the attached resume.
    
    Provide a JSON response with EXACTLY these fields:
    {
        "name": "Full Name of Candidate",
        "score": 75,
        "summary": "Brief professional summary in first-person style (e.g., 'Experienced software developer with...')",
        "strengths": ["Strength 1", "Strength 2", "Strength 3"],
        "weaknesses": ["Weakness 1", "Weakness 2", "Weakness 3"],
        "suggestedRole": "Job Title",
        "skillsFound": ["Skill1", "Skill2", "Skill3", "Skill4", "Skill5"]
    }

    Rules:
    - Score should be 0-100
    - suggestedRole must be ONE job title only (e.g., "Frontend Developer", not "Frontend Developer with React experience")
    - Return ONLY valid JSON, no markdown formatting, no code blocks
    - All fields are required
    """

    try:
        print("Starting resume analysis...")
        
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
        
        print(f"Temporary file created: {tmp_path}")
        
        # Upload file to Gemini
        uploaded_file = genai.upload_file(tmp_path, mime_type=mime_type)
        print(f"File uploaded to Gemini: {uploaded_file.name}")
        
        # Create model - FIXED MODEL NAME
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generate content
        print("Generating analysis...")
        response = model.generate_content([prompt, uploaded_file])
        
        print(f"Raw response: {response.text[:200]}...")
        
        # Clean response text
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if '```' in response_text:
            # Extract content between code blocks
            parts = response_text.split('```')
            for part in parts:
                if part.strip().startswith('json'):
                    response_text = part.strip()[4:].strip()
                    break
                elif part.strip().startswith('{'):
                    response_text = part.strip()
                    break
        
        # Parse JSON
        result = json.loads(response_text)
        print(f"Parsed result: {result}")
        
        # Validate required fields
        required_fields = ['name', 'score', 'summary', 'strengths', 'weaknesses', 'suggestedRole', 'skillsFound']
        for field in required_fields:
            if field not in result:
                print(f"Missing field: {field}")
                result[field] = "" if field in ['name', 'summary', 'suggestedRole'] else [] if field in ['strengths', 'weaknesses', 'skillsFound'] else 0
        
        # Clean the job title
        if 'suggestedRole' in result:
            role = result['suggestedRole']
            # Remove descriptions after comma, "with", or dash
            role = role.split(',')[0].split(' with ')[0].split(' - ')[0].strip()
            result['suggestedRole'] = role
        
        # Clean up temp file
        try:
            os.unlink(tmp_path)
            print("Temp file cleaned up")
        except:
            pass
        
        print("Analysis completed successfully!")
        return result

    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return None
    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def suggest_improvements(weaknesses):
    """
    Generates actionable fixes for weaknesses.
    """
    prompt = f"""
    You are a career coach. For each of these resume weaknesses, provide one specific, actionable tip to fix it:
    
    {json.dumps(weaknesses)}
    
    Return ONLY a JSON object in this format:
    {{
        "improvements": ["Tip for weakness 1", "Tip for weakness 2", "Tip for weakness 3"]
    }}
    
    No markdown, no code blocks, just pure JSON.
    """

    try:
        print("Generating improvements...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Clean response
        response_text = response.text.strip()
        if '```' in response_text:
            parts = response_text.split('```')
            for part in parts:
                if 'json' in part.lower():
                    response_text = part.replace('json', '').strip()
                    break
                elif '{' in part:
                    response_text = part.strip()
                    break
        
        data = json.loads(response_text)
        improvements = data.get("improvements", [])
        print(f"Generated {len(improvements)} improvements")
        return improvements
        
    except Exception as e:
        print(f"Error in improvements: {e}")
        import traceback
        traceback.print_exc()
        return []

def find_jobs(query, location, mode):
    """
    Generates job search results using Gemini.
    """
    search_prompt = f"""
    Find and list 5 real job openings for the position: "{query}"
    Location: {location if location else "Remote/Any"}
    Type: {mode if mode and mode != "Any" else "Any type"}
    
    For each job, provide:
    - Job title
    - Company name
    - Brief description
    
    Format your response as a summary paragraph followed by job listings.
    Focus on recent postings from the last 30 days.
    """

    try:
        print(f"Searching jobs for: {query}")
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(search_prompt)
        
        # Create mock job sources (since we can't access real job APIs easily)
        sources = []
        job_titles = [
            f"{query} - Entry Level",
            f"Senior {query}",
            f"{query} Specialist",
            f"{query} - Remote",
            f"Lead {query}"
        ]
        
        companies = ["TechCorp", "InnovateLabs", "DataWorks Inc", "CloudSphere", "AI Solutions"]
        
        for i, title in enumerate(job_titles):
            sources.append({
                "title": title,
                "company": companies[i],
                "url": f"https://www.linkedin.com/jobs/search/?keywords={query.replace(' ', '+')}",
                "snippet": f"Exciting opportunity for {query} role at {companies[i]}"
            })
        
        print(f"Generated {len(sources)} job results")
        
        return {
            "text": response.text,
            "sources": sources
        }

    except Exception as e:
        print(f"Error in job search: {e}")
        import traceback
        traceback.print_exc()
        return {
            "text": "Unable to fetch job listings at this time. Please try again later.",
            "sources": []
        }