from uagents import Agent, Context
import os
import aiohttp
import asyncio
from typing import List, Dict
from urllib.parse import quote_plus
from datetime import datetime, timedelta

# Import models from your models.py file
from models import CandidateProfile, JobListingBatch

# 🔗 Replace with actual Recommendation Agent address
RECOMMENDATION_ADDRESS = "agent1q2g24508ufjrlcusjxk7cmg53f7udtu4a49a5e76zfj77x207sj5us5xwt6"

# Initialize Agent for Agentverse
agent = Agent()

class JobBoardAggregator:
    """Aggregates jobs from multiple sources with intelligent filtering"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.max_jobs_per_source = 5
        self.max_jobs_total = 15
        self.days_filter = 14  # Last 14 days
    
    def _is_recent_job(self, date_str: str) -> bool:
        """Check if job was posted in last 14 days"""
        if not date_str:
            return True
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.days_filter)
            
            if 'T' in date_str:
                job_date = datetime.fromisoformat(date_str.split('T')[0])
            else:
                job_date = datetime.fromisoformat(date_str)
            
            return job_date >= cutoff_date
        except:
            return True
    
    def _quick_skill_match(self, job_text: str, skills: List[str]) -> bool:
        """Check if ANY skill matches"""
        job_text_lower = job_text.lower()
        
        for skill in skills[:5]:  # Check top 5 skills
            if skill.lower() in job_text_lower:
                return True
        return False
    
    def _calculate_match_score(self, job_text: str, skills: List[str]) -> float:
        """Calculate match score based on skill overlap"""
        job_text_lower = job_text.lower()
        matches = 0
        total_skills = len(skills[:5])
        
        for i, skill in enumerate(skills[:5]):
            if skill.lower() in job_text_lower:
                # Top 3 skills get higher weight
                weight = 0.25 if i < 3 else 0.15
                matches += weight
        
        return min(matches, 1.0)
    
    async def fetch_adzuna_jobs(self, skills: List[str]) -> List[Dict]:
        """Fetch from Adzuna API"""
        jobs = []
        
        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")
        
        if not app_id or not app_key:
            print("⚠️ Adzuna credentials not found")
            return jobs
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use top skill for search
                skill_query = quote_plus(skills[0] if skills else "software developer")
                url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
                
                params = {
                    'app_id': app_id,
                    'app_key': app_key,
                    'what': skill_query,
                    'results_per_page': 10,
                    'max_days_old': self.days_filter,
                    'sort_by': 'date'
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for job in data.get('results', []):
                            job_text = f"{job.get('title', '')} {job.get('description', '')}"
                            
                            if not self._quick_skill_match(job_text, skills):
                                continue
                            
                            score = self._calculate_match_score(job_text, skills)
                            
                            if score >= 0.15:
                                salary_min = job.get('salary_min', 0)
                                salary_max = job.get('salary_max', 0)
                                salary = f"${salary_min:,.0f}-${salary_max:,.0f}" if salary_min else "Not specified"
                                
                                jobs.append({
                                    'title': job.get('title', 'N/A'),
                                    'company': job.get('company', {}).get('display_name', 'N/A'),
                                    'location': job.get('location', {}).get('display_name', 'Remote'),
                                    'description': job.get('description', 'N/A')[:500],
                                    'url': job.get('redirect_url', 'N/A'),
                                    'salary': salary,
                                    'remote': 'remote' in job_text.lower(),
                                    'source': 'Adzuna',
                                    'match_score': score,
                                    'requirements': []
                                })
                            
                            if len(jobs) >= self.max_jobs_per_source:
                                break
                    else:
                        print(f"Adzuna API error: {response.status}")
        except Exception as e:
            print(f"Adzuna fetch error: {e}")
        
        return jobs
    
    async def fetch_findwork_jobs(self, skills: List[str]) -> List[Dict]:
        """Fetch from FindWork API"""
        jobs = []
        
        api_key = os.getenv("FINDWORK_API_KEY")
        
        if not api_key:
            print("⚠️ FindWork API key not found")
            return jobs
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://findwork.dev/api/jobs/"
                
                headers = {
                    'Authorization': f'Token {api_key}',
                    **self.headers
                }
                
                params = {
                    'search': skills[0] if skills else "developer",
                    'sort_by': 'date'
                }
                
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        for job in results:
                            if not self._is_recent_job(job.get('date_posted')):
                                continue
                            
                            job_text = f"{job.get('role', '')} {job.get('text', '')} {job.get('keywords', '')}"
                            
                            if not self._quick_skill_match(job_text, skills):
                                continue
                            
                            score = self._calculate_match_score(job_text, skills)
                            
                            if score >= 0.15:
                                jobs.append({
                                    'title': job.get('role', 'N/A'),
                                    'company': job.get('company_name', 'N/A'),
                                    'location': job.get('location', 'Remote'),
                                    'description': job.get('text', 'N/A')[:500],
                                    'url': job.get('url', 'N/A'),
                                    'salary': 'Not specified',
                                    'remote': job.get('remote', False),
                                    'source': 'FindWork',
                                    'match_score': score,
                                    'requirements': job.get('keywords', '').split(',')[:5] if job.get('keywords') else []
                                })
                            
                            if len(jobs) >= self.max_jobs_per_source:
                                break
                    else:
                        print(f"FindWork API error: {response.status}")
        except Exception as e:
            print(f"FindWork fetch error: {e}")
        
        return jobs
    
    async def fetch_serpapi_jobs(self, skills: List[str], location: str = "United States") -> List[Dict]:
        """Fetch from Google Jobs via SerpAPI"""
        jobs = []
        
        api_key = os.getenv("SERPAPI_API_KEY")
        
        if not api_key:
            print("⚠️ SerpAPI key not found")
            return jobs
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://serpapi.com/search"
                
                search_query = " OR ".join(skills[:2]) + " jobs"
                
                params = {
                    'engine': 'google_jobs',
                    'q': search_query,
                    'location': location,
                    'api_key': api_key,
                    'num': 10
                }
                
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for job in data.get('jobs_results', []):
                            job_text = f"{job.get('title', '')} {job.get('description', '')}"
                            
                            if not self._quick_skill_match(job_text, skills):
                                continue
                            
                            score = self._calculate_match_score(job_text, skills)
                            
                            if score >= 0.15:
                                salary = "Not specified"
                                extensions = job.get('detected_extensions', {})
                                if extensions.get('salary'):
                                    salary = extensions['salary']
                                
                                jobs.append({
                                    'title': job.get('title', 'N/A'),
                                    'company': job.get('company_name', 'N/A'),
                                    'location': job.get('location', 'Remote'),
                                    'description': job.get('description', 'N/A')[:500],
                                    'url': job.get('share_link', job.get('apply_link', 'N/A')),
                                    'salary': salary,
                                    'remote': 'remote' in job_text.lower(),
                                    'source': 'Google Jobs',
                                    'match_score': score,
                                    'requirements': []
                                })
                            
                            if len(jobs) >= self.max_jobs_per_source:
                                break
                    else:
                        print(f"SerpAPI error: {response.status}")
        except Exception as e:
            print(f"SerpAPI fetch error: {e}")
        
        return jobs
    
    async def fetch_remotive_jobs(self, skills: List[str]) -> List[Dict]:
        """Fetch from Remotive (free API)"""
        jobs = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://remotive.com/api/remote-jobs"
                
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for job in data.get('jobs', []):
                            if not self._is_recent_job(job.get('publication_date')):
                                continue
                            
                            job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('category', '')}"
                            
                            if not self._quick_skill_match(job_text, skills):
                                continue
                            
                            score = self._calculate_match_score(job_text, skills)
                            
                            if score >= 0.15:
                                jobs.append({
                                    'title': job.get('title', 'N/A'),
                                    'company': job.get('company_name', 'N/A'),
                                    'location': job.get('candidate_required_location', 'Remote'),
                                    'description': job.get('description', 'N/A')[:500],
                                    'url': job.get('url', 'N/A'),
                                    'salary': job.get('salary', 'Not specified'),
                                    'remote': True,
                                    'source': 'Remotive',
                                    'match_score': score,
                                    'requirements': []
                                })
                            
                            if len(jobs) >= self.max_jobs_per_source:
                                break
        except Exception as e:
            print(f"Remotive fetch error: {e}")
        
        return jobs
    
    async def aggregate_jobs(self, skills: List[str], location: str = "United States") -> List[Dict]:
        """Fetch from all sources in parallel"""
        
        tasks = [
            self.fetch_adzuna_jobs(skills),
            self.fetch_findwork_jobs(skills),
            self.fetch_serpapi_jobs(skills, location),
            self.fetch_remotive_jobs(skills)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs = []
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
        
        # Remove duplicates based on title + company
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job['title']}-{job['company']}".lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        # Sort by match score
        unique_jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return unique_jobs[:self.max_jobs_total]

@agent.on_message(model=CandidateProfile)
async def discover_jobs(ctx: Context, sender: str, msg: CandidateProfile):
    ctx.logger.info(f"📥 Profile received for: {msg.candidate_id}")
    ctx.logger.info(f"🎯 Skills: {msg.skills[:5]}")
    ctx.logger.info(f"💼 Experience: {msg.experience_years} years")
    
    # Extract location preference
    location = msg.preferences.get('location_preference', 'United States')
    if location == 'flexible':
        location = 'United States'
    
    ctx.logger.info(f"📍 Location: {location}")
    
    # Fetch jobs from all sources
    aggregator = JobBoardAggregator()
    filtered_jobs = await aggregator.aggregate_jobs(msg.skills, location)
    
    ctx.logger.info(f"✅ Found {len(filtered_jobs)} matching jobs")
    
    if not filtered_jobs:
        ctx.logger.warning("⚠️ No matching jobs found, sending empty batch")
        filtered_jobs = [{
            'title': f"{msg.skills[0].title()} Developer Position",
            'company': "Various Companies",
            'requirements': msg.skills[:5],
            'description': "We're currently aggregating job listings matching your profile. Please check back soon!",
            'salary': "Competitive",
            'location': "Remote",
            'remote': True,
            'url': "https://jobmate.ai",
            'match_score': 0.5,
            'source': 'Fallback'
        }]
    
    # Log all jobs
    for i, job in enumerate(filtered_jobs, 1):
        ctx.logger.info(
            f"📤 [{i}/{len(filtered_jobs)}] {job['title']} @ {job['company']} "
            f"(Score: {job['match_score']:.2f}, Source: {job['source']})"
        )
    
    # Create and send batch
    batch = JobListingBatch(
        candidate_id=msg.candidate_id,
        jobs=filtered_jobs,
        total_count=len(filtered_jobs)
    )
    
    try:
        await ctx.send(RECOMMENDATION_ADDRESS, batch)
        ctx.logger.info(f"✅ Sent batch of {len(filtered_jobs)} jobs to Recommendation Agent")
    except Exception as e:
        ctx.logger.error(f"❌ Failed to send batch: {e}")

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("="*70)
    ctx.logger.info("🚀 JOB DISCOVERY AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🌐 Job Sources:")
    ctx.logger.info(f"   • Adzuna (API)")
    ctx.logger.info(f"   • FindWork (API)")
    ctx.logger.info(f"   • Google Jobs via SerpAPI")
    ctx.logger.info(f"   • Remotive (Free)")
    ctx.logger.info(f"⚙️ Settings:")
    ctx.logger.info(f"   • Max jobs per source: 5")
    ctx.logger.info(f"   • Max total jobs: 15")
    ctx.logger.info(f"   • Date filter: Last 14 days")
    ctx.logger.info(f"   • Min match score: 0.15")
    ctx.logger.info(f"📤 Sends to: {RECOMMENDATION_ADDRESS}")
    ctx.logger.info("="*70)
    
    # Check API keys
    ctx.logger.info("\n🔑 Checking API credentials...")
    
    if os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"):
        ctx.logger.info("   ✅ Adzuna configured")
    else:
        ctx.logger.warning("   ⚠️ Adzuna credentials missing")
    
    if os.getenv("FINDWORK_API_KEY"):
        ctx.logger.info("   ✅ FindWork configured")
    else:
        ctx.logger.warning("   ⚠️ FindWork API key missing")
    
    if os.getenv("SERPAPI_KEY"):
        ctx.logger.info("   ✅ SerpAPI configured")
    else:
        ctx.logger.warning("   ⚠️ SerpAPI key missing")
    
    ctx.logger.info("   ✅ Remotive (no auth required)\n")

if __name__ == "__main__":
    agent.run()
