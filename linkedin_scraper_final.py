"""
LinkedIn Profile Scraper
Extracts profile data from LinkedIn using manual input (fallback method)
"""

import json
import time
from typing import Dict, Optional


def manual_input_linkedin_profile() -> Dict:
    """
    Fallback method: Ask user to manually input their LinkedIn profile data.
    This is the most compliant method and works without LinkedIn API access.
    """
    print("\n" + "="*80)
    print("LINKEDIN PROFILE DATA COLLECTION")
    print("="*80)
    print("\nSince we don't have LinkedIn API access, please provide your profile info:")
    print("(Press Enter to skip optional fields)\n")

    profile_data = {
        "full_name": input("Full Name: ").strip(),
        "headline": input("Professional Headline (e.g., 'Software Engineer at Google'): ").strip(),
        "email": input("Email: ").strip(),
        "phone": input("Phone (optional): ").strip() or None,
        "location": input("Location (e.g., 'San Francisco, CA'): ").strip(),
        "linkedin_url": input("LinkedIn Profile URL (optional): ").strip() or None,
        "summary": input("\nProfessional Summary (paste your About section):\n").strip(),
        "experiences": [],
        "education": [],
        "skills": []
    }

    # Collect work experience
    print("\n" + "-"*80)
    print("WORK EXPERIENCE")
    print("-"*80)
    print("Enter your work experiences (press Enter on job title to finish)\n")

    exp_count = 1
    while True:
        print(f"\nExperience #{exp_count}:")
        job_title = input("  Job Title (or Enter to finish): ").strip()
        if not job_title:
            break

        experience = {
            "title": job_title,
            "company": input("  Company Name: ").strip(),
            "location": input("  Location (optional): ").strip() or None,
            "start_date": input("  Start Date (e.g., 'Jan 2020'): ").strip(),
            "end_date": input("  End Date (or 'Present'): ").strip(),
            "description": input("  Description (what did you do? paste all bullets):\n  ").strip()
        }
        profile_data["experiences"].append(experience)
        exp_count += 1

    # Collect education
    print("\n" + "-"*80)
    print("EDUCATION")
    print("-"*80)
    print("Enter your education (press Enter on degree to finish)\n")

    edu_count = 1
    while True:
        print(f"\nEducation #{edu_count}:")
        degree = input("  Degree (e.g., 'BS Computer Science') (or Enter to finish): ").strip()
        if not degree:
            break

        education = {
            "degree": degree,
            "school": input("  School Name: ").strip(),
            "graduation_year": input("  Graduation Year (optional): ").strip() or None,
            "gpa": input("  GPA (optional): ").strip() or None
        }
        profile_data["education"].append(education)
        edu_count += 1

    # Collect skills
    print("\n" + "-"*80)
    print("SKILLS")
    print("-"*80)
    skills_input = input("Enter your skills (comma-separated):\n").strip()
    if skills_input:
        profile_data["skills"] = [s.strip() for s in skills_input.split(",")]

    print("\n✓ Profile data collected successfully!")
    return profile_data


def save_profile_to_json(profile_data: Dict, filename: str = "linkedin_profile.json"):
    """Save profile data to JSON file for reuse."""
    with open(filename, 'w') as f:
        json.dump(profile_data, f, indent=2)
    print(f"\n✓ Profile saved to {filename}")


def load_profile_from_json(filename: str = "linkedin_profile.json") -> Optional[Dict]:
    """Load saved profile data from JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_linkedin_profile() -> Dict:
    """
    Main function to get LinkedIn profile data.
    Tries to load from saved file first, otherwise prompts for manual input.
    """
    print("\n" + "="*80)
    print("STEP 1: GET LINKEDIN PROFILE DATA")
    print("="*80)

    # Check if we have saved profile data
    saved_profile = load_profile_from_json()
    if saved_profile:
        print("\n✓ Found saved LinkedIn profile!")
        print(f"   Name: {saved_profile.get('full_name')}")
        print(f"   Headline: {saved_profile.get('headline')}")

        use_saved = input("\nUse this profile? (y/n): ").strip().lower()
        if use_saved == 'y':
            return saved_profile

    # Manual input
    print("\nNo saved profile found. Let's collect your LinkedIn data.")
    profile_data = manual_input_linkedin_profile()

    # Save for future use
    save_profile = input("\nSave this profile for future use? (y/n): ").strip().lower()
    if save_profile == 'y':
        save_profile_to_json(profile_data)

    return profile_data


if __name__ == "__main__":
    # Test the scraper
    profile = get_linkedin_profile()
    print("\n" + "="*80)
    print("PROFILE DATA:")
    print("="*80)
    print(json.dumps(profile, indent=2))
