import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, TypedDict, List
from async_timeout import timeout
from decouple import config
from django.core.cache import cache
from anthropic import Anthropic
from asgiref.sync import sync_to_async

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

@dataclass
class AIConfig:
    MODEL: str = "claude-3-5-sonnet-20241022"
    TIMEOUT_SECONDS: int = 30
    CACHE_DURATION: int = 3600
    MAX_TOKENS: int = 4000
    SYSTEM_PROMPT: str = (
        "You are an expert web developer focusing on creating modern, accessible websites. "
        "Respond with complete, properly formatted JSON objects."
    )

class AIResponseError(Exception):
    """Custom exception for AI response handling errors."""
    pass

class AIPlanner:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = Anthropic(api_key=api_key or config("AI_PLANNER"))
        self.logger = logging.getLogger(__name__)
        self.config = AIConfig()

    async def get_cached_response(self, prompt: str) -> WebsitePlan:
        """Retrieve response from cache or generate a new one if not cached."""
        cache_key = f"ai_response_{hash(prompt)}"
        try:
            cached_result = await sync_to_async(cache.get)(cache_key)
            if cached_result:
                self.logger.debug("Cache hit for prompt")
                return self._validate_response(cached_result)
            async with timeout(self.config.TIMEOUT_SECONDS):
                response = await self.generate_response(prompt)
                await sync_to_async(cache.set)(
                    cache_key,
                    response,
                    timeout=self.config.CACHE_DURATION
                )
                return response
        except TimeoutError:
            self.logger.error("Response generation timed out")
            raise AIResponseError("AI response generation timed out")
        except Exception as e:
            self.logger.error(f"Cache operation failed: {str(e)}")
            raise AIResponseError(f"Cache operation failed: {str(e)}")

    async def generate_response(self, prompt: str) -> WebsitePlan:
        """Generate and validate AI response."""
        try:
            response = await sync_to_async(self.client.messages.create)(
                model=self.config.MODEL,
                max_tokens=self.config.MAX_TOKENS,
                system=self.config.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            content = (
                response.content[0].text
                if hasattr(response, "content") and isinstance(response.content, list)
                else response.content
            )
            self.logger.debug(f"Raw AI response content: {content}")
            return self._extract_and_validate_json(content)
        except Exception as e:
            self.logger.error(f"AI generation error: {str(e)}")
            raise AIResponseError(f"AI generation failed: {str(e)}")

    def _extract_and_validate_json(self, content: str) -> WebsitePlan:
        """Extract JSON from content and validate its structure."""
        try:
            json_data = json.loads(content)
            return self._validate_response(json_data)
        except json.JSONDecodeError:
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, content)
            if match:
                try:
                    json_data = json.loads(match.group(0))
                    return self._validate_response(json_data)
                except json.JSONDecodeError:
                    raise AIResponseError("Found JSON-like structure but parsing failed")
            else:
                raise AIResponseError("No JSON structure found in AI response")

    def _validate_response(self, data: Dict[str, Any]) -> WebsitePlan:
        """Validate the response structure matches the expected WebsitePlan schema."""
        required_fields = {
            "client_summary": str,
            "website_template": str,
            "developer_notes": dict,
        }
        developer_notes_fields = {
            "architecture": str,
            "components": list,
            "integrations": list,
            "accessibility": str,
            "performance": str,
        }
        if not isinstance(data, dict):
            raise AIResponseError("Response must be a dictionary")
        for field, field_type in required_fields.items():
            if field not in data:
                raise AIResponseError(f"Missing required field: {field}")
            if not isinstance(data[field], field_type):
                raise AIResponseError(f"Invalid type for field {field}")
        dev_notes = data["developer_notes"]
        for field, field_type in developer_notes_fields.items():
            if field not in dev_notes:
                raise AIResponseError(f"Missing required field in developer_notes: {field}")
            if not isinstance(dev_notes[field], field_type):
                raise AIResponseError(f"Invalid type for developer_notes.{field}")
        return data

    async def generate_website_plan(
        self, 
        submission_data: Dict[str, Any],
        project_data: Optional[ProjectData] = None
    ) -> WebsitePlan:
        """Generate website plan incorporating both planner and project data."""
        prompt = self._create_combined_prompt(submission_data, project_data) if project_data else self._create_prompt(submission_data)
        return await self.get_cached_response(prompt)

    def _create_combined_prompt(
        self,
        submission_data: Dict[str, Any],
        project_data: ProjectData
    ) -> str:
        """Create a comprehensive prompt combining project and planner data."""
        return f"""
        Project Package: {project_data['package_name']} (€{project_data['price_eur']})
        Selected Features: {', '.join(project_data['features'])}
        Add-ons: {', '.join(addon['name'] for addon in project_data['addons'])}
        Total Budget: €{project_data['total_price']}

        Client Requirements:
        {self._format_planner_data(submission_data)}

        Please provide a JSON response with:
        1. client_summary: A comprehensive project overview
        2. website_template: Complete HTML5/CSS/JS code for a responsive website preview
        3. developer_notes: Technical specifications and implementation guidelines
        """

    def _create_prompt(self, submission_data: Dict[str, Any]) -> str:
        """Construct the prompt string for the AI based on submission data only."""
        return (
            f"Create a website plan based on these requirements: {json.dumps(submission_data, indent=2)}\n\n"
            "Respond with a single, complete JSON object using this exact structure:\n"
            "{\n"
            '  "client_summary": "string",\n'
            '  "website_template": "string",\n'
            '  "developer_notes": {\n'
            '    "architecture": "string",\n'
            '    "components": ["string"],\n'
            '    "integrations": ["string"],\n'
            '    "accessibility": "string",\n'
            '    "performance": "string"\n'
            "  }\n"
            "}\n\n"
            "Do not include any text before or after the JSON object. Ensure all values are properly quoted strings or arrays."
        )

    def _format_planner_data(self, data: Dict[str, Any]) -> str:
        """Format planner data for the prompt."""
        return "\n".join(f"{key}: {value}" for key, value in data.items())

async def update_developer_worksheet(submission: Any) -> None:
    """Update the developer worksheet with the AI-generated website plan."""
    planner = AIPlanner()
    try:
        ai_response = await planner.generate_website_plan(submission.submission_data)
        if not isinstance(ai_response, dict) or "developer_notes" not in ai_response:
            logging.error(f"Invalid AI response structure: {ai_response}")
            raise AIResponseError("Invalid AI response structure")
        await sync_to_async(lambda: submission.__setattr__(
            "developer_worksheet",
            ai_response["developer_notes"]
        ))()
        await sync_to_async(submission.save)()
    except AIResponseError as e:
        logging.error(f"AI response error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error updating developer worksheet: {str(e)}")
        raise