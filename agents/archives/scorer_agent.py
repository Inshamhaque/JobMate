from uagents import Agent, Context, Model
import os
from config.agent_addresses import RECOMMENDER_ADDRESS

# Data Models - MUST MATCH Job Discovery Agent exactly
class JobListing(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    requirements: list
    description: str
    salary_range: str
    location: str
    remote: bool
    source_url: str  # Added - matches discovery agent
    match_score: float  # Added - matches discovery agent

class MatchScore(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    match_score: float
    reasoning: str
    skill_gaps: list
    strengths: list
    salary_range: str
    location: str
    remote: bool
    source_url: str  # Include for recommender

# Initialize Agent
scorer_agent = Agent(
    name="Compatibility Scorer Agent",
    port=8004,
    seed="scorer_seed_abc",
    endpoint=["http://localhost:8004/submit"]
)

# Store candidate profiles (in-memory cache)
candidate_profiles = {}

def calculate_compatibility_score(job: JobListing, candidate_skills: list = None) -> dict:
    """
    Calculate enhanced compatibility score
    Uses pre-calculated match_score from discovery agent + additional factors
    """
    
    # Use mock skills if not provided (fallback)
    if not candidate_skills:
        candidate_skills = ["python", "django", "aws", "docker", "machine learning"]
    
    # Start with discovery agent's match score (already 0-1.0)
    base_score = job.match_score * 100  # Convert to percentage
    
    # Additional scoring factors
    matching_skills = []
    missing_skills = []
    
    if job.requirements:
        matching_skills = [
            skill for skill in job.requirements 
            if any(cs.lower() in skill.lower() or skill.lower() in cs.lower() 
                   for cs in candidate_skills)
        ]
        missing_skills = [
            skill for skill in job.requirements 
            if skill not in matching_skills
        ]
    
    # Boost score based on requirements match
    if job.requirements:
        req_match_boost = (len(matching_skills) / len(job.requirements)) * 10
        base_score = min(base_score + req_match_boost, 100)
    
    # Remote work bonus
    if job.remote:
        base_score = min(base_score + 5, 100)
    
    # Salary bonus (if specified)
    if job.salary_range and job.salary_range != "Not specified":
        base_score = min(base_score + 3, 100)
    
    # Build reasoning
    reasoning = f'''
🎯 Match Analysis: {job.title} at {job.company}

📊 Overall Compatibility: {base_score:.1f}%

✅ Matching Skills ({len(matching_skills)}/{len(job.requirements) if job.requirements else 0}):
{', '.join(matching_skills[:5]) if matching_skills else 'Skill match detected in description'}

⚠️ Skill Gaps ({len(missing_skills)}):
{', '.join(missing_skills[:5]) if missing_skills else 'None identified'}

💰 Salary: {job.salary_range}
📍 Location: {job.location} {'🏠 (Remote)' if job.remote else '🏢 (On-site)'}
🔗 Source: {job.source_url[:50]}...

💡 Recommendation: {"🌟 Excellent Match!" if base_score >= 80 else "✓ Good Match" if base_score >= 60 else "○ Moderate Match - Consider upskilling"}
    '''
    
    return {
        "score": base_score,
        "reasoning": reasoning.strip(),
        "skill_gaps": missing_skills[:10],  # Limit to top 10
        "strengths": matching_skills[:10]
    }

@scorer_agent.on_message(model=JobListing)
async def score_compatibility(ctx: Context, sender: str, msg: JobListing):
    ctx.logger.info(f"📥 Received: {msg.title} @ {msg.company}")
    ctx.logger.info(f"📊 Pre-score from Discovery: {msg.match_score:.2f}")
    
    # Get candidate profile if cached
    candidate_skills = candidate_profiles.get(msg.candidate_id, None)
    
    # Calculate enhanced compatibility
    analysis = calculate_compatibility_score(msg, candidate_skills)
    
    ctx.logger.info(f"✅ Final Score: {analysis['score']:.1f}%")
    ctx.logger.info(f"💪 Strengths: {len(analysis['strengths'])} | ⚠️ Gaps: {len(analysis['skill_gaps'])}")
    
    # Create match score message
    match_score = MatchScore(
        job_id=msg.job_id,
        candidate_id=msg.candidate_id,
        title=msg.title,
        company=msg.company,
        match_score=analysis["score"],
        reasoning=analysis["reasoning"],
        skill_gaps=analysis["skill_gaps"],
        strengths=analysis["strengths"],
        salary_range=msg.salary_range,
        location=msg.location,
        remote=msg.remote,
        source_url=msg.source_url
    )
    
    # Send to Recommender
    if "PUT_AGENT" not in RECOMMENDER_ADDRESS:
        await ctx.send(RECOMMENDER_ADDRESS, match_score)
        ctx.logger.info(f"📤 Sent to Recommender: {msg.title} (Score: {analysis['score']:.1f}%)")
    else:
        ctx.logger.error("❌ RECOMMENDER_ADDRESS not configured!")

# Optional: Receive candidate profiles for better scoring
class CandidateProfile(Model):
    candidate_id: str
    skills: list
    experience_years: int
    preferences: dict

@scorer_agent.on_message(model=CandidateProfile)
async def cache_profile(ctx: Context, sender: str, msg: CandidateProfile):
    """Cache candidate profile for better scoring"""
    candidate_profiles[msg.candidate_id] = msg.skills
    ctx.logger.info(f"📝 Cached profile for {msg.candidate_id} with {len(msg.skills)} skills")

@scorer_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 COMPATIBILITY SCORER AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8004")
    ctx.logger.info(f"🎯 Scoring Formula:")
    ctx.logger.info(f"   - Base: Discovery agent match score (0-100%)")
    ctx.logger.info(f"   - Boost: +10% for requirements match")
    ctx.logger.info(f"   - Boost: +5% for remote work")
    ctx.logger.info(f"   - Boost: +3% for salary info")
    ctx.logger.info(f"   - Max: 100%")

if __name__ == "__main__":
    scorer_agent.run()