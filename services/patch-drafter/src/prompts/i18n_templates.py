"""
Multi-language patch draft templates (Q2 Backlog).
Provides Spanish and Japanese variants of the fallback patch recommendation.
"""

FALLBACK_TEMPLATES_ES = {
    "npm": """
## Resumen
Se detectó una vulnerabilidad crítica {cve_id} en `{package_name}` utilizada por este repositorio.

## Ruta de dependencia
{repo_url} → `{package_name}` ({version_range})

## Solución recomendada
Actualice `{package_name}` a la versión `{fix_version}` o superior de inmediato.

## Cambio de código
```json
"dependencies": {{
  "{package_name}": "^{fix_version}"
}}
```

## Versiones afectadas
Todas las versiones anteriores a `{fix_version}` están afectadas.
""",
    "pypi": """
## Resumen
Se detectó una vulnerabilidad crítica {cve_id} en `{package_name}`.

## Solución recomendada
Actualice `{package_name}` a `{fix_version}` en su `requirements.txt`:

```
{package_name}>={fix_version}
```

## Versiones afectadas
Todas las versiones anteriores a `{fix_version}` están afectadas.
""",
}

FALLBACK_TEMPLATES_JA = {
    "npm": """
## 概要
リポジトリで使用されている `{package_name}` に深刻な脆弱性 {cve_id} が検出されました。

## 依存関係パス
{repo_url} → `{package_name}` ({version_range})

## 推奨される対応
`{package_name}` を `{fix_version}` 以降のバージョンに更新してください。

## コード修正
```json
"dependencies": {{
  "{package_name}": "^{fix_version}"
}}
```

## 影響を受けるバージョン
`{fix_version}` より前のすべてのバージョンが影響を受けます。
""",
    "pypi": """
## 概要
`{package_name}` に脆弱性 {cve_id} が検出されました。

## 推奨される対応
`requirements.txt` を以下のように更新してください：

```
{package_name}>={fix_version}
```

## 影響を受けるバージョン
`{fix_version}` より前のすべてのバージョンが影響を受けます。
""",
}

SUPPORTED_LANGUAGES = {
    "en": None,   # Use the default English templates
    "es": FALLBACK_TEMPLATES_ES,
    "ja": FALLBACK_TEMPLATES_JA,
}

def get_localized_fallback(ecosystem: str, language: str = "en", **kwargs) -> str:
    """
    Return a localized fallback patch template.
    Falls back to English if the language/ecosystem combo is not available.
    """
    from .templates import FALLBACK_TEMPLATES as EN_TEMPLATES
    
    templates = SUPPORTED_LANGUAGES.get(language, None) or EN_TEMPLATES
    
    # Fall back to English if the specific language doesn't have this ecosystem
    if ecosystem.lower() not in templates:
        templates = EN_TEMPLATES
    
    template = templates.get(ecosystem.lower(), EN_TEMPLATES.get("npm", ""))
    
    # Supply defaults for Maven-specific params if missing
    if ecosystem.lower() == "maven":
        pkg = kwargs.get("package_name", ":")
        parts = pkg.split(":")
        kwargs.setdefault("group_id", parts[0] if len(parts) > 0 else "com.example")
        kwargs.setdefault("artifact_id", parts[1] if len(parts) > 1 else pkg)
    
    return template.format(**kwargs)
