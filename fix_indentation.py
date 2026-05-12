import re

with open('streamlit_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation of the elif statement
content = re.sub(r'(\n                    )elif mode == "Manual Data Load":', r'\n\nelif mode == "Manual Data Load":', content)

with open('streamlit_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed indentation")
