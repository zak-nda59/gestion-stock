#!/usr/bin/env python3
"""
Script pour adapter automatiquement les requêtes SQL de SQLite vers PostgreSQL/SQLite hybride
"""

import re

def fix_app_py():
    """Corrige app.py pour supporter PostgreSQL et SQLite"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Liste des patterns à remplacer
    replacements = [
        # cursor.execute avec paramètres ?
        (
            r"cursor\.execute\('(SELECT [^']+\?[^']*)'",
            r"cursor.execute(adapt_query('SELECT \1')"
        ),
        (
            r'cursor\.execute\("(SELECT [^"]+\?[^"]*)"',
            r'cursor.execute(adapt_query("SELECT \1")'
        ),
        (
            r"cursor\.execute\('(UPDATE [^']+\?[^']*)'",
            r"cursor.execute(adapt_query('UPDATE \1')"
        ),
        (
            r'cursor\.execute\("(UPDATE [^"]+\?[^"]*)"',
            r'cursor.execute(adapt_query("UPDATE \1")'
        ),
        (
            r"cursor\.execute\('(INSERT [^']+\?[^']*)'",
            r"cursor.execute(adapt_query('INSERT \1')"
        ),
        (
            r'cursor\.execute\("(INSERT [^"]+\?[^"]*)"',
            r'cursor.execute(adapt_query("INSERT \1")'
        ),
        (
            r"cursor\.execute\('(DELETE [^']+\?[^']*)'",
            r"cursor.execute(adapt_query('DELETE \1')"
        ),
        (
            r'cursor\.execute\("(DELETE [^"]+\?[^"]*)"',
            r'cursor.execute(adapt_query("DELETE \1")'
        ),
    ]
    
    # Appliquer les remplacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Remplacer les cursor simples par des cursor avec RealDictCursor pour PostgreSQL
    # Dans toutes les routes
    lines = content.split('\n')
    new_lines = []
    in_route = False
    cursor_line_found = False
    
    for line in lines:
        if '@app.route' in line:
            in_route = True
            cursor_line_found = False
        
        if in_route and 'cursor = conn.cursor()' in line and 'if USE_POSTGRES' not in line:
            # Remplacer par version conditionnelle
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + 'if USE_POSTGRES:')
            new_lines.append(' ' * (indent + 4) + 'cursor = conn.cursor(cursor_factory=RealDictCursor)')
            new_lines.append(' ' * indent + 'else:')
            new_lines.append(' ' * (indent + 4) + 'cursor = conn.cursor()')
            cursor_line_found = True
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Sauvegarder
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ app.py corrigé pour PostgreSQL et SQLite")
    print("📝 Vérifiez le fichier et testez localement avant de déployer")

if __name__ == '__main__':
    try:
        fix_app_py()
    except Exception as e:
        print(f"❌ Erreur: {e}")
