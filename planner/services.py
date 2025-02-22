import json
import logging
import re
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional, TypedDict, List, Union
from async_timeout import timeout
from decouple import config
from django.core.cache import cache
from anthropic import Anthropic
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# --- TypedDict definitions for legacy project data ---
class ProjectData(TypedDict):
    package_type: str
    package_name: str
    price_eur: float
    features: List[str]
    addons: List[Dict[str, Any]]
    total_price: float

class DeveloperNotes(TypedDict):
    architecture: str
    components: List[str]
    integrations: List[str]
    accessibility: str
    performance: str

class WebsitePlan(TypedDict):
    client_summary: str
    website_template: str
    developer_notes: DeveloperNotes

# --- Simplified project context (without pricing information) ---
@dataclass
class ProjectContext:
    package_type: str
    package_name: str
    features: List[str]
    selected_addons: List[str]
    business_goals: List[str]

# --- Updated AIConfig with better model choice and configuration ---
@dataclass
class AIConfig:
    MODEL: str = "claude-3-5-sonnet-20241022"  # Using Sonnet for optimal performance and cost
    TIMEOUT_SECONDS: int = 120
    CACHE_DURATION: int = 3600
    MAX_TOKENS: int = 4000
    SYSTEM_PROMPTS: Dict[str, str] = None
    SYSTEM_PROMPT: str = ""

    def __post_init__(self):
        self.SYSTEM_PROMPTS = {
            'template': """Create a modern, responsive website template:
- Use semantic HTML5 structure
- Implement mobile-first design with CSS Grid/Flexbox
- Follow WCAG 2.1 AA accessibility standards
- Add performance optimizations and progressive enhancement
- Include modern JS features and error handling
- Create a multi-page structure with clean navigation
- Use CSS custom properties for theming
- Add responsive breakpoints and dark mode support
- Implement lazy loading and image optimization
- Add proper meta tags and SEO elements

Response Format:
{
  "html": "Main HTML content",
  "css": "All CSS styles",
  "js": "All JavaScript code",
  "pages": [
    {
      "title": "Page Title",
      "path": "/page-path",
      "content": "Page HTML content"
    }
  ]
}""",
            'developer': """Provide comprehensive technical specifications:
{
  "architecture": "Technical stack and infrastructure",
  "components": ["List of reusable components"],
  "integrations": ["Required third-party services"],
  "data_model": ["Database schema and relationships"],
  "api_endpoints": ["Required API endpoints"],
  "security": ["Security measures and considerations"],
  "accessibility": "WCAG compliance implementation",
  "performance": "Performance optimization strategies",
  "deployment": "Deployment and hosting requirements"
}""",
            'summary': """Create a concise project summary focusing on:
- Business objectives and goals
- Target audience and user needs
- Core features and functionality
- Design direction and brand alignment
- Technical considerations
- Development timeline and milestones

Response Format:
{
  "summary": "Your comprehensive summary here"
}"""
        }
        self.SYSTEM_PROMPT = self.SYSTEM_PROMPTS['template']

# --- Custom exception for AI response handling errors ---
class AIResponseError(Exception):
    pass

# --- Shared JSON extraction/validation helpers ---

def validate_json_data(json_data: dict) -> WebsitePlan:
    """
    Validate that the JSON data contains the required fields with the correct types.
    """
    if not isinstance(json_data, dict):
        raise AIResponseError("Response must be a dictionary")
    
    required_fields = {
        "client_summary": str,
        "website_template": str,
        "developer_notes": dict
    }
    for field, expected_type in required_fields.items():
        if field not in json_data:
            raise AIResponseError(f"Missing required field: {field}")
        if not isinstance(json_data[field], expected_type):
            raise AIResponseError(
                f"Invalid type for {field}: expected {expected_type.__name__}, got {type(json_data[field]).__name__}"
            )
    
    dev_notes = json_data["developer_notes"]
    required_dev_notes = {
        "architecture": str,
        "components": list,
        "integrations": list,
        "accessibility": str,
        "performance": str
    }
    for field, expected_type in required_dev_notes.items():
        if field not in dev_notes:
            raise AIResponseError(f"Missing required field in developer_notes: {field}")
        if not isinstance(dev_notes[field], expected_type):
            raise AIResponseError(f"Invalid type for developer_notes.{field}")
    
    return json_data

def extract_and_validate_json(content: Union[str, dict]) -> WebsitePlan:
    """
    Enhanced JSON extraction with better error handling and sanitization.
    Accepts either a JSON string or a dict.
    """
    try:
        if isinstance(content, dict):
            # If already a dict, just validate its structure.
            return validate_json_data(content)
        
        # Remove any control characters and sanitize the input
        cleaned_content = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', content)
        
        # Try to find valid JSON object in the response
        match = re.search(r'\{(?:[^{}]|{[^{}]*})*\}', cleaned_content)
        if not match:
            logger.error("No valid JSON object found in response")
            logger.error(f"Content received: {cleaned_content[:1000]}")
            raise AIResponseError("No valid JSON structure found in response")
            
        json_str = match.group(0)
        
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Problematic JSON: {json_str[:1000]}")
            raise AIResponseError(f"Failed to parse JSON: {str(e)}")
        
        return validate_json_data(json_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.error(f"Content causing error: {content[:1000]}")
        raise AIResponseError(f"JSON parsing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error in JSON extraction: {str(e)}")
        logger.error(f"Content: {content[:1000]}")
        raise AIResponseError(f"JSON extraction failed: {str(e)}")

# --- AIPlanner with Enhanced Error Handling ---
class AIPlanner:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = Anthropic(api_key=api_key or config("AI_PLANNER"))
        self.config = AIConfig()

    async def get_cached_response(self, prompt: str) -> WebsitePlan:
        cache_key = f"ai_response_{hash(prompt)}"
        try:
            cached_result = await sync_to_async(cache.get)(cache_key)
            if cached_result:
                logger.debug("Cache hit for prompt")
                return extract_and_validate_json(cached_result)
            
            async with timeout(self.config.TIMEOUT_SECONDS):
                response = await self.generate_response(prompt)
                await sync_to_async(cache.set)(cache_key, response, timeout=self.config.CACHE_DURATION)
                return response

        except asyncio.TimeoutError:
            logger.error("Response generation timed out")
            raise AIResponseError("AI response generation timed out")
        except Exception as e:
            logger.error(f"Cache operation failed: {str(e)}")
            raise AIResponseError(f"Cache operation failed: {str(e)}")

    async def generate_response(self, prompt: str) -> WebsitePlan:
        try:
            logger.debug(f"Generating AI response for prompt of length {len(prompt)}")
            response = await sync_to_async(self.client.messages.create)(
                model=self.config.MODEL,
                max_tokens=self.config.MAX_TOKENS,
                system=self.config.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if hasattr(response, "content") and isinstance(response.content, list):
                content = response.content[0].text
            else:
                content = response.content
                
            if not content:
                raise AIResponseError("Empty response from AI model")
                
            logger.debug(f"Raw AI response content (first 500 chars): {content[:500]}")
            return extract_and_validate_json(content)
            
        except asyncio.TimeoutError:
            logger.error("Response generation timed out")
            raise AIResponseError("AI response generation timed out")
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            raise AIResponseError(f"AI generation failed: {str(e)}")

    async def generate_website_plan(
        self,
        submission_data: Dict[str, Any],
        project_data: Optional[ProjectData] = None
    ) -> WebsitePlan:
        prompt = (
            self._create_combined_prompt(submission_data, project_data)
            if project_data
            else self._create_prompt(submission_data)
        )
        return await self.get_cached_response(prompt)

    def _create_combined_prompt(
        self,
        submission_data: Dict[str, Any],
        project_data: ProjectData
    ) -> str:
        return f"""
Project Context:
- Package: {project_data['package_name']}
- Package Type: {project_data['package_type']}
- Selected Features: {', '.join(project_data['features'])}
- Add-ons: {', '.join(addon.get('name', 'Unnamed Addon') for addon in project_data['addons'])}

Detailed Project Requirements:
{self._format_submission_data(submission_data)}

Objective:
Create a comprehensive website plan with the following deliverables:
1. A concise client summary
2. Complete HTML5/CSS/JS website template
3. Detailed developer technical specifications

Critical Instructions:
- Respond ONLY with a valid JSON object 
- Fill ALL fields with meaningful, specific content
- Use EXACT structure from system prompt
- Tailor content precisely to project requirements
"""

    def _create_prompt(self, submission_data: Dict[str, Any]) -> str:
        return f"""
Project Requirements:
{self._format_submission_data(submission_data)}

Objective:
Generate a comprehensive website plan with:
1. Concise client summary
2. Complete HTML5/CSS/JS website template
3. Detailed developer technical specifications

Critical Instructions:
- Respond ONLY with a valid JSON object
- Fill ALL fields with meaningful, specific content
- Use EXACT structure from system prompt
- Tailor content precisely to project requirements
"""

    def _format_submission_data(self, data: Dict[str, Any]) -> str:
        formatted_sections = []

        # Project Overview
        overview = data.get('projectOverview', {})
        overview_str = f"""
Project Overview:
- Name: {overview.get('projectName', 'Unnamed Project')}
- Industry: {overview.get('industry', 'Unspecified')}
- Timeline: {overview.get('timeline', 'Not Specified')}
- Target Audience: {', '.join(overview.get('targetAudience', []))}
- Vision: {overview.get('vision', 'No specific vision stated')}
"""
        formatted_sections.append(overview_str)

        # Business Goals
        business_goals = data.get('businessGoals', {})
        goals_str = f"""
Business Goals:
- Primary Objective: {business_goals.get('primaryObjective', 'Not Specified')}
- Brand Personality: {business_goals.get('brandPersonality', 'Not Defined')}
- Primary Purpose: {', '.join(business_goals.get('primaryPurpose', []))}
- Homepage Sections: {', '.join(business_goals.get('homepageSections', []))}
"""
        formatted_sections.append(goals_str)

        # Design Preferences
        design_prefs = data.get('designPreferences', {})
        design_str = f"""
Design Preferences:
- Style: {design_prefs.get('stylePreference', 'Not Specified')}
- Color Palette: {design_prefs.get('colorPalette', 'Not Specified')}
- Font Pairing: {design_prefs.get('fontPairing', 'Not Specified')}
- Inspirational Websites: {', '.join(design_prefs.get('inspirationalWebsites', []))}
"""
        formatted_sections.append(design_str)

        # User Experience
        ux_prefs = design_prefs.get('userExperience', {})
        ux_str = f"""
User Experience:
- Device Support: {', '.join(ux_prefs.get('deviceSupport', []))}
- Performance Expectations: {ux_prefs.get('performanceExpectations', 'Not Specified')}
- Accessibility Goals: {ux_prefs.get('accessibility', 'Not Specified')}
"""
        formatted_sections.append(ux_str)

        return "\n".join(formatted_sections)

# --- EnhancedAIPlanner with Concurrent Generation ---
class EnhancedAIPlanner:
    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key or config("AI_PLANNER"))
        self.config = AIConfig()

    async def generate_complete_plan(
        self,
        submission_data: Dict[str, Any],
        project_context: Optional[ProjectContext] = None
    ) -> Dict[str, Any]:
        summary_task = self._generate_summary(submission_data, project_context)
        template_task = self._generate_template(submission_data, project_context)
        developer_task = self._generate_developer_notes(submission_data, project_context)

        summary, template, developer_notes = await asyncio.gather(
            summary_task, template_task, developer_task
        )

        return {
            "client_summary": summary,
            "website_template": template,
            "developer_notes": developer_notes
        }

    def _create_template_prompt(self, data: Dict[str, Any], context: Optional[ProjectContext]) -> str:
        sections = []
        if 'designPreferences' in data:
            design = data['designPreferences']
            sections.append(f"""
Design Requirements:
- Brand Personality: {design.get('brandPersonality', 'Not Specified')}
- Color Palette: {design.get('colorPalette', 'Not Specified')}
- Typography: {design.get('fontPairing', 'Not Specified')}
- Style: {design.get('stylePreference', 'Not Specified')}
- Accessibility Level: {design.get('userExperience', {}).get('accessibility', 'Standard')}
- Responsive Design: {design.get('userExperience', {}).get('responsive', 'Mobile-First')}
""")
        if 'businessGoals' in data:
            business = data['businessGoals']
            sections.append(f"""
Content Structure:
- Primary Purpose: {', '.join(business.get('primaryPurpose', []))}
- Required Sections: {', '.join(business.get('homepageSections', []))}
- Navigation: {', '.join(business.get('requiredPages', []))}
""")
        if context:
            sections.append(f"""
Technical Stack:
- Package Type: {context.package_type}
- Core Features: {', '.join(context.features)}
- Additional Features: {', '.join(context.selected_addons)}
""")
        return "\n".join(sections)

    def _create_developer_prompt(self, data: Dict[str, Any], context: Optional[ProjectContext]) -> str:
        return self.config.SYSTEM_PROMPTS['developer']

    def _create_summary_prompt(self, data: Dict[str, Any], context: Optional[ProjectContext]) -> str:
        return self.config.SYSTEM_PROMPTS['summary']

    async def _generate_ai_response(self, prompt: str, system: Optional[str] = None) -> WebsitePlan:
        try:
            response = await sync_to_async(self.client.messages.create)(
                model=self.config.MODEL,
                max_tokens=self.config.MAX_TOKENS,
                system=system if system is not None else self.config.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            if hasattr(response, "content") and isinstance(response.content, list):
                content = response.content[0].text
            else:
                content = response.content
            return extract_and_validate_json(content)
        except Exception as e:
            logger.error(f"Enhanced AI generation error: {str(e)}")
            raise AIResponseError(f"Enhanced AI generation failed: {str(e)}")

    async def _generate_summary(self, submission_data: Dict[str, Any], context: Optional[ProjectContext]) -> str:
        prompt = self._create_summary_prompt(submission_data, context)
        response = await self._generate_ai_response(prompt, system=self.config.SYSTEM_PROMPTS['summary'])
        return response.get("summary") or response.get("client_summary", "")

    async def _generate_template(self, submission_data: Dict[str, Any], context: Optional[ProjectContext]) -> str:
        prompt = self._create_template_prompt(submission_data, context)
        response = await self._generate_ai_response(prompt, system=self.config.SYSTEM_PROMPTS['template'])
        return response.get("website_template", "")

    async def _generate_developer_notes(self, submission_data: Dict[str, Any], context: Optional[ProjectContext]) -> Any:
        prompt = self._create_developer_prompt(submission_data, context)
        response = await self._generate_ai_response(prompt, system=self.config.SYSTEM_PROMPTS['developer'])
        return response.get("developer_notes", {})

# --- Background Task ---
async def update_developer_worksheet(submission: Any) -> None:
    """
    Update the developer worksheet with the AI-generated website plan.
    This background task uses the AIPlanner to generate the plan and saves the developer notes.
    """
    planner = AIPlanner()
    try:
        ai_response = await planner.generate_website_plan(submission.submission_data)
        if not isinstance(ai_response, dict) or "developer_notes" not in ai_response:
            logger.error(f"Invalid AI response structure: {ai_response}")
            raise AIResponseError("Invalid AI response structure")
        await sync_to_async(lambda: submission.__setattr__(
            "developer_worksheet", json.dumps(ai_response["developer_notes"])
        ))()
        await sync_to_async(submission.save)()
    except AIResponseError as e:
        logger.error(f"AI response error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating developer worksheet: {str(e)}")
        raise
