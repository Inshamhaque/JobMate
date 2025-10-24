from uagents import Agent, Context, Model
import os
from config.agent_addresses import SCORER_ADDRESS
from dotenv import load_dotenv
import json
import aiohttp
import asyncio
from typing import List, Dict
from urllib.parse import quote_plus
from datetime import datetime, timedelta

load_dotenv()

# Data Models
class EnrichedSkillsProfile(Model):
    candidate_id: str
    original_skills: list
    related_skills: list
    skill_categories: dict
    market_demand: dict
    experience_years: int
    preferences: dict

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
    source_url: str
    match_score: float

# Initialize Agent
job_discovery_agent = Agent(
    name="Job Discovery Agent",
    port=8003,
    seed="job_discovery_seed_789",
    endpoint=["http://localhost:8003/submit"]
)

class JobBoardAggregator:
    """Aggregates jobs from multiple free sources with smart filtering"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.max_jobs_total = 12  # Hard limit
        self.days_filter = 7  # Only last 7 days
    
    def _is_recent_job(self, date_str: str) -> bool:
        """Check if job was posted in last 7 days"""
        if not date_str:
            return True  # Include if no date info
        
        try:
            # Handle different date formats
            cutoff_date = datetime.now() - timedelta(days=self.days_filter)
            
            # Common formats: "2025-10-20", "2025-10-20T10:30:00Z"
            if 'T' in date_str:
                job_date = datetime.fromisoformat(date_str.split('T')[0])
            else:
                job_date = datetime.fromisoformat(date_str)
            
            return job_date >= cutoff_date
        except:
            return True  # Include if parsing fails
    
    def _quick_skill_match(self, job_text: str, top_skills: List[str]) -> bool:
        """Fast pre-filter: Check if ANY top skill matches"""
        job_text_lower = job_text.lower()
        
        # Must match at least 1 of top 3 skills
        for skill in top_skills[:3]:
            if skill.lower() in job_text_lower:
                return True
        return False
    
    def _calculate_match_score(self, job_text: str, all_skills: List[str]) -> float:
        """Quick match scoring without LLM"""
        job_text_lower = job_text.lower()
        matches = 0
        
        # Top 3 skills worth more
        for i, skill in enumerate(all_skills[:5]):
            if skill.lower() in job_text_lower:
                weight = 0.3 if i < 3 else 0.1  # Top 3 get higher weight
                matches += weight
        
        return min(matches, 1.0)  # Cap at 1.0
    
    async def fetch_remotive_jobs(self, top_skills: List[str], all_skills: List[str]) -> List[Dict]:
        """Fetch from Remotive with pre-filtering"""
        jobs = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://remotive.com/api/remote-jobs"
                
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        all_jobs = data.get('jobs', [])
                        
                        for job in all_jobs:
                            # Date filter
                            if not self._is_recent_job(job.get('publication_date')):
                                continue
                            
                            # Quick skill match
                            job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('category', '')}"
                            
                            if not self._quick_skill_match(job_text, top_skills):
                                continue
                            
                            # Calculate score
                            score = self._calculate_match_score(job_text, all_skills)
                            
                            if score >= 0.2:  # Minimum threshold
                                jobs.append({
                                    'title': job.get('title', 'N/A'),
                                    'company': job.get('company_name', 'N/A'),
                                    'location': job.get('candidate_required_location', 'Remote'),
                                    'description': job.get('description', 'N/A')[:300],
                                    'url': job.get('url', 'N/A'),
                                    'salary': job.get('salary', 'Not specified'),
                                    'remote': True,
                                    'source': 'Remotive',
                                    'match_score': score,
                                    'requirements': []  # Will be extracted if needed
                                })
                            
                            if len(jobs) >= 5:  # Max per source
                                break
                        
        except Exception as e:
            print(f"Remotive fetch error: {e}")
        
        return jobs
    
    async def fetch_arbeitnow_jobs(self, top_skills: List[str], all_skills: List[str]) -> List[Dict]:
        """Fetch from Arbeitnow with pre-filtering"""
        jobs = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.arbeitnow.com/api/job-board-api"
                
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        all_jobs = data.get('data', [])
                        
                        for job in all_jobs:
                            # Date filter
                            if not self._is_recent_job(job.get('created_at')):
                                continue
                            
                            # Quick skill match
                            job_text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}"
                            
                            if not self._quick_skill_match(job_text, top_skills):
                                continue
                            
                            score = self._calculate_match_score(job_text, all_skills)
                            
                            if score >= 0.2:
                                jobs.append({
                                    'title': job.get('title', 'N/A'),
                                    'company': job.get('company_name', 'N/A'),
                                    'location': job.get('location', 'Remote'),
                                    'description': job.get('description', 'N/A')[:300],
                                    'url': job.get('url', 'N/A'),
                                    'salary': 'Not specified',
                                    'remote': job.get('remote', False),
                                    'source': 'Arbeitnow',
                                    'match_score': score,
                                    'requirements': job.get('tags', [])[:5]
                                })
                            
                            if len(jobs) >= 5:
                                break
        except Exception as e:
            print(f"Arbeitnow fetch error: {e}")
        
        return jobs
    
    async def fetch_adzuna_jobs(self, top_skills: List[str], all_skills: List[str]) -> List[Dict]:
        """Fetch from Adzuna with pre-filtering"""
        jobs = []
        
        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")
        
        if not app_id or not app_key:
            return jobs
        
        try:
            async with aiohttp.ClientSession() as session:
                # Only search with TOP skill to reduce API calls
                skill_query = quote_plus(top_skills[0])
                url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
                
                # Calculate date range (last 7 days)
                max_days_old = self.days_filter
                
                params = {
                    'app_id': app_id,
                    'app_key': app_key,
                    'what': skill_query,
                    'results_per_page': 10,  # Reduced from 20
                    'max_days_old': max_days_old  # Built-in date filter!
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for job in data.get('results', []):
                            job_text = f"{job.get('title', '')} {job.get('description', '')}"
                            
                            # Quick skill match
                            if not self._quick_skill_match(job_text, top_skills):
                                continue
                            
                            score = self._calculate_match_score(job_text, all_skills)
                            
                            if score >= 0.2:
                                jobs.append({
                                    'title': job.get('title', 'N/A'),
                                    'company': job.get('company', {}).get('display_name', 'N/A'),
                                    'location': job.get('location', {}).get('display_name', 'N/A'),
                                    'description': job.get('description', 'N/A')[:300],
                                    'url': job.get('redirect_url', 'N/A'),
                                    'salary': f"${job.get('salary_min', 0):.0f}-${job.get('salary_max', 0):.0f}" if job.get('salary_min') else 'Not specified',
                                    'remote': 'remote' in job.get('description', '').lower(),
                                    'source': 'Adzuna',
                                    'match_score': score,
                                    'requirements': []
                                })
                            
                            if len(jobs) >= 5:
                                break
        except Exception as e:
            print(f"Adzuna fetch error: {e}")
        
        return jobs
    
    async def aggregate_jobs(self, top_skills: List[str], all_skills: List[str]) -> List[Dict]:
        """Fetch from all sources with smart limits"""
        
        # Run all sources in parallel
        tasks = [
            self.fetch_remotive_jobs(top_skills, all_skills),
            self.fetch_arbeitnow_jobs(top_skills, all_skills),
            self.fetch_adzuna_jobs(top_skills, all_skills)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs = []
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
        
        # Sort by match score and take top 12
        all_jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return all_jobs[:self.max_jobs_total]

def build_skill_lists(profile: EnrichedSkillsProfile) -> tuple[List[str], List[str]]:
    """
    Returns (top_skills, all_skills)
    - top_skills: Top 3 for filtering
    - all_skills: Top 5 for scoring
    """
    top_skills = []
    
    # Prioritize high-demand skills
    try:
        sorted_by_demand = sorted(
            profile.market_demand.items(),
            key=lambda x: float(x[1].get('avg_salary', 0)) if isinstance(x[1], dict) else 0,
            reverse=True
        )
        top_skills = [skill for skill, _ in sorted_by_demand[:3]]
    except:
        top_skills = profile.original_skills[:3]
    
    # All skills for scoring (top 5)
    all_skills = list(dict.fromkeys(  # Remove duplicates, preserve order
        top_skills + profile.original_skills[:5]
    ))[:5]
    
    return top_skills, all_skills

def create_job_listing(job_data: Dict, candidate_id: str) -> JobListing:
    """Convert job dict to JobListing model"""
    
    return JobListing(
        job_id=f"{job_data['source']}_{hash(job_data['url'])}_{candidate_id}",
        candidate_id=candidate_id,
        title=job_data['title'],
        company=job_data['company'],
        requirements=job_data.get('requirements', []),
        description=job_data['description'],
        salary_range=job_data['salary'],
        location=job_data['location'],
        remote=job_data['remote'],
        source_url=job_data['url'],
        match_score=job_data['match_score']
    )

@job_discovery_agent.on_message(model=EnrichedSkillsProfile)
async def discover_jobs(ctx: Context, sender: str, msg: EnrichedSkillsProfile):
    ctx.logger.info(f"📥 Enriched profile received: {msg.candidate_id}")
    
    # Extract skills
    top_skills, all_skills = build_skill_lists(msg)
    
    ctx.logger.info(f"🎯 Top Skills (for filtering): {top_skills}")
    ctx.logger.info(f"📊 All Skills (for scoring): {all_skills}")
    ctx.logger.info(f"📅 Date Range: Last 7 days only")
    ctx.logger.info(f"🔢 Max Jobs: 12")
    
    # Fetch pre-filtered jobs
    aggregator = JobBoardAggregator()
    filtered_jobs = await aggregator.aggregate_jobs(top_skills, all_skills)
    
    ctx.logger.info(f"✅ Found {len(filtered_jobs)} pre-filtered jobs")
    
    if not filtered_jobs:
        ctx.logger.warning("⚠️ No matching jobs found")
        return
    
    # Convert to JobListing models
    job_listings = []
    for job_data in filtered_jobs:
        try:
            job_listing = create_job_listing(job_data, msg.candidate_id)
            job_listings.append(job_listing)
            ctx.logger.info(
                f"📋 {job_listing.title} @ {job_listing.company} "
                f"(Score: {job_listing.match_score:.2f}) - {job_listing.source_url[:50]}"
            )
        except Exception as e:
            ctx.logger.error(f"❌ Failed to create listing: {e}")
    
    # Send to Scorer Agent
    for job_listing in job_listings:
        if "PUT_AGENT" not in SCORER_ADDRESS:
            await ctx.send(SCORER_ADDRESS, job_listing)
            ctx.logger.info(f"📤 Sent to Scorer: {job_listing.title}")
        else:
            ctx.logger.error("❌ SCORER_ADDRESS not configured!")
            break
    
    ctx.logger.info(f"✅ Sent {len(job_listings)} jobs to Scorer Agent")

@job_discovery_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 JOB DISCOVERY AGENT STARTED (Optimized Mode)")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8003")
    ctx.logger.info(f"🌐 Sources: Remotive, Arbeitnow, Adzuna")
    ctx.logger.info(f"⚡ Optimizations:")
    ctx.logger.info(f"   - Pre-filtering by top 3 skills")
    ctx.logger.info(f"   - Last 7 days jobs only")
    ctx.logger.info(f"   - Max 12 jobs total (5 per source)")
    ctx.logger.info(f"   - No expensive LLM parsing")
    ctx.logger.info(f"   - Client-side scoring")
    
    # Quick connection test
    try:
        ctx.logger.info("🧪 Testing connections...")
        aggregator = JobBoardAggregator()
        test_jobs = await aggregator.aggregate_jobs(
            ["python", "javascript", "react"],
            ["python", "javascript", "react", "node", "aws"]
        )
        ctx.logger.info(f"✅ Test successful: {len(test_jobs)} jobs retrieved")
    except Exception as e:
        ctx.logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    job_discovery_agent.run()