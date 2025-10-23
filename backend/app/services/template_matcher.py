"""
Intelligent Template Matcher

This module analyzes job postings and automatically selects the most appropriate
resume templates from the library, with justifications for each choice.
"""

from typing import Dict, List, Tuple, Optional
import re
from ..services.template_handler import get_available_templates


class TemplateMatcher:
    """
    Intelligent system to match job postings with appropriate resume templates.
    """

    # Template type scoring based on job characteristics
    TEMPLATE_JOB_AFFINITY = {
        'sales': {
            'keywords': ['sales', 'account executive', 'business development', 'revenue', 'customer', 'client'],
            'industries': ['sales', 'marketing', 'business development', 'retail'],
            'score_boost': 10
        },
        'accounting': {
            'keywords': ['accountant', 'cpa', 'financial', 'audit', 'bookkeeping', 'tax', 'finance'],
            'industries': ['finance', 'accounting', 'banking'],
            'score_boost': 10
        },
        'legal': {
            'keywords': ['attorney', 'lawyer', 'legal', 'counsel', 'litigation', 'law'],
            'industries': ['legal', 'law', 'compliance'],
            'score_boost': 10
        },
        'management': {
            'keywords': ['manager', 'director', 'supervisor', 'lead', 'head of', 'chief'],
            'industries': ['management', 'operations', 'administration'],
            'score_boost': 8
        },
        'technical': {
            'keywords': ['engineer', 'developer', 'devops', 'software', 'technical', 'architect', 'programmer'],
            'industries': ['technology', 'software', 'it', 'engineering'],
            'score_boost': 10
        }
    }

    def __init__(self):
        """Initialize template matcher."""
        pass

    def analyze_job(self, job_data: Dict) -> Dict[str, any]:
        """
        Analyze job posting to extract key characteristics.

        Args:
            job_data: Job posting data

        Returns:
            Dictionary with job analysis
        """
        title = (job_data.get('title', '') or '').lower()
        description = (job_data.get('description', '') or '').lower()
        company = (job_data.get('company', '') or '').lower()
        full_text = f"{title} {description} {company}"

        analysis = {
            'title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'seniority_level': job_data.get('seniority_level', 'mid'),
            'detected_type': None,
            'keywords_found': [],
            'formality_level': 'professional'  # professional, creative, formal
        }

        # Detect job type based on keywords
        type_scores = {}
        for template_type, config in self.TEMPLATE_JOB_AFFINITY.items():
            score = 0
            keywords_matched = []

            for keyword in config['keywords']:
                if keyword in full_text:
                    score += 1
                    keywords_matched.append(keyword)

            if score > 0:
                type_scores[template_type] = {
                    'score': score,
                    'keywords': keywords_matched
                }

        # Determine primary type
        if type_scores:
            primary_type = max(type_scores.items(), key=lambda x: x[1]['score'])
            analysis['detected_type'] = primary_type[0]
            analysis['keywords_found'] = primary_type[1]['keywords']

        # Detect formality level
        if any(word in full_text for word in ['law', 'legal', 'attorney', 'banking', 'finance']):
            analysis['formality_level'] = 'formal'
        elif any(word in full_text for word in ['creative', 'design', 'marketing', 'startup']):
            analysis['formality_level'] = 'creative'

        return analysis

    def select_best_templates(
        self,
        job_data: Dict,
        num_templates: int = 2
    ) -> List[Dict[str, any]]:
        """
        Select the best templates for a job posting.

        Args:
            job_data: Job posting data
            num_templates: Number of templates to select (default: 2)

        Returns:
            List of selected templates with scores and justifications
        """
        # Get all available custom templates (exclude built-in)
        all_templates = get_available_templates()

        if not all_templates:
            raise ValueError("No custom templates available in /teamplate directory")

        # Analyze the job
        job_analysis = self.analyze_job(job_data)

        # Score each template
        scored_templates = []
        for template in all_templates:
            score, justification = self._score_template(template, job_analysis)
            scored_templates.append({
                'template': template,
                'score': score,
                'justification': justification,
                'job_analysis': job_analysis
            })

        # Sort by score (descending)
        scored_templates.sort(key=lambda x: x['score'], reverse=True)

        # Select top N templates
        selected = scored_templates[:num_templates]

        # If we don't have enough templates with good scores, add variety
        if len(selected) < num_templates and len(scored_templates) > num_templates:
            # Add templates with different types for variety
            used_types = {t['template']['type'] for t in selected}
            for template in scored_templates[num_templates:]:
                if template['template']['type'] not in used_types:
                    selected.append(template)
                    used_types.add(template['template']['type'])
                    if len(selected) >= num_templates:
                        break

        return selected[:num_templates]

    def _score_template(
        self,
        template: Dict,
        job_analysis: Dict
    ) -> Tuple[int, str]:
        """
        Score a template based on how well it matches the job.

        Args:
            template: Template metadata
            job_analysis: Job analysis results

        Returns:
            Tuple of (score, justification)
        """
        score = 0
        justifications = []

        template_type = template.get('type', 'general')
        template_name = template.get('name', '')
        detected_job_type = job_analysis.get('detected_type')

        # Base score - all templates start equal
        score = 50

        # Perfect match: template type matches detected job type
        if detected_job_type and template_type == detected_job_type:
            score += 30
            justifications.append(f"Perfect match for {detected_job_type} role")

        # Partial match: template type is related to job
        elif detected_job_type and template_type in self.TEMPLATE_JOB_AFFINITY:
            affinity = self.TEMPLATE_JOB_AFFINITY.get(template_type, {})
            if detected_job_type in affinity.get('keywords', []):
                score += 15
                justifications.append(f"Good fit for {template_type} positions")

        # Formality level match
        if job_analysis.get('formality_level') == 'formal':
            if 'attorney' in template_name.lower() or 'professional' in template_name.lower():
                score += 10
                justifications.append("Formal design suits professional environment")

        # ATS optimization bonus
        if 'ats' in template_name.lower():
            score += 15
            justifications.append("ATS-optimized for applicant tracking systems")

        # Modern/bold bonus for creative roles
        if job_analysis.get('formality_level') == 'creative':
            if 'modern' in template_name.lower() or 'bold' in template_name.lower():
                score += 10
                justifications.append("Modern design for creative industry")

        # Management template for senior roles
        seniority = job_analysis.get('seniority_level', '').lower()
        if 'manager' in template_type or 'executive' in template_name.lower():
            if any(word in seniority for word in ['senior', 'director', 'manager', 'executive']):
                score += 10
                justifications.append("Executive-level design for senior position")

        # General fallback justification
        if not justifications:
            justifications.append(f"Professional {template_type} design")

        # Create final justification string
        job_title = job_analysis.get('title', 'this position')
        company = job_analysis.get('company', 'the company')

        final_justification = (
            f"**Why this template works for {job_title} at {company}:**\n\n"
            + "\n".join([f"• {j}" for j in justifications])
        )

        return score, final_justification


def select_templates_for_job(job_data: Dict, num_templates: int = 2) -> List[Dict]:
    """
    Convenience function to select best templates for a job.

    Args:
        job_data: Job posting data
        num_templates: Number of templates to select

    Returns:
        List of selected templates with scores and justifications
    """
    matcher = TemplateMatcher()
    return matcher.select_best_templates(job_data, num_templates)


if __name__ == "__main__":
    """Test template matcher"""
    print("="*80)
    print("TEMPLATE MATCHER TEST")
    print("="*80)

    # Test job data
    test_jobs = [
        {
            "title": "DevOps Engineer",
            "company": "Metyis",
            "description": "We are looking for a DevOps engineer with experience in cloud infrastructure, CI/CD, and automation.",
            "seniority_level": "mid-senior"
        },
        {
            "title": "Senior Accountant",
            "company": "KPMG",
            "description": "Looking for a CPA with 5+ years experience in financial reporting and audit.",
            "seniority_level": "senior"
        },
        {
            "title": "Sales Manager",
            "company": "Salesforce",
            "description": "Drive revenue growth and manage enterprise accounts.",
            "seniority_level": "manager"
        }
    ]

    matcher = TemplateMatcher()

    for job in test_jobs:
        print(f"\n{'='*80}")
        print(f"Job: {job['title']} at {job['company']}")
        print(f"{'='*80}")

        # Analyze job
        analysis = matcher.analyze_job(job)
        print(f"\n📊 Job Analysis:")
        print(f"   Detected Type: {analysis['detected_type']}")
        print(f"   Keywords: {', '.join(analysis['keywords_found'])}")
        print(f"   Formality: {analysis['formality_level']}")

        # Select templates
        selected = matcher.select_best_templates(job, num_templates=2)

        print(f"\n✅ Selected {len(selected)} Templates:\n")
        for i, selection in enumerate(selected, 1):
            template = selection['template']
            score = selection['score']
            justification = selection['justification']

            print(f"   {i}. {template['name']}")
            print(f"      Score: {score}/100")
            print(f"      Type: {template['type']}")
            print(f"      {justification}\n")
