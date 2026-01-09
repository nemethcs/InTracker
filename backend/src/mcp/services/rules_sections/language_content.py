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
        "language_requirement": "**Language Requirement (CRITICAL):** If team language is set, ALWAYS use that language when creating todos, features, and ideas!",
        "language_requirement_detail": "Team language setting determines the language for all InTracker content (todos, features, ideas). If team language is Hungarian (hu), create content in Hungarian. If English (en) or not set, create in English.",
        "language_examples": "Examples: If team language = 'hu': 'Implementálj egy új funkciót' (in Hungarian). If team language = 'en' or not set: 'Implement a new feature' (in English).",
        "todo_language_note": "ALWAYS use team language when creating todo title and description!",
        "feature_language_note": "ALWAYS use team language when creating feature name and description!",
        "idea_language_note": "ALWAYS use team language when creating idea title and description!",
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
        "language_requirement": "**Nyelv Követelmény (KRITIKUS):** Ha a team nyelv beállítva van, MINDIG használd azt a nyelvet todo-k, feature-ök és idea-k létrehozásánál!",
        "language_requirement_detail": "A team nyelv beállítása meghatározza, hogy milyen nyelven kell létrehozni az összes InTracker tartalmat (todo-k, feature-ök, idea-k). Ha a team nyelv magyar (hu), akkor magyarul kell létrehozni. Ha angol (en) vagy nincs beállítva, akkor angolul.",
        "language_examples": "Példák: Ha team nyelv = 'hu': 'Implementálj egy új funkciót' (magyarul). Ha team nyelv = 'en' vagy nincs beállítva: 'Implement a new feature' (angolul).",
        "todo_language_note": "MINDIG használd a team nyelvét a todo cím és leírás létrehozásánál!",
        "feature_language_note": "MINDIG használd a team nyelvét a feature név és leírás létrehozásánál!",
        "idea_language_note": "MINDIG használd a team nyelvét az idea cím és leírás létrehozásánál!",
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
