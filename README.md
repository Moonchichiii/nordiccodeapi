# Nordic Code Works - Backend API

[Live Project Link](Coming Soon!)
[Frontend Repository Link]()

## Table of Contents
1. [Project Overview](#project-overview)
2. [Planning & Design](#planning--design)
3. [Technologies](#technologies)
4. [Testing](#testing)
5. [Deployment](#deployment)
6. [Credits](#credits)

## Project Overview

The Nordic Code Works Backend API is a personal project management system designed to organize and track projects from my portfolio website. It features a bilingual chatbot to assist visitors with navigation and project inquiries. Built with Django, the API emphasizes clean architecture and scalability while maintaining simplicity.

Key Features:
- Personal project management system
- Bilingual chatbot (OpenAI-powered)
- Portfolio website integration
- Secure API endpoints
- Performance optimization with Redis
- Async task handling with Celery

## Planning & Design

### Architecture
The backend is structured following Django's MVT pattern with additional layers for:
- API interfaces
- Service layer for business logic
- Cache management
- Task queue processing

### Data Models

```python
class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.JSONField()
    status = models.CharField(max_length=50)
    start_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    github_link = models.URLField(blank=True)
    live_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ChatLog(models.Model):
    query = models.TextField()
    response = models.TextField()
    language = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100)
```

## Technologies

### Core
- Django (Latest)
- Django REST Framework
- PostgreSQL
- Redis + django-redis 5.4.0
- Celery

### Security & Performance
- django-cors-headers
- django-csp
- django-ratelimit
- django-filter

### Cloud & Media
- Cloudinary
- Pillow

### AI & Language
- OpenAI
- langdetect

### Utils
- python-decouple
- dj_database_url
- psycopg2-binary

## Testing

### Manual Testing
- API endpoint verification (Postman)
- Cache performance monitoring
- Task queue validation
- Cross-browser compatibility

### Automated Testing
- Unit tests for models and services
- API endpoint integration tests
- Chatbot response validation
- Cache operation verification

## Deployment

The application is containerized and deployed using Docker, with separate containers for:
- Django application
- PostgreSQL database
- Redis cache
- Celery workers

Environment configuration and deployment scripts are maintained in a separate private repository.

## Credits

- Django Documentation
- Django REST Framework Documentation
- OpenAI API Documentation
- Redis Documentation
- Celery Documentation

[Back to top](#nordic-code-works---backend-api)