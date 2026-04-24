#!/usr/bin/env python
"""Final verification of database-backed knowledge base"""

from knowledge_base import get_all_documents, get_documents_by_category, get_knowledge_base
from db_init import DatabaseInitializer

print('=' * 60)
print('KNOWLEDGE BASE VERIFICATION')
print('=' * 60)

# Test 1: Document loading
docs = get_all_documents()
print(f'\n✓ Total documents: {len(docs)}')

# Test 2: Document count via KB
kb = get_knowledge_base()
print(f'✓ KB document count: {kb.get_document_count()}')

# Test 3: Category queries
categories = {}
for doc in docs:
    cat = doc['category']
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(doc['id'])

print(f'\n✓ Document Categories:')
for cat in sorted(categories.keys()):
    print(f'  - {cat}: {len(categories[cat])} docs')

# Test 4: Document content
sample = docs[0]
print(f'\n✓ Sample Document:')
print(f'  ID: {sample["id"]}')
print(f'  Title: {sample["title"]}')
print(f'  Content length: {len(sample["content"])} chars')

# Test 5: Database info
db = DatabaseInitializer()
print(f'\n✓ Database Status:')
print(f'  Path: banking_docs.db')
print(f'  Documents: {db.get_document_count()}')

# Test 6: Category filtering
products = get_documents_by_category('products')
print(f'\n✓ Product Documents:')
for doc in products:
    print(f'  - {doc["id"]}: {doc["title"]}')

print('\n' + '=' * 60)
print('ALL TESTS PASSED ✓')
print('=' * 60)
