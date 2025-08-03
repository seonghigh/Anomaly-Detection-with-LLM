#utils/prompt.py
def load_template(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def build_prompt(template: str, rules: str, data: str) -> str:
    return template.format(rules=rules, data=data)
