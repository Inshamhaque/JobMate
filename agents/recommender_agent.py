"""
LangChain-Powered Recommendation Agent with OpenAI - Optimized & Complete
Features:
- Efficient batch processing with local skill matching
- Single AI call for comprehensive personalized report
- Fast execution with smart fallback handling
- Production-ready error handling
"""

from uagents import Agent, Context
from models import JobListingBatch, RecommendationReport
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from collections import Counter
import os
from config.agent_addresses import CANDIDATE_AGENT_ADDRESS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

agent = Agent()

llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY,
    max_retries=2,
    request_timeout=30
)

def analyze_skill_match_local(job: dict, candidate_skills: list) -> dict:
    """
    Fast local skill analysis without AI calls.
    Matches candidate skills against job requirements.
    """
    job_requirements = job.get('requirements', [])
    job_description = job.get('description', '').lower()
    
    matching_skills = []
    missing_skills = []
    
    for skill in candidate_skills:
        skill_lower = skill.lower()
        if any(skill_lower in req.lower() or req.lower() in skill_lower for req in job_requirements):
            matching_skills.append(skill)
        elif skill_lower in job_description:
            matching_skills.append(skill)
    
    for req in job_requirements[:8]: 
        req_lower = req.lower()
        if not any(skill.lower() in req_lower or req_lower in skill.lower() for skill in candidate_skills):
            missing_skills.append(req)
    
    total_skills = len(matching_skills) + len(missing_skills)
    if total_skills > 0:
        skill_match_pct = (len(matching_skills) / total_skills) * 100
    else:
        skill_match_pct = 50 
    
    return {
        'matching_skills': matching_skills[:8],
        'missing_skills': missing_skills[:5],
        'skill_match_percentage': round(skill_match_pct, 1)
    }


def calculate_readiness_score_local(
    skill_analysis: dict, 
    experience_years: int, 
    job: dict
) -> dict:
    """
    Calculate application readiness score locally.
    Fast scoring algorithm without AI.
    """
    score = 0
    reasons = []
    
    skill_pct = skill_analysis['skill_match_percentage']
    if skill_pct >= 80:
        score += 50
        reasons.append(f"Excellent skill match ({skill_pct}%)")
    elif skill_pct >= 60:
        score += 35
        reasons.append(f"Good skill match ({skill_pct}%)")
    elif skill_pct >= 40:
        score += 20
        reasons.append(f"Moderate skill match ({skill_pct}%)")
    else:
        score += 10
        reasons.append(f"Foundational skills present")
    
    missing_count = len(skill_analysis['missing_skills'])
    if missing_count == 0:
        score += 20
        reasons.append("All key skills present")
    elif missing_count <= 2:
        score += 15
        reasons.append("Minor skill gaps only")
    elif missing_count <= 4:
        score += 10
        reasons.append("Some upskilling recommended")
    else:
        score += 5
        reasons.append("Several skills to develop")
    
    if experience_years >= 5:
        score += 20
        reasons.append(f"Strong experience ({experience_years}+ years)")
    elif experience_years >= 3:
        score += 15
        reasons.append(f"Solid experience ({experience_years} years)")
    elif experience_years >= 1:
        score += 10
        reasons.append(f"{experience_years} year(s) experience")
    else:
        score += 5
        reasons.append("Entry-level position")
    
    if job.get('remote', False):
        score += 5
        reasons.append("Remote-friendly opportunity")
    
    if job.get('salary', 'Not specified') != 'Not specified':
        score += 5
        reasons.append("Transparent compensation")
    
    if score >= 80:
        level = "Apply Immediately"
        recommendation = "🎯 You're an excellent match!"
    elif score >= 65:
        level = "Ready to Apply"
        recommendation = "✅ Strong candidate, customize your application"
    elif score >= 50:
        level = "Apply with Preparation"
        recommendation = "📚 Consider upskilling or emphasize transferable skills"
    else:
        level = "Develop Skills First"
        recommendation = "⏳ Build foundations before applying"
    
    return {
        'score': min(score, 100),  # Cap at 100
        'level': level,
        'recommendation': recommendation,
        'reasons': reasons[:4]  # Top 4 reasons
    }


COMPREHENSIVE_REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert career advisor and technical recruiter creating a comprehensive, personalized job search report.

Your task: Analyze all job opportunities together and create ONE cohesive, actionable report that helps the candidate succeed.

Writing style:
- Encouraging yet realistic
- Specific and actionable
- Strategic and insightful
- Professional yet warm
- Use second person ("you", "your")

Format requirements:
- Use markdown headers (##, ###)
- Use emojis strategically for visual appeal
- Bold important terms and numbers
- Create clear, scannable sections
- Total length: 800-1200 words"""),
    
    ("human", """Create a comprehensive job search report for this candidate:

# CANDIDATE PROFILE
- Experience Level: {experience_years} years
- Skills: {candidate_skills}

# JOB OPPORTUNITIES ANALYZED
{job_analyses}

# AGGREGATE STATISTICS
- Total Jobs Reviewed: {total_jobs}
- Average Readiness Score: {avg_readiness}/100
- Jobs Ready to Apply Now: {ready_count}
- Remote Opportunities Available: {remote_count}
- Most Common Missing Skills: {common_missing_skills}

# REPORT STRUCTURE

Generate a complete report with these sections:

## 1. EXECUTIVE SUMMARY (3-4 sentences)
Provide an overall assessment of the candidate's position in the current job market and immediate opportunities.

## 2. TOP 3 STRATEGIC RECOMMENDATIONS
What specific actions should the candidate take in the next 2-4 weeks? Be concrete and prioritized.

## 3. SKILLS DEVELOPMENT ROADMAP
Based on ALL jobs analyzed, identify the TOP 3 most impactful skills to learn.

For each skill provide:
- **Why it matters**: Which jobs require it and how it increases opportunities
- **Learning timeline**: Realistic estimate (e.g., "2-4 weeks", "6-8 weeks")
- **Best approach**: Recommended learning method
- **Specific resources**: Name 1-2 actual platforms/courses (e.g., "Udemy Python Bootcamp", "FreeCodeCamp", "Official documentation")
- **Validation**: How to demonstrate the skill (portfolio project idea)

## 4. APPLICATION STRATEGY
Provide tactical advice on:
- How to prioritize applications among the ready jobs
- Key points to emphasize in resume/cover letter
- How to address skill gaps strategically
- Company research approach
- Timeline for applications

## 5. CAREER TRAJECTORY INSIGHTS
Analyze:
- Do these roles match the candidate's experience level?
- What growth opportunities exist in these positions?
- What's the next career step after these roles?
- How to position themselves for advancement

## 6. MOTIVATIONAL CLOSING (2-3 sentences)
End with genuine encouragement and confidence-building message.

---

Generate the complete report now:""")
])


async def generate_comprehensive_ai_report(
    job_analyses: list,
    candidate_skills: list,
    experience_years: int,
    ctx: Context
) -> str:
    """
    Generate comprehensive report with single AI call.
    Synthesizes all job data into actionable insights.
    """
    try:
        # job summaries 
        job_summaries = []
        for i, analysis in enumerate(job_analyses[:10], 1):
            job = analysis['job']
            skill_analysis = analysis['skill_analysis']
            readiness = analysis['readiness']
            
            summary = f"""
**Job {i}: {job.get('title', 'N/A')} at {job.get('company', 'N/A')}**
- Location: {job.get('location', 'N/A')} ({'Remote' if job.get('remote') else 'On-site'})
- Salary: {job.get('salary', 'Not specified')}
- Readiness Score: {readiness['score']}/100 ({readiness['level']})
- Skill Match: {skill_analysis['skill_match_percentage']}%
- Matching Skills: {', '.join(skill_analysis['matching_skills'][:5]) if skill_analysis['matching_skills'] else 'Basic alignment'}
- Skills to Develop: {', '.join(skill_analysis['missing_skills'][:3]) if skill_analysis['missing_skills'] else 'None - ready to apply'}
- Application URL: {job.get('url', 'N/A')}
"""
            job_summaries.append(summary.strip())
        
        
        avg_readiness = sum(a['readiness']['score'] for a in job_analyses) / len(job_analyses)
        ready_count = sum(1 for a in job_analyses if a['readiness']['score'] >= 65)
        remote_count = sum(1 for a in job_analyses if a['job'].get('remote', False))
        
        # most common skills
        all_missing_skills = []
        for analysis in job_analyses:
            all_missing_skills.extend(analysis['skill_analysis']['missing_skills'])
        
        skill_counter = Counter(all_missing_skills)
        common_missing = [skill for skill, count in skill_counter.most_common(5)]
        
        skills_text = ', '.join(candidate_skills) if candidate_skills else 'Not specified - general technical background'
        missing_skills_text = ', '.join(common_missing) if common_missing else 'None identified - strong skill coverage'
        
        chain = COMPREHENSIVE_REPORT_PROMPT | llm
        
        ctx.logger.info("🤖 Calling OpenAI for comprehensive report generation...")
        
        response = await chain.ainvoke({
            "experience_years": experience_years,
            "candidate_skills": skills_text,
            "job_analyses": '\n'.join(job_summaries),
            "total_jobs": len(job_analyses),
            "avg_readiness": f"{avg_readiness:.1f}",
            "ready_count": ready_count,
            "remote_count": remote_count,
            "common_missing_skills": missing_skills_text
        })
        
        ctx.logger.info("✅ AI report generated successfully")
        return response.content
    
    except Exception as e:
        ctx.logger.error(f"❌ AI report generation failed: {e}")
        return generate_fallback_report(job_analyses, candidate_skills, experience_years)

# generating fallback report if the main path fails
def generate_fallback_report(
    job_analyses: list, 
    candidate_skills: list, 
    experience_years: int
) -> str:
    """
    Fallback report if AI fails.
    Provides basic but useful information.
    """
    lines = [
        "## 🎯 YOUR JOB MATCHES REPORT",
        "",
        "### Executive Summary",
        f"We've analyzed {len(job_analyses)} job opportunities that match your profile. "
        f"With {experience_years} years of experience, you have several promising opportunities ahead.",
        "",
        "### Key Recommendations",
        "1. **Apply immediately** to jobs with a readiness score of 65 or higher",
        "2. **Customize each application** highlighting your relevant skills and experience",
        "3. **Address skill gaps** by starting online courses or building portfolio projects",
        "",
        "### Skills Development",
        "Focus on developing the most commonly required skills across these positions:",
    ]
    
    # Find common missing skills
    all_missing = []
    for a in job_analyses:
        all_missing.extend(a['skill_analysis']['missing_skills'])
    
    common_skills = Counter(all_missing).most_common(3)
    for skill, count in common_skills:
        lines.append(f"- **{skill}** (required in {count} positions)")
    
    lines.extend([
        "",
        "### Application Strategy",
        "- Start with the highest readiness score jobs",
        "- Research each company before applying",
        "- Tailor your resume to each job's requirements",
        "- Prepare examples demonstrating your skills",
        "",
        "### Next Steps",
        "Review the detailed job breakdown below and start applying today!",
        ""
    ])
    
    return "\n".join(lines)

async def create_optimized_report(
    jobs: list, 
    candidate_skills: list, 
    experience_years: int,
    ctx: Context
) -> str:
    """
    Create comprehensive report with optimized workflow:
    1. Fast local analysis for all jobs
    2. Single AI call for strategic insights
    3. Assemble complete report
    """
    
    if not jobs:
        return """❌ **No jobs found matching your profile.**

**Suggestions:**
• Broaden your search keywords
• Check different job boards
• Try again in a few days as new positions are posted daily
• Consider related job titles or industries"""
    
    
    ctx.logger.info(f"⚡ Running local analysis on {len(jobs)} jobs...")
    
    job_analyses = []
    for job in jobs[:15]:  # Process up to 15 jobs
        skill_analysis = analyze_skill_match_local(job, candidate_skills)
        readiness = calculate_readiness_score_local(skill_analysis, experience_years, job)
        
        job_analyses.append({
            'job': job,
            'skill_analysis': skill_analysis,
            'readiness': readiness
        })
    
    # Sort by readiness score (best matches first)
    job_analyses.sort(key=lambda x: x['readiness']['score'], reverse=True)
    
    top_score = job_analyses[0]['readiness']['score'] if job_analyses else 0
    ctx.logger.info(f"✅ Local analysis complete. Top match score: {top_score}/100")
    
    
    ai_generated_report = await generate_comprehensive_ai_report(
        job_analyses,
        candidate_skills,
        experience_years,
        ctx
    )
    
    
    report_lines = [
        "# 🎯 YOUR PERSONALIZED JOB RECOMMENDATION REPORT",
        "=" * 70,
        "",
        ai_generated_report,
        "",
        "=" * 70,
        "## 📋 DETAILED JOB BREAKDOWN",
        "=" * 70,
        "",
        "*Review each opportunity below with your readiness score and specific insights.*",
        ""
    ]
    
    for i, analysis in enumerate(job_analyses[:10], 1):
        job = analysis['job']
        skill_analysis = analysis['skill_analysis']
        readiness = analysis['readiness']
        
        report_lines.extend([
            f"### {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}",
            "",
            f"**🎯 Readiness Score: {readiness['score']}/100** - *{readiness['level']}*",
            f"> {readiness['recommendation']}",
            "",
            "**📍 Job Details:**",
            f"- **Location:** {job.get('location', 'N/A')} {'🌍 (Remote)' if job.get('remote') else '🏢 (On-site)'}",
            f"- **Salary:** {job.get('salary', 'Not specified')}",
            f"- **Skill Match:** {skill_analysis['skill_match_percentage']}%",
            f"- **Application Link:** [Apply Here]({job.get('url', '#')})",
            ""
        ])
        
        if skill_analysis['matching_skills']:
            skills_str = ', '.join(skill_analysis['matching_skills'][:6])
            report_lines.extend([
                f"**✅ Your Matching Skills ({len(skill_analysis['matching_skills'])}):**",
                f"{skills_str}",
                ""
            ])
        
        if skill_analysis['missing_skills']:
            missing_str = ', '.join(skill_analysis['missing_skills'][:4])
            report_lines.extend([
                f"**⚠️ Skills to Develop ({len(skill_analysis['missing_skills'])}):**",
                f"{missing_str}",
                ""
            ])
        
        report_lines.append("**💡 Why This Match:**")
        for reason in readiness['reasons']:
            report_lines.append(f"- {reason}")
        
        report_lines.extend(["", "---", ""])
    
    
    avg_readiness = sum(a['readiness']['score'] for a in job_analyses) / len(job_analyses)
    ready_count = sum(1 for a in job_analyses if a['readiness']['score'] >= 65)
    remote_count = sum(1 for a in job_analyses if a['job'].get('remote', False))
    
    report_lines.extend([
        "## 📊 SUMMARY STATISTICS",
        "",
        f"- **Average Readiness Score:** {avg_readiness:.1f}/100",
        f"- **Jobs Ready to Apply Now:** {ready_count}/{len(job_analyses)}",
        f"- **Remote Opportunities:** {remote_count}/{len(job_analyses)}",
        f"- **Total Jobs Analyzed:** {len(jobs)}",
        "",
        "=" * 70,
        "",
        "*Report generated using AI-powered analysis. Good luck with your applications!* 🚀",
        ""
    ])
    
    return "\n".join(report_lines)


@agent.on_message(model=JobListingBatch)
async def handle_job_batch(ctx: Context, sender: str, msg: JobListingBatch):
    """
    Handle incoming job batch from Scraper Agent.
    Generate personalized recommendations and send to Candidate Agent.
    """
    
    candidate_id = msg.candidate_id
    jobs = msg.jobs
    total_count = msg.total_count
    
    candidate_skills = getattr(msg, 'candidate_skills', [])
    experience_years = getattr(msg, 'experience_years', 2)
    
    ctx.logger.info("=" * 70)
    ctx.logger.info("📦 JOB BATCH RECEIVED FROM SCRAPER")
    ctx.logger.info("=" * 70)
    ctx.logger.info(f"👤 Candidate ID: {candidate_id[:20]}...")
    ctx.logger.info(f"📊 Total Jobs: {total_count}")
    ctx.logger.info(f"🎯 Candidate Skills: {len(candidate_skills)}")
    ctx.logger.info(f"📈 Experience: {experience_years} years")
    ctx.logger.info(f"⚡ Processing Strategy: Local analysis + Single AI call")
    
    if not jobs:
        ctx.logger.warning("⚠️ Empty job batch received")
        return

    ctx.logger.info(f"📋 Sample jobs:")
    for i, job in enumerate(jobs[:3], 1):
        ctx.logger.info(f"  {i}. {job.get('title', 'N/A')} @ {job.get('company', 'N/A')}")
    if len(jobs) > 3:
        ctx.logger.info(f"  ... and {len(jobs) - 3} more")
    
    ctx.logger.info("🎨 Generating personalized report...")
    report_text = await create_optimized_report(
        jobs, 
        candidate_skills, 
        experience_years, 
        ctx
    )
    
    ctx.logger.info(f"✅ Report generated successfully ({len(report_text)} characters)")
    
    top_titles = [job.get('title', 'N/A') for job in jobs[:5]]
    
    report = RecommendationReport(
        candidate_id=candidate_id,
        report=report_text,
        top_matches=top_titles
    )

    try:
        await ctx.send(CANDIDATE_AGENT_ADDRESS, report)
        ctx.logger.info("✅ Report sent to Candidate Agent successfully")
        ctx.logger.info("=" * 70)
    except Exception as e:
        ctx.logger.error(f"❌ Failed to send report: {e}")

# AGENT main events 

@agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event - log configuration"""
    ctx.logger.info("=" * 70)
    ctx.logger.info("🚀 RECOMMENDATION AGENT STARTED")
    ctx.logger.info("=" * 70)
    ctx.logger.info(f"📍 Agent Address: {ctx.agent.address}")
    ctx.logger.info("")
    ctx.logger.info("✨ Features:")
    ctx.logger.info("   • LangChain + OpenAI GPT-4o-mini")
    ctx.logger.info("   • Fast local skill matching")
    ctx.logger.info("   • Single AI call for comprehensive report")
    ctx.logger.info("   • Batch processing (up to 15 jobs)")
    ctx.logger.info("   • Smart fallback handling")
    ctx.logger.info("   • Personalized career insights")
    ctx.logger.info("")
    ctx.logger.info(f"🎯 Target Candidate Agent: {CANDIDATE_AGENT_ADDRESS}")
    ctx.logger.info("=" * 70)
    
    # Validate API key
    if OPENAI_API_KEY == "your-api-key-here":
        ctx.logger.warning("⚠️  WARNING: OpenAI API key not configured!")
        ctx.logger.warning("    Set OPENAI_API_KEY environment variable")
        ctx.logger.warning("    Report will use fallback mode without AI insights")
    else:
        ctx.logger.info("✅ OpenAI API key configured")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    """Agent shutdown event"""
    ctx.logger.info("👋 Recommendation Agent shutting down...")


if __name__ == "__main__":
    agent.run()