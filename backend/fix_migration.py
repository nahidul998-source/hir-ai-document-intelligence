import re

filepath = r'e:\HIR-ai-document-intelligence\backend\app\infrastructure\database\migrations\versions\81aaa72d2fb3_enforce_global_tenant_isolation.py'
with open(filepath, 'r') as f:
    content = f.read()

# Strip any existing postgresql_using
content = re.sub(r",\s*postgresql_using='tenant_id::(uuid|varchar)'", "", content)

# Now, we process line by line, maintaining state of whether we are inside an op.alter_column block for tenant_id
lines = content.split('\n')
new_lines = []
in_alter_column = False
is_upgrade = False

for line in lines:
    if 'def upgrade()' in line:
        is_upgrade = True
    elif 'def downgrade()' in line:
        is_upgrade = False
        
    if "op.alter_column(" in line and "'tenant_id'" in line:
        in_alter_column = True
    
    if in_alter_column:
        if is_upgrade and 'type_=sa.Uuid()' in line:
            line = line.replace('type_=sa.Uuid()', "type_=sa.Uuid(), postgresql_using='tenant_id::uuid'")
            in_alter_column = False # Assuming type_ is the last line or close to it, or we just reset it here. 
            # But wait, existing_nullable might be next.
        elif not is_upgrade and 'type_=sa.VARCHAR(length=50)' in line:
            line = line.replace('type_=sa.VARCHAR(length=50)', "type_=sa.VARCHAR(length=50), postgresql_using='tenant_id::varchar'")
            in_alter_column = False
            
        # If we see the end of the statement 'existing_nullable=True)'
        if 'existing_nullable' in line:
            in_alter_column = False

    new_lines.append(line)

with open(filepath, 'w') as f:
    f.write('\n'.join(new_lines))
print('Cleaned and fixed migration file.')
