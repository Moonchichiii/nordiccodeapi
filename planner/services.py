# planner/services.py
from openai import OpenAI
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class AIPlanner:
    """
    Comprehensive service for AI-powered project planning and analysis
    """
    
    @staticmethod
    async def analyze_requirements(project_type: str, requirements: dict):
        """Analyze project requirements using GPT-4"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert web development project planner with deep knowledge of:
                            - Modern web architectures
                            - Development best practices
                            - Project estimation
                            - Technical risk assessment
                            """
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Project Type: {project_type}
                        Requirements: {json.dumps(requirements, indent=2)}
                        
                        Please provide a comprehensive analysis including:
                        1. Technical Stack Recommendations:
                           - Frontend framework and libraries
                           - Backend technologies
                           - Database solutions
                           - DevOps and deployment
                        
                        2. Potential Challenges and Solutions:
                           - Technical risks
                           - Scalability considerations
                           - Security concerns
                           - Performance optimization
                        
                        3. Development Timeline:
                           - Major milestones
                           - Phase breakdown
                           - Time estimates per phase
                        
                        4. Resource Requirements:
                           - Team composition
                           - Skill requirements
                           - Infrastructure needs
                        
                        Format your response in a clear, structured JSON-like format.
                        """
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return {
                "analysis": response.choices[0].message.content,
                "confidence_score": response.choices[0].finish_reason == "stop" and 1.0 or 0.8
            }
        except Exception as e:
            logger.error(f"AI Analysis Error: {str(e)}")
            raise

    @staticmethod
    async def get_design_recommendations(requirements: dict, preferences: dict):
        """Get AI-powered design recommendations"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert web designer specializing in:
                            - Modern UI/UX principles
                            - Brand identity
                            - Responsive design
                            - Accessibility
                            """
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Based on:
                        Requirements: {json.dumps(requirements, indent=2)}
                        User Preferences: {json.dumps(preferences, indent=2)}
                        
                        Please provide comprehensive design recommendations including:
                        1. Color Scheme:
                           - Primary and secondary colors (with hex codes)
                           - Accent colors
                           - Dark/light mode variations
                        
                        2. Typography:
                           - Font pairings
                           - Heading hierarchy
                           - Text sizes and weights
                        
                        3. Layout Structure:
                           - Component hierarchy
                           - Grid system
                           - Spacing guidelines
                        
                        4. UI Elements:
                           - Button styles
                           - Form elements
                           - Navigation patterns
                           - Card designs
                        
                        5. Responsive Design:
                           - Breakpoints
                           - Mobile-first considerations
                           - Touch targets
                        
                        Format your response in a clear, structured JSON-like format.
                        """
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return {
                "recommendations": response.choices[0].message.content,
                "confidence_score": response.choices[0].finish_reason == "stop" and 1.0 or 0.8
            }
        except Exception as e:
            logger.error(f"Design Recommendations Error: {str(e)}")
            raise

    @staticmethod
    async def get_tech_stack_recommendations(project_type: str, requirements: dict):
        """Get detailed technology stack recommendations"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in modern web development stacks with deep knowledge of:
                            - Frontend frameworks and libraries
                            - Backend technologies
                            - Database systems
                            - DevOps and deployment
                            - Security best practices
                            """
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Project Type: {project_type}
                        Requirements: {json.dumps(requirements, indent=2)}
                        
                        Please provide detailed tech stack recommendations including:
                        1. Frontend:
                           - Framework choice with rationale
                           - Key libraries and tools
                           - State management
                           - Build system
                        
                        2. Backend:
                           - Framework selection
                           - API architecture
                           - Authentication system
                           - Performance considerations
                        
                        3. Database:
                           - Database type and specific solution
                           - Data modeling approach
                           - Scaling strategy
                        
                        4. DevOps:
                           - Deployment strategy
                           - CI/CD pipeline
                           - Monitoring and logging
                           - Security measures
                        
                        Format your response in a clear, structured JSON-like format.
                        """
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return {
                "recommendations": response.choices[0].message.content,
                "confidence_score": response.choices[0].finish_reason == "stop" and 1.0 or 0.8
            }
        except Exception as e:
            logger.error(f"Tech Stack Recommendation Error: {str(e)}")
            raise