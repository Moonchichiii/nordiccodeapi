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

logger = logging.getLogger(__name__)

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
    framework: Dict[str, Any]

class WebsiteTemplate(TypedDict):
    sections: Dict[str, str]
    css: str
    js: str
    meta: Dict[str, Any]

class WebsitePlan(TypedDict):
    client_summary: str
    website_template: WebsiteTemplate
    developer_notes: DeveloperNotes

@dataclass
class AIConfig:
    MODEL: str = "claude-3-5-sonnet-20241022"
    TIMEOUT_SECONDS: int = 120
    CACHE_DURATION: int = 3600
    MAX_TOKENS: int = 4000
    SYSTEM_PROMPTS: Dict[str, str] = None
    SYSTEM_PROMPT: str = ""

    def __post_init__(self):
        self.SYSTEM_PROMPTS = {
            'template': (
                "Your task is to generate a complete website plan based on the following input. "
                "Your response must be a valid JSON object with three keys:\n\n"
                "1. \"client_summary\": A brief overview of the website plan, intended for client review.\n"
                "2. \"website_template\": A complete HTML5/CSS/JS website template. Under the key \"sections\", include keys for "
                "'hero', 'about', 'services', 'testimonials', 'contact', and 'blog'.\n"
                "3. \"developer_notes\": A detailed technical specification intended solely for the developer. "
                "In this section, provide free-form recommendations on which framework to use based on the provided package type. "
                "These suggestions should appear only in this section.\n\n"
                "Respond ONLY with a valid JSON object that exactly matches the following structure:\n\n"
                "{\n"
                "  \"client_summary\": \"...\",\n"
                "  \"website_template\": {\n"
                "       \"sections\": { \"hero\": \"...\", \"about\": \"...\", \"services\": \"...\", \"testimonials\": \"...\", \"contact\": \"...\", \"blog\": \"...\" },\n"
                "       \"css\": \"...\",\n"
                "       \"js\": \"...\",\n"
                "       \"meta\": { \"colors\": { ... }, \"typography\": { \"headings\": \"...\", \"body\": \"...\" }, \"spacing\": \"...\", \"breakpoints\": [ ... ] }\n"
                "  },\n"
                "  \"developer_notes\": {\n"
                "       \"architecture\": \"...\",\n"
                "       \"components\": [ \"...\" ],\n"
                "       \"integrations\": [ \"...\" ],\n"
                "       \"accessibility\": \"...\",\n"
                "       \"performance\": \"...\",\n"
                "       \"framework\": {\n"
                "            \"primary\": \"...\",\n"
                "            \"alternatives\": [ \"...\" ],\n"
                "            \"reasoning\": \"...\"\n"
                "       }\n"
                "  }\n"
                "}\n"
            )
        }
        self.SYSTEM_PROMPT = self.SYSTEM_PROMPTS['template']

class AIResponseError(Exception):
    pass

class AIPlanner:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = Anthropic(api_key=api_key or config("AI_PLANNER"))
        self.config = AIConfig()

    async def get_cached_response(self, prompt: str) -> WebsitePlan:
        cache_key = f"ai_response_{hash(prompt)}"
        try:
            cached_result = await sync_to_async(cache.get)(cache_key)
            if cached_result:
                return self._validate_response(cached_result)
            async with timeout(self.config.TIMEOUT_SECONDS):
                response = await self.generate_response(prompt)
                await sync_to_async(cache.set)(cache_key, response, timeout=self.config.CACHE_DURATION)
                return response
        except TimeoutError:
            logger.error("Response generation timed out")
            raise AIResponseError("AI response generation timed out after 120 seconds")
        except Exception as e:
            logger.error(f"Cache operation failed: {str(e)}")
            raise AIResponseError(f"Cache operation failed: {str(e)}")

    async def generate_response(self, prompt: str) -> WebsitePlan:
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
            return self._extract_and_validate_json(content)
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            raise AIResponseError(f"AI generation failed: {str(e)}")

    def _extract_and_validate_json(self, content: str) -> WebsitePlan:
        def clean_json_content(text: str) -> str:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            return match.group(0) if match else text
        try:
            try:
                json_data = json.loads(content)
                return self._validate_response(json_data)
            except json.JSONDecodeError:
                cleaned_content = clean_json_content(content)
                json_data = json.loads(cleaned_content)
                return self._validate_response(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise AIResponseError(f"Unable to parse JSON: {e}")
        except Exception as e:
            logger.error(f"JSON extraction error: {str(e)}")
            raise AIResponseError(f"JSON extraction failed: {str(e)}")

    def _validate_response(self, data: Dict[str, Any]) -> WebsitePlan:
        if not isinstance(data, dict):
            logger.error("Response data is not a dictionary.")
            raise AIResponseError("Response must be a dictionary")
        required_fields = {"client_summary": str, "website_template": dict, "developer_notes": dict}
        for field, field_type in required_fields.items():
            if field not in data:
                logger.error(f"Missing required field: {field}")
                raise AIResponseError(f"Missing required field: {field}")
            if not isinstance(data[field], field_type):
                logger.error(f"Invalid type for {field}")
                raise AIResponseError(f"Invalid type for {field}")

        if isinstance(data["client_summary"], str):
            data["client_summary"] = data["client_summary"].strip()

        template = data["website_template"]
        template_fields = {"sections": dict, "css": str, "js": str, "meta": dict}
        for field, field_type in template_fields.items():
            if field not in template:
                logger.error(f"Missing field in website_template: {field}")
                raise AIResponseError(f"Missing field in website_template: {field}")
            if not isinstance(template[field], field_type):
                logger.error(f"Invalid type for website_template.{field}")
                raise AIResponseError(f"Invalid type for website_template.{field}")
        if isinstance(template["css"], str):
            template["css"] = template["css"].strip()
        if isinstance(template["js"], str):
            template["js"] = template["js"].strip()

        sections = template["sections"]
        valid_sections = {"hero", "about", "services", "testimonials", "contact", "blog"}
        for section_name, content in sections.items():
            if section_name not in valid_sections:
                logger.error(f"Invalid section name: {section_name}")
                raise AIResponseError(f"Invalid section name: {section_name}")
            if content is None:
                sections[section_name] = ""
            elif not isinstance(content, str):
                logger.error(f"Invalid content type for section: {section_name}")
                raise AIResponseError(f"Invalid content type for section: {section_name}")
            else:
                sections[section_name] = content.strip()

        dev_notes = data["developer_notes"]
        required_dev_notes = {"architecture": str, "components": list, "integrations": list, "accessibility": str, "performance": str, "framework": dict}
        for field, field_type in required_dev_notes.items():
            if field not in dev_notes:
                logger.error(f"Missing field in developer_notes: {field}")
                raise AIResponseError(f"Missing field in developer_notes: {field}")
            if not isinstance(dev_notes[field], field_type):
                logger.error(f"Invalid type for developer_notes.{field}")
                raise AIResponseError(f"Invalid type for developer_notes.{field}")
            if field_type == str:
                dev_notes[field] = dev_notes[field].strip() if dev_notes[field] else dev_notes[field]

        framework = dev_notes["framework"]
        required_framework_fields = {"primary": str, "alternatives": list, "reasoning": str}
        for field, field_type in required_framework_fields.items():
            if field not in framework:
                logger.error(f"Missing field in framework: {field}")
                raise AIResponseError(f"Missing field in framework: {field}")
            if not isinstance(framework[field], field_type):
                logger.error(f"Invalid type for framework.{field}")
                raise AIResponseError(f"Invalid type for framework.{field}")
            if field_type == str:
                framework[field] = framework[field].strip() if framework[field] else framework[field]
        return data

    def _format_submission_data(self, data: Dict[str, Any]) -> str:
        overview = data.get('projectOverview', {})
        overview_str = (
            f"Project Overview:\n"
            f"- Name: {overview.get('projectName', 'Unnamed Project')}\n"
            f"- Industry: {overview.get('industry', 'Unspecified')}\n"
            f"- Timeline: {overview.get('timeline', 'Not Specified')}\n"
            f"- Vision: {overview.get('vision', 'No specific vision stated')}\n"
        )
        business_goals = data.get('businessGoals', {})
        goals_str = (
            f"Business Goals:\n"
            f"- Primary Objective: {business_goals.get('primaryObjective', 'Not Specified')}\n"
            f"- Primary Purpose: {', '.join(business_goals.get('primaryPurpose', []))}\n"
            f"- Homepage Sections: {', '.join(business_goals.get('homepageSections', []))}\n"
        )
        design_prefs = data.get('designPreferences', {})
        design_str = (
            f"Design Preferences:\n"
            f"- Style Preference: {design_prefs.get('stylePreference', 'Not Specified')}\n"
            f"- Color Palette: {design_prefs.get('colorPalette', 'Not Specified')}\n"
            f"- Font Pairing: {design_prefs.get('fontPairing', 'Not Specified')}\n"
        )
        ux_prefs = design_prefs.get('userExperience', {})
        ux_str = (
            f"User Experience:\n"
            f"- Accessibility: {ux_prefs.get('accessibility', 'Not Specified')}\n"
            f"- Device Support: {', '.join(ux_prefs.get('deviceSupport', []))}\n"
            f"- Performance Expectations: {ux_prefs.get('performanceExpectations', 'Not Specified')}\n"
            f"- Performance: {ux_prefs.get('performance', 'Not Specified')}\n"
            f"- Responsive: {ux_prefs.get('responsive', 'Not Specified')}\n"
        )
        formatted_data = "\n".join([overview_str, goals_str, design_str, ux_str])
        return formatted_data

    def _create_combined_prompt(self, submission_data: Dict[str, Any], project_data: ProjectData) -> str:
        prompt = (
            f"Project Context:\n"
            f"- Package: {project_data['package_name']} (€{project_data['price_eur']})\n"
            f"- Package Type: {project_data['package_type']}\n"
            f"- Total Budget: €{project_data['total_price']}\n"
            f"- Selected Features: {', '.join(project_data['features'])}\n"
            f"- Add-ons: {', '.join(addon.get('name', 'Unnamed Addon') for addon in project_data['addons'])}\n\n"
            f"Detailed Project Requirements:\n{self._format_submission_data(submission_data)}\n\n"
            f"Objective:\n"
            f"Generate a comprehensive website plan with the following deliverables:\n"
            f"1. A concise client summary (for client review).\n"
            f"2. A complete HTML5/CSS/JS website template with the specified homepage sections (for client preview).\n"
            f"3. A detailed developer worksheet containing technical recommendations. In the developer worksheet, include free-form "
            f"suggestions on which framework to use based on the provided package type. These suggestions must appear only in the "
            f"'developer_notes' section.\n\n"
            f"Critical Instructions:\n"
            f"- Respond ONLY with a valid JSON object matching the defined structure.\n"
            f"- Fill ALL fields with meaningful, specific content.\n"
            f"- Use the EXACT JSON structure as defined.\n"
            f"- Tailor content precisely to the project requirements.\n"
        )
        return prompt

    def _create_prompt(self, submission_data: Dict[str, Any]) -> str:
        prompt = (
            f"Project Requirements:\n{self._format_submission_data(submission_data)}\n\n"
            f"Objective:\n"
            f"Generate a comprehensive website plan with the following deliverables:\n"
            f"1. A concise client summary (for client review).\n"
            f"2. A complete HTML5/CSS/JS website template with homepage sections (for client preview).\n"
            f"3. A detailed developer worksheet with technical recommendations including free framework suggestions.\n\n"
            f"Critical Instructions:\n"
            f"- Respond ONLY with a valid JSON object matching the defined structure.\n"
            f"- Fill ALL fields with meaningful, specific content.\n"
            f"- Use the EXACT JSON structure as defined.\n"
            f"- Tailor content precisely to the project requirements.\n"
        )
        return prompt

    async def generate_website_plan(self, submission_data: Dict[str, Any], project_data: Optional[ProjectData] = None) -> WebsitePlan:
        prompt = (self._create_combined_prompt(submission_data, project_data)
                  if project_data else self._create_prompt(submission_data))
        website_plan = await self.get_cached_response(prompt)
        if project_data:
            framework_recommendation = self._recommend_framework(project_data['package_type'])
            if isinstance(website_plan["developer_notes"], dict):
                website_plan["developer_notes"]["framework"] = framework_recommendation
        return website_plan

    def _recommend_framework(self, project_type: str) -> Dict[str, Any]:
        frameworks = {
            "static": {
                "primary": "Next.js",
                "alternatives": ["Astro", "Gatsby"],
                "reasoning": "For static sites, Next.js (or similar) delivers fast, SEO-optimized performance."
            },
            "fullstack": {
                "primary": "Next.js",
                "alternatives": ["Nuxt.js", "SvelteKit"],
                "reasoning": "For full-stack applications, Next.js offers robust API routes and server-side rendering."
            },
            "enterprise": {
                "primary": "Next.js Enterprise",
                "alternatives": ["Remix", "Next.js Enterprise"],
                "reasoning": "For enterprise-grade projects, a specialized enterprise framework provides scalable and advanced features."
            }
        }
        return frameworks.get(project_type, frameworks["static"])

    def _determine_state_needs(self, project_type: str) -> Dict[str, Any]:
        state_management = {
            "static": {
                "recommendation": "React Context + Local Storage",
                "reasoning": "A lightweight solution for basic state management."
            },
            "fullstack": {
                "recommendation": "Redux Toolkit + RTK Query",
                "reasoning": "Provides robust state management with integrated API handling."
            },
            "enterprise": {
                "recommendation": "Redux Toolkit + Redux Saga",
                "reasoning": "Handles complex state with side effects effectively."
            }
        }
        return state_management.get(project_type, state_management["static"])

    def _plan_api_integration(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        business_goals = submission_data.get('businessGoals', {})
        primary_purpose = business_goals.get('primaryPurpose', [])
        integrations = {
            "required": [],
            "optional": [],
            "security": ["JWT Authentication", "CORS Configuration"]
        }
        if "Sell Products" in primary_purpose:
            integrations["required"].extend([
                "Payment Gateway API",
                "Inventory Management API",
                "Order Processing API"
            ])
        if "Get Appointments" in primary_purpose:
            integrations["required"].extend([
                "Calendar API",
                "Booking System API",
                "Notification Service"
            ])
        return integrations

    def _create_seo_strategy(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        industry = submission_data.get('projectOverview', {}).get('industry', '')
        business_goals = submission_data.get('businessGoals', {})
        strategy = {
            "technical_seo": [
                "Server-side rendering",
                "Optimized meta tags",
                "Structured data implementation",
                "Sitemap generation",
                "Robots.txt configuration"
            ],
            "content_strategy": [
                f"Industry-specific keywords for {industry}",
                "Regular content updates",
                "Blog integration",
                "Social media integration"
            ],
            "monitoring": [
                "Google Search Console integration",
                "Analytics setup",
                "Performance monitoring"
            ]
        }
        return strategy

async def update_developer_worksheet(submission: Any) -> None:
    planner = AIPlanner()
    try:
        ai_response = await planner.generate_website_plan(submission.submission_data)
        if not isinstance(ai_response, dict) or "developer_notes" not in ai_response:
            logger.error(f"Invalid AI response structure: {ai_response}")
            raise AIResponseError("Invalid AI response structure")
        await sync_to_async(lambda: submission.__setattr__(
            "developer_worksheet", json.dumps(ai_response["developer_notes"])
        ))()
        if "website_template" in ai_response:
            await sync_to_async(lambda: submission.__setattr__(
                "website_template", json.dumps(ai_response["website_template"])
            ))()
        if "client_summary" in ai_response:
            await sync_to_async(lambda: submission.__setattr__(
                "client_summary", ai_response["client_summary"]
            ))()
        await sync_to_async(submission.save)()
    except AIResponseError as e:
        logger.error(f"AI response error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating developer worksheet: {str(e)}")
        raise
