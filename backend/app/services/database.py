from app.services.prompt_templates import (
        init_prompt_templates_table,
        seed_prompt_templates_if_needed,
    )

def init_tables_if_not_exists():
    init_prompt_templates_table()
    seed_prompt_templates_if_needed()
