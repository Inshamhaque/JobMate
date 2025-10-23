"""
Shared Models for JobMate Agent System
All agents should import models from this file to ensure schema compatibility
"""

from uagents import Model

class PDFResume(Model):
    """Model for sending PDF resumes"""
    filename: str
    content: str  # base64 encoded PDF content
    candidate_name: str = "Anonymous"

class CandidateProfile(Model):
    """Candidate profile with extracted information"""
    candidate_id: str
    resume_text: str
    skills: list
    top_skills: list
    experience_years: int
    preferences: dict

class RecommendationReport(Model):
    """Job recommendation report for candidate"""
    candidate_id: str
    report: str
    top_matches: list