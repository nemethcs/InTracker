"""Language-aware content for rules sections."""
from typing import Dict


# Language-specific content mappings
LANGUAGE_CONTENT: Dict[str, Dict[str, str]] = {
    "en": {
        "core_workflow_title": "### Development Workflow (MANDATORY)",
        "core_workflow_intro": "**Every agent MUST follow this workflow:**",
        "project_identification": "**Project Identification (first time only):**",
        "project_setup": "**Project Setup (NEW/EXISTING PROJECTS - first time only):**",
        "resume_context": "**Resume Context & Cursor Rules (first time only):**",
        "branch_check": "**Branch Check (MANDATORY for feature work!):**",
        "work_on_todo": "**Work on Next Todo:**",
        "update_todo_status": "**Update Todo Status:**",
        "git_workflow": "**Git Workflow (MANDATORY - Follow this order!):**",
        "critical": "**CRITICAL:**",
        "never": "**NEVER:**",
        "always": "**ALWAYS:**",
    },
    "hu": {
        "core_workflow_title": "### Fejlesztési Munkafolyamat (KÖTELEZŐ)",
        "core_workflow_intro": "**Minden agentnek KÖTELEZŐ ezt a munkafolyamatot követni:**",
        "project_identification": "**Projekt Azonosítás (csak először):**",
        "project_setup": "**Projekt Beállítás (ÚJ/LÉTEZŐ PROJEKTEK - csak először):**",
        "resume_context": "**Resume Context & Cursor Rules (csak először):**",
        "branch_check": "**Branch Ellenőrzés (KÖTELEZŐ feature munkához!):**",
        "work_on_todo": "**Következő Todo Elvégzése:**",
        "update_todo_status": "**Todo Státusz Frissítése:**",
        "git_workflow": "**Git Munkafolyamat (KÖTELEZŐ - Kövesd ezt a sorrendet!):**",
        "critical": "**KRITIKUS:**",
        "never": "**SOHA:**",
        "always": "**MINDIG:**",
    },
}


def get_content(key: str, language: str = "en") -> str:
    """Get language-specific content.
    
    Args:
        key: Content key
        language: Language code ('hu' or 'en')
        
    Returns:
        Content string in the specified language, or English if not found
    """
    lang_dict = LANGUAGE_CONTENT.get(language, LANGUAGE_CONTENT["en"])
    return lang_dict.get(key, LANGUAGE_CONTENT["en"].get(key, key))


def get_section_content(section_name: str, language: str = "en") -> str:
    """Get full section content based on language.
    
    This function generates the complete section content dynamically
    based on the language. For now, it's a placeholder that can be
    extended with full translations.
    
    Args:
        section_name: Name of the section
        language: Language code ('hu' or 'en')
        
    Returns:
        Section content string
    """
    # For now, return English content by default
    # Full translations can be added later
    if language == "hu":
        # Return Hungarian version if available
        # For now, we'll use English with Hungarian key replacements
        pass
    
    # Return English by default
    return ""


def replace_language_placeholders(content: str, language: str = "en") -> str:
    """Replace language placeholders in content with language-specific text.
    
    Args:
        content: Content string with placeholders like {LANG:key}
        language: Language code ('hu' or 'en')
        
    Returns:
        Content with placeholders replaced
    """
    import re
    
    # Pattern to match {LANG:key} placeholders
    pattern = r"\{LANG:(\w+)\}"
    
    def replace_match(match):
        key = match.group(1)
        return get_content(key, language)
    
    return re.sub(pattern, replace_match, content)
