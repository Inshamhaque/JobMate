from uagents import Agent, Context, Model
import os
from config.agent_addresses import JOB_DISCOVERY_ADDRESS
from agents.models import CandidateProfile
# Data Models
class EnrichedSkillsProfile(Model):
    candidate_id: str
    original_skills: list
    related_skills: list
    skill_categories: dict
    market_demand: dict
    experience_years: int
    preferences: dict

# CONFIGURATION - UPDATE THIS AFTER RUNNING AGENT 3
# JOB_DISCOVERY_ADDRESS = os.environ.get("JOB_DISCOVERY_ADDRESS")

# Initialize Agent
skills_mapper_agent = Agent(
    name="Skills Mapper Agent",
    port=8002,
    seed="skills_mapper_seed_456",
    endpoint=["http://localhost:8002/submit"]
)

# MeTTa Knowledge Graph (Simulated)
SKILLS_KNOWLEDGE_GRAPH = {
    "python": {
        "related": ["django", "flask", "pandas", "data science", "machine learning"],
        "category": "Programming",
        "demand": "very high",
        "avg_salary": 120000
    },
    "javascript": {
        "related": ["react", "node.js", "vue.js", "typescript"],
        "category": "Programming",
        "demand": "very high",
        "avg_salary": 115000
    },
    "react": {
        "related": ["javascript", "redux", "next.js", "typescript"],
        "category": "Frontend",
        "demand": "very high",
        "avg_salary": 110000
    },
    "machine learning": {
        "related": ["tensorflow", "pytorch", "python", "data science", "ai"],
        "category": "AI/ML",
        "demand": "very high",
        "avg_salary": 145000
    },
    "aws": {
        "related": ["docker", "kubernetes", "terraform", "devops"],
        "category": "Cloud",
        "demand": "very high",
        "avg_salary": 135000
    },
    "docker": {
        "related": ["kubernetes", "aws", "devops", "ci/cd"],
        "category": "DevOps",
        "demand": "very high",
        "avg_salary": 125000
    },
    "sql": {
        "related": ["postgresql", "mysql", "database", "data analysis"],
        "category": "Database",
        "demand": "high",
        "avg_salary": 105000
    },
    "leadership": {
        "related": ["project management", "agile", "team building"],
        "category": "Soft Skills",
        "demand": "very high",
        "avg_salary": 155000
    }
}

def query_metta_knowledge_graph(skills: list) -> dict:
    related_skills = set()
    skill_categories = {}
    market_demand = {}
    
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in SKILLS_KNOWLEDGE_GRAPH:
            info = SKILLS_KNOWLEDGE_GRAPH[skill_lower]
            related_skills.update(info["related"])
            
            category = info["category"]
            if category not in skill_categories:
                skill_categories[category] = []
            skill_categories[category].append(skill)
            
            market_demand[skill] = {
                "demand": info["demand"],
                "avg_salary": info["avg_salary"]
            }
    
    return {
        "related_skills": list(related_skills),
        "skill_categories": skill_categories,
        "market_demand": market_demand
    }

@skills_mapper_agent.on_message(model=CandidateProfile)
async def map_skills(ctx: Context, sender: str, msg: CandidateProfile):
    ctx.logger.info(f"📥 Profile received for: {msg.candidate_id}")
    ctx.logger.info(f"🎯 Original skills: {msg.skills}")
    
    enriched_data = query_metta_knowledge_graph(msg.skills)
    
    ctx.logger.info(f"✅ Found {len(enriched_data['related_skills'])} related skills")
    
    enriched_profile = EnrichedSkillsProfile(
        candidate_id=msg.candidate_id,
        original_skills=msg.skills,
        related_skills=enriched_data["related_skills"],
        skill_categories=enriched_data["skill_categories"],
        market_demand=enriched_data["market_demand"],
        experience_years=msg.experience_years,
        preferences=msg.preferences
    )
    
    if "PUT_AGENT" not in JOB_DISCOVERY_ADDRESS:
        await ctx.send(JOB_DISCOVERY_ADDRESS, enriched_profile)
        ctx.logger.info(f"📤 Enriched profile sent to Job Discovery")
    else:
        ctx.logger.error("❌ JOB_DISCOVERY_ADDRESS not configured!")

@skills_mapper_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 SKILLS MAPPER AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8002")

if __name__ == "__main__":
    skills_mapper_agent.run()