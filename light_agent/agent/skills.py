import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


class SkillsLoader:
    def __init__(self, workspace_dir: Path):
        self.skills_dir = workspace_dir / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def list_skills(self) -> List[Dict[str, Any]]:
        skills = []
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    meta = self._get_metadata(skill_file)
                    skills.append(
                        {
                            "name": meta.get("name", skill_dir.name),
                            "description": meta.get("description", ""),
                            "path": str(skill_file),
                            "meta": meta,
                        }
                    )
        return skills

    def load_skill_content(self, name: str) -> Optional[str]:
        skill_file = self.skills_dir / name / "SKILL.md"
        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
            return self._strip_frontmatter(content)
        return None

    def _get_metadata(self, path: Path) -> Dict[str, Any]:
        content = path.read_text(encoding="utf-8")
        if content.startswith("---"):
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                try:
                    return yaml.safe_load(match.group(1)) or {}
                except Exception as e:
                    logger.error(f"Error parsing metadata for {path}: {e}")
        return {}

    def _strip_frontmatter(self, content: str) -> str:
        if content.startswith("---"):
            match = re.match(r"^---\n.*?\n---\n", content, re.DOTALL)
            if match:
                return content[match.end() :].strip()
        return content

    def get_skills_summary(self) -> str:
        skills = self.list_skills()
        if not skills:
            return "No skills available."

        summary = ["Available Skills:"]
        for s in skills:
            summary.append(f"- {s['name']}: {s['description']}")
        return "\n".join(summary)
