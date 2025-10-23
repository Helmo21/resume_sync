# Resume Template Guide

## How to Use Custom Templates with Typography Preservation

This guide shows you how to provide DOCX templates and have the system use their typography/formatting to generate different resume variations.

## 📁 Template Directory Structure

Templates are stored in: `/teamplate/`

Current templates:
- `ATS Bold accounting resume.docx` - Bold ATS-friendly accounting template
- `ATS office manager resume.docx` - Office manager template
- `Attorney resume.docx` - Legal profession template
- `Modern bold sales resume.docx` - Sales-focused modern template

## 🎨 How Templates Work

The system can work with templates in **two ways**:

### Method 1: Style-Based Generation (Currently Active)

The system generates resumes from scratch but **adopts the typography** from template analysis:
- Fonts, sizes, and colors
- Section layouts
- Spacing and margins
- Bullet styles

### Method 2: Placeholder-Based Templates (For Custom Templates)

You can create templates with placeholders that get replaced with actual data.

## 📝 Creating Your Own Template

### Step 1: Create a DOCX File

Open Microsoft Word or LibreOffice and create your resume design with:

1. **Typography**: Use your preferred fonts, sizes, colors
2. **Layout**: Set margins, spacing, section headers
3. **Placeholders**: Use these patterns for dynamic content:

```
[Full Name]           → Will be replaced with candidate's name
[Email Address]       → Email
[Phone Number]        → Phone
[LinkedIn URL]        → LinkedIn profile
[Location]            → City/location
[Professional Summary]→ Summary paragraph
```

### Step 2: Structure Sections

Use clear section headers:
```
PROFESSIONAL SUMMARY
[Professional Summary]

WORK EXPERIENCE
[This section will be filled with experience entries]

EDUCATION
[This section will be filled with education entries]

SKILLS
[This section will be filled with categorized skills]
```

### Step 3: Save and Add to System

1. Save your template as `.docx` format
2. Place it in `/teamplate/` directory
3. Name it descriptively (e.g., `Modern Tech Resume.docx`)
4. The system will auto-detect it!

## 🔧 Template Naming Conventions

The system auto-detects template types from filenames:

- `*technical*` or `*engineer*` → Technical template
- `*sales*` → Sales template
- `*accounting*` → Accounting template
- `*attorney*` or `*legal*` → Legal template
- `*manager*` → Management template
- `*modern*` → Modern style
- `*classic*` → Classic style

## 🎯 Using Templates in API

### Generate with Specific Template

```json
POST /api/resumes/generate
{
  "job_url": "https://linkedin.com/jobs/...",
  "template_id": "modern_bold_sales_resume",
  "use_profile_picture": true,
  "additional_links": ["https://github.com/username"]
}
```

### Available Template IDs

Check available templates:
```bash
GET /api/resumes/templates/list
```

Response:
```json
{
  "templates": [
    {
      "id": "modern_bold_sales_resume",
      "name": "Modern Bold Sales Resume",
      "type": "sales",
      "preview_url": "/static/templates/preview/modern_bold_sales.png"
    },
    ...
  ]
}
```

## 🎨 Typography Elements Preserved

When using templates, the system preserves:

✅ **Fonts**: Font family, size, weight (bold/italic)
✅ **Colors**: Text colors, highlighting
✅ **Alignment**: Left, center, right, justified
✅ **Spacing**: Line spacing, paragraph spacing
✅ **Margins**: Page margins, indentation
✅ **Bullets**: Custom bullet styles
✅ **Headers/Footers**: Template headers and footers

## 📋 Example: Creating a Tech Template

### 1. Template DOCX Content:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Full Name]
Software Engineer | [Location]
[Email] | [Phone] | [LinkedIn URL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TECHNICAL SKILLS
────────────────
[Skills will be displayed here in categorized format]

PROFESSIONAL SUMMARY
────────────────────
[Professional Summary]

EXPERIENCE
──────────
[Work experience entries will be listed here]

EDUCATION
─────────
[Education entries will be listed here]
```

### 2. Apply Typography:
- Use `Consolas` or `Fira Code` for tech feel
- Use `#2E86AB` blue for headers
- Use 11pt for body, 16pt for name
- Add subtle borders/lines

### 3. Save as:
`Technical Modern Resume.docx`

### 4. Place in:
`/teamplate/Technical Modern Resume.docx`

## 🚀 Advanced: Dynamic Template Selection

The system can auto-select templates based on job type:

```python
# In backend/app/api/resumes.py
def auto_select_template(job_title: str) -> str:
    job_lower = job_title.lower()

    if 'engineer' in job_lower or 'developer' in job_lower:
        return 'technical_modern_resume'
    elif 'sales' in job_lower or 'account' in job_lower:
        return 'modern_bold_sales_resume'
    elif 'manager' in job_lower:
        return 'ats_office_manager_resume'
    elif 'accountant' in job_lower:
        return 'ats_bold_accounting_resume'
    else:
        return 'modern'  # Default
```

## 📊 Template Management API

### List Templates
```bash
GET /api/resumes/templates/list
```

### Analyze Template
```bash
GET /api/resumes/templates/analyze/{template_id}
```

Returns:
```json
{
  "id": "modern_bold_sales_resume",
  "name": "Modern Bold Sales Resume",
  "type": "sales",
  "analysis": {
    "has_tables": true,
    "has_headers": true,
    "paragraph_count": 45,
    "styles_used": ["Heading 1", "Normal", "Title"],
    "placeholders_detected": 8
  }
}
```

## 💡 Tips for Best Results

1. **Keep it Simple**: Avoid complex layouts (multi-column, text boxes)
2. **Use Standard Styles**: Stick to Word's built-in styles for ATS compatibility
3. **Test Your Template**: Generate a test resume to see how it looks
4. **Provide Placeholders**: Clear placeholders make replacement easier
5. **Consider ATS**: Templates should work well with Applicant Tracking Systems

## 🔍 Debugging Templates

If a template isn't working correctly:

1. **Check Template Analysis**:
   ```bash
   python3 -m app.services.template_handler
   ```

2. **Verify Placeholders**: Ensure placeholders match expected patterns

3. **Test with Sample Data**: Generate a resume and review the output

4. **Check Logs**: Look for template-related errors in backend logs

## 📚 Resources

- Template Examples: `/teamplate/`
- Template Handler Code: `/backend/app/services/template_handler.py`
- Document Generator: `/backend/app/services/document_generator.py`

---

For questions or issues, check the GitHub repository or contact support.
