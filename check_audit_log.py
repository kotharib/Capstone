"""Check agent activity audit log"""
import sqlite3

conn = sqlite3.connect('banking_production.db')
cursor = conn.cursor()

logs = cursor.execute('SELECT tool_name, success FROM agent_activity_log ORDER BY rowid DESC LIMIT 20').fetchall()

print('=' * 80)
print('AGENT ACTIVITY LOG (Tool Audit Trail)')
print('=' * 80)
print('{:<35} {:<15}'.format('Tool Name', 'Status'))
print('-' * 80)

for tool, success in logs:
    status = 'SUCCESS' if success else 'FAILED'
    print('{:<35} {:<15}'.format(tool, status))

print('-' * 80)
print('Total tool calls logged: {}'.format(len(logs)))

conn.close()
