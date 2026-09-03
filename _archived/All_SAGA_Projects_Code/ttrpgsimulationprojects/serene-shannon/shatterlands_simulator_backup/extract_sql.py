import os
import ast

def extract_sql_queries(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Attribute) and node.func.attr in ('execute', 'executemany'):
                                if node.args and isinstance(node.args[0], ast.Constant):
                                    sql = node.args[0].value
                                    if isinstance(sql, str):
                                        print(f"--- {file} ---")
                                        print(sql.strip())
                except Exception as e:
                    pass

extract_sql_queries(r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine')
