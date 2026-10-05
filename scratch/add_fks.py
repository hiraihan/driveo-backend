import os
import re

directory = 'app/modules'
target_tables = {
    'user_id': 'users.id',
    'rental_id': 'rentals.id',
    'vehicle_id': 'vehicles.id',
    'listing_id': 'listings.id',
    'booking_id': 'bookings.id',
    'promo_id': 'promos.id',
}

# Regex to find Column definitions like `user_id = Column(String(36), ...)`
# and we want to inject `ForeignKey("...", ondelete="RESTRICT")` if not already there.

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('models.py') or file == 'checklist_models.py':
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Check if ForeignKey is imported, if not add it
            if 'ForeignKey' not in content:
                content = re.sub(r'from sqlalchemy import (.*?)\n', r'from sqlalchemy import \1, ForeignKey\n', content)
            
            new_content = content
            for col, ref in target_tables.items():
                # We look for something like: user_id = Column(String(36), index=True)
                # We need to handle nullable, index, etc.
                # Just match `col = Column(String(36)` and replace with `col = Column(String(36), ForeignKey("ref", ondelete="RESTRICT")`
                # Only if not already containing ForeignKey
                
                def replacer(match):
                    full = match.group(0)
                    if 'ForeignKey' in full:
                        return full
                    rest = match.group(1)
                    return f'{col} = Column(String(36), ForeignKey("{ref}", ondelete="RESTRICT"){rest})'
                
                pattern = re.compile(rf'{col}\s*=\s*Column\(String\(36\)(.*?)\)', re.DOTALL)
                new_content = pattern.sub(replacer, new_content)
                
            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
