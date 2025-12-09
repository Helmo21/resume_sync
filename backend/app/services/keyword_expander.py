"""
Keyword Expansion Service
Expands resume keywords with synonyms and variations for better job matching.
"""
from typing import List, Set, Dict, Optional


class KeywordExpander:
    """Expands keywords with job title and technology synonyms"""

    # Job Title Synonyms - maps base titles to variations
    JOB_TITLE_SYNONYMS = {
        "software engineer": ["developer", "programmer", "software developer", "engineer", "coder"],
        "full stack": ["full stack developer", "full-stack engineer", "fullstack developer"],
        "frontend": ["frontend developer", "front-end developer", "ui developer", "react developer", "vue developer", "angular developer"],
        "backend": ["backend developer", "back-end developer", "server developer", "api developer"],
        "devops": ["devops engineer", "sre", "site reliability engineer", "platform engineer", "cloud engineer", "infrastructure engineer"],
        "data scientist": ["ml engineer", "machine learning engineer", "data analyst", "ai engineer", "data engineer"],
        "product manager": ["pm", "product owner", "product lead", "product strategist"],
        "project manager": ["program manager", "delivery manager", "scrum master", "agile coach"],
        "ux designer": ["ui designer", "ux/ui designer", "product designer", "user experience designer"],
        "qa engineer": ["qa", "test engineer", "quality assurance", "sdet", "automation engineer"],
        "security engineer": ["cybersecurity engineer", "infosec engineer", "security analyst", "penetration tester"],
        "mobile developer": ["ios developer", "android developer", "mobile engineer", "app developer"],
        "web developer": ["web engineer", "frontend developer", "backend developer", "full stack developer"],
        "architect": ["solution architect", "software architect", "system architect", "technical architect"],
        "technical lead": ["tech lead", "team lead", "engineering lead", "lead developer", "lead engineer"],
        "engineering manager": ["development manager", "software manager", "technical manager"],
        "cto": ["chief technology officer", "vp engineering", "head of engineering", "technology director"],
        "consultant": ["advisor", "specialist", "expert", "strategist"],
    }

    # Technology & Skills Synonyms
    TECH_SYNONYMS = {
        # Cloud platforms
        "aws": ["amazon web services", "cloud", "ec2", "s3", "lambda"],
        "azure": ["microsoft azure", "cloud", "azure cloud"],
        "gcp": ["google cloud", "google cloud platform", "cloud"],

        # Programming languages
        "python": ["python3", "django", "flask", "fastapi"],
        "javascript": ["js", "node.js", "nodejs", "typescript", "ts"],
        "java": ["spring", "spring boot", "j2ee"],
        "c#": ["csharp", ".net", "dotnet", "asp.net"],
        "go": ["golang"],
        "ruby": ["ruby on rails", "rails", "ror"],
        "php": ["laravel", "symfony", "wordpress"],

        # Frontend frameworks
        "react": ["react.js", "reactjs", "react native"],
        "angular": ["angular.js", "angularjs"],
        "vue": ["vue.js", "vuejs"],
        "svelte": ["sveltejs"],

        # Backend frameworks
        "django": ["python", "rest framework"],
        "flask": ["python"],
        "express": ["express.js", "node", "nodejs"],
        "fastapi": ["python", "async python"],

        # Databases
        "postgresql": ["postgres", "sql", "database", "rdbms"],
        "mysql": ["sql", "database", "mariadb"],
        "mongodb": ["mongo", "nosql", "database"],
        "redis": ["cache", "in-memory database"],
        "elasticsearch": ["elastic", "search", "elk"],

        # DevOps tools
        "docker": ["containers", "containerization"],
        "kubernetes": ["k8s", "container orchestration", "eks", "gke", "aks"],
        "terraform": ["infrastructure as code", "iac"],
        "ansible": ["automation", "configuration management"],
        "jenkins": ["ci/cd", "continuous integration"],
        "github actions": ["ci/cd", "github workflows"],
        "gitlab ci": ["ci/cd", "gitlab pipelines"],

        # Methodologies
        "agile": ["scrum", "kanban", "sprint", "jira"],
        "ci/cd": ["continuous integration", "continuous deployment", "devops"],
        "microservices": ["distributed systems", "service-oriented architecture", "soa"],
        "rest api": ["restful", "api", "web services"],
        "graphql": ["api", "graph api"],

        # Data & ML
        "machine learning": ["ml", "ai", "artificial intelligence", "deep learning"],
        "tensorflow": ["ml", "deep learning"],
        "pytorch": ["ml", "deep learning"],
        "pandas": ["data analysis", "python", "numpy"],
        "spark": ["apache spark", "big data", "pyspark"],

        # Testing
        "pytest": ["python testing", "unit testing"],
        "jest": ["javascript testing", "react testing"],
        "selenium": ["automation testing", "e2e testing"],

        # Other tools
        "git": ["version control", "github", "gitlab", "bitbucket"],
        "linux": ["unix", "ubuntu", "centos", "rhel"],
        "nginx": ["web server", "reverse proxy"],
        "apache": ["httpd", "web server"],
    }

    # Soft Skills Synonyms
    SOFT_SKILL_SYNONYMS = {
        "leadership": ["team lead", "mentoring", "coaching", "management"],
        "communication": ["presentation", "collaboration", "stakeholder management"],
        "problem solving": ["analytical thinking", "troubleshooting", "debugging"],
        "teamwork": ["collaboration", "cross-functional", "team player"],
        "agile": ["scrum", "kanban", "iterative development"],
    }

    @classmethod
    def expand_keywords(cls, keywords: List[str], max_expansion: int = 30) -> List[str]:
        """
        Expand keywords with synonyms and variations.

        Args:
            keywords: Original list of keywords
            max_expansion: Maximum number of expanded keywords to return

        Returns:
            Expanded list of keywords (unique)
        """
        expanded: Set[str] = set()

        # Add original keywords (lowercased)
        for keyword in keywords:
            expanded.add(keyword.lower().strip())

        # Expand each keyword
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()

            # Check job title synonyms
            for base_title, synonyms in cls.JOB_TITLE_SYNONYMS.items():
                if base_title in keyword_lower or keyword_lower in base_title:
                    expanded.add(base_title)
                    expanded.update(synonyms)

            # Check tech synonyms
            for tech, synonyms in cls.TECH_SYNONYMS.items():
                if tech == keyword_lower or keyword_lower == tech:
                    expanded.add(tech)
                    expanded.update(synonyms)

            # Check soft skill synonyms
            for skill, synonyms in cls.SOFT_SKILL_SYNONYMS.items():
                if skill in keyword_lower or keyword_lower in skill:
                    expanded.add(skill)
                    expanded.update(synonyms)

        # Convert to sorted list and limit
        expanded_list = sorted(list(expanded))
        return expanded_list[:max_expansion]

    @classmethod
    def expand_job_titles(cls, job_titles: List[str]) -> List[str]:
        """
        Expand job titles specifically.

        Args:
            job_titles: List of job titles

        Returns:
            Expanded list of job title variations
        """
        expanded: Set[str] = set()

        for title in job_titles:
            title_lower = title.lower().strip()
            expanded.add(title_lower)

            # Find matching synonyms
            for base_title, synonyms in cls.JOB_TITLE_SYNONYMS.items():
                if base_title in title_lower or title_lower in base_title:
                    expanded.add(base_title)
                    expanded.update(synonyms)

        return list(expanded)

    @classmethod
    def expand_technologies(cls, technologies: List[str]) -> List[str]:
        """
        Expand technology/skill keywords specifically.

        Args:
            technologies: List of technologies/skills

        Returns:
            Expanded list of technology variations
        """
        expanded: Set[str] = set()

        for tech in technologies:
            tech_lower = tech.lower().strip()
            expanded.add(tech_lower)

            # Find matching synonyms
            for base_tech, synonyms in cls.TECH_SYNONYMS.items():
                if base_tech == tech_lower:
                    expanded.add(base_tech)
                    expanded.update(synonyms)

        return list(expanded)

    @classmethod
    def get_top_keywords(cls, keywords: List[str], top_n: int = 10) -> List[str]:
        """
        Get top N keywords prioritized by relevance.

        Prioritization:
        1. Job titles (highest priority)
        2. Technologies
        3. Soft skills
        4. Others

        Args:
            keywords: List of keywords to prioritize
            top_n: Number of top keywords to return

        Returns:
            Prioritized list of top keywords
        """
        job_titles = []
        technologies = []
        soft_skills = []
        others = []

        for keyword in keywords:
            keyword_lower = keyword.lower().strip()

            # Classify keyword
            is_job_title = any(base in keyword_lower for base in cls.JOB_TITLE_SYNONYMS.keys())
            is_tech = any(tech == keyword_lower for tech in cls.TECH_SYNONYMS.keys())
            is_soft_skill = any(skill in keyword_lower for skill in cls.SOFT_SKILL_SYNONYMS.keys())

            if is_job_title:
                job_titles.append(keyword)
            elif is_tech:
                technologies.append(keyword)
            elif is_soft_skill:
                soft_skills.append(keyword)
            else:
                others.append(keyword)

        # Combine in priority order
        prioritized = job_titles + technologies + soft_skills + others
        return prioritized[:top_n]

    @classmethod
    def generate_search_queries(cls, analysis_data: Dict) -> List[Dict]:
        """
        Generate multiple search query strategies from resume analysis.

        Creates 4-6 different query approaches to maximize job discovery:
        1. Primary job titles
        2. Technical skills + seniority
        3. Industry + role combination
        4. Broad keyword search
        5. Alternative job titles
        6. Technology stack focused

        Args:
            analysis_data: Resume analysis data with job_titles, technical_skills, etc.

        Returns:
            List of query dictionaries with 'keywords', 'type', and 'description'
        """
        queries = []

        # Extract data from analysis
        job_titles = analysis_data.get('job_titles', [])[:3]
        technical_skills = analysis_data.get('technical_skills', [])[:10]
        soft_skills = analysis_data.get('soft_skills', [])[:5]
        industries = analysis_data.get('industries', [])[:3]
        seniority_level = analysis_data.get('seniority_level', '')
        search_keywords = analysis_data.get('search_keywords', [])[:15]

        # Expand job titles for variations
        if job_titles:
            expanded_titles = cls.expand_job_titles(job_titles)
            primary_titles = expanded_titles[:3]
            alternative_titles = expanded_titles[3:6] if len(expanded_titles) > 3 else []

            # Query 1: Primary job titles (most specific)
            if primary_titles:
                queries.append({
                    'keywords': primary_titles,
                    'type': 'job_title_primary',
                    'description': f'Primary job titles: {", ".join(primary_titles[:3])}'
                })

            # Query 5: Alternative job titles (catch variations)
            if alternative_titles:
                queries.append({
                    'keywords': alternative_titles,
                    'type': 'job_title_alternative',
                    'description': f'Alternative titles: {", ".join(alternative_titles[:3])}'
                })

        # Query 2: Technical skills + seniority level
        if technical_skills:
            tech_keywords = technical_skills[:5]  # Top 5 technical skills
            if seniority_level:
                # Add seniority to each skill for context
                seniority_queries = [f"{seniority_level} {skill}" for skill in tech_keywords[:3]]
                tech_keywords = seniority_queries + tech_keywords[3:5]

            queries.append({
                'keywords': tech_keywords,
                'type': 'technical_skills',
                'description': f'Technical skills{" (" + seniority_level + ")" if seniority_level else ""}: {", ".join(technical_skills[:5])}'
            })

        # Query 3: Industry + role combination
        if industries and job_titles:
            industry_queries = []
            for industry in industries[:2]:
                for title in job_titles[:2]:
                    industry_queries.append(f"{industry} {title}")

            if industry_queries:
                queries.append({
                    'keywords': industry_queries[:4],  # Max 4 combinations
                    'type': 'industry_role',
                    'description': f'Industry + Role: {industries[0]} jobs'
                })

        # Query 4: Broad keyword search (cast wide net)
        if search_keywords:
            # Mix of job titles, skills, and keywords
            broad_keywords = []
            if job_titles:
                broad_keywords.extend(job_titles[:2])
            if technical_skills:
                broad_keywords.extend(technical_skills[:3])
            if soft_skills:
                broad_keywords.extend(soft_skills[:2])

            # Ensure uniqueness
            broad_keywords = list(set(broad_keywords))[:8]

            if broad_keywords:
                queries.append({
                    'keywords': broad_keywords,
                    'type': 'broad_search',
                    'description': f'Broad search: {len(broad_keywords)} keywords'
                })

        # Query 6: Technology stack focused
        if technical_skills and len(technical_skills) >= 3:
            # Expand technologies to catch similar stacks
            expanded_tech = cls.expand_technologies(technical_skills[:5])
            tech_stack = expanded_tech[:6]

            queries.append({
                'keywords': tech_stack,
                'type': 'tech_stack',
                'description': f'Tech stack: {", ".join(technical_skills[:3])}'
            })

        # Ensure we have at least one query
        if not queries:
            # Fallback: use any available keywords
            fallback_keywords = search_keywords[:10] if search_keywords else job_titles[:5]
            if fallback_keywords:
                queries.append({
                    'keywords': fallback_keywords,
                    'type': 'fallback',
                    'description': 'Fallback search'
                })

        return queries

    @classmethod
    def format_query_for_linkedin(cls, keywords: List[str], max_keywords: int = 5) -> str:
        """
        Format keywords into a LinkedIn search query string.

        Uses OR operator to match any of the keywords.

        Args:
            keywords: List of keywords to search for
            max_keywords: Maximum number of keywords to include in query

        Returns:
            Formatted search query string
        """
        # Limit keywords to avoid too long URL
        selected_keywords = keywords[:max_keywords]

        # Clean and quote keywords that contain spaces
        formatted_keywords = []
        for keyword in selected_keywords:
            keyword = keyword.strip()
            if ' ' in keyword:
                # Quote multi-word keywords for exact match
                formatted_keywords.append(f'"{keyword}"')
            else:
                formatted_keywords.append(keyword)

        # Join with OR operator
        return ' OR '.join(formatted_keywords)
