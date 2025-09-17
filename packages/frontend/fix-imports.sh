#!/bin/bash

# Fix all @ alias imports in the frontend codebase
# This script replaces @/ imports with relative imports

# Function to calculate relative path
get_relative_path() {
    local from_file="$1"
    local to_path="$2"
    
    # Get directory of the from file
    local from_dir=$(dirname "$from_file")
    
    # If importing from lib or components at root
    if [[ "$to_path" == "@/lib"* ]]; then
        local target_path="${to_path/@\/lib/src/lib}"
    elif [[ "$to_path" == "@/components"* ]]; then
        local target_path="${to_path/@\/components/src/components}"
    else
        return
    fi
    
    # Calculate relative path from from_dir to target_path
    local relative=$(python3 -c "
import os
from_dir = '$from_dir'
target = '$target_path'
# Remove src/ prefix from paths for calculation
from_dir = from_dir.replace('src/', '')
target = target.replace('src/', '')
rel = os.path.relpath(target, from_dir)
if not rel.startswith('.'):
    rel = './' + rel
print(rel)
")
    
    echo "$relative"
}

# Fix imports in components directory
echo "Fixing imports in components..."

# Fix connection-status.tsx
sed -i "" "s|from '@/components/ui/card'|from '../ui/card'|g" src/components/accounts/connection-status.tsx
sed -i "" "s|from '@/components/ui/button'|from '../ui/button'|g" src/components/accounts/connection-status.tsx
sed -i "" "s|from '@/lib/api/accounts'|from '../../lib/api/accounts'|g" src/components/accounts/connection-status.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/accounts/connection-status.tsx

# Fix plaid-link.tsx
sed -i "" "s|from '@/components/ui/button'|from '../ui/button'|g" src/components/plaid/plaid-link.tsx
sed -i "" "s|from '@/components/ui/loading'|from '../ui/loading'|g" src/components/plaid/plaid-link.tsx
sed -i "" "s|from '@/lib/api/accounts'|from '../../lib/api/accounts'|g" src/components/plaid/plaid-link.tsx

# Fix layout components
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/layout/sidebar.tsx
sed -i "" "s|from '@/components/ui/button'|from '../ui/button'|g" src/components/layout/sidebar.tsx

sed -i "" "s|from '@/components/providers/auth-provider'|from '../providers/auth-provider'|g" src/components/layout/header.tsx
sed -i "" "s|from '@/components/ui/button'|from '../ui/button'|g" src/components/layout/header.tsx

# Fix UI components that import utils
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/input.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/select.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/checkbox.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/loading.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/badge.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/modal.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/table.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/tabs.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/tooltip.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/dialog.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/dropdown-menu.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/alert.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/calendar.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/command.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/pagination.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/popover.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/progress.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/separator.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/skeleton.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/slider.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/switch.tsx
sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" src/components/ui/textarea.tsx

# Fix dashboard components
for file in src/components/dashboard/*.tsx; do
    if [ -f "$file" ]; then
        sed -i "" "s|from '@/components/ui/card'|from '../ui/card'|g" "$file"
        sed -i "" "s|from '@/components/ui/button'|from '../ui/button'|g" "$file"
        sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" "$file"
        sed -i "" "s|from '@/lib/api/|from '../../lib/api/|g" "$file"
    fi
done

# Fix chart components
for file in src/components/charts/*.tsx; do
    if [ -f "$file" ]; then
        sed -i "" "s|from '@/components/ui/card'|from '../ui/card'|g" "$file"
        sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" "$file"
    fi
done

# Fix transaction components
for file in src/components/transactions/*.tsx; do
    if [ -f "$file" ]; then
        sed -i "" "s|from '@/components/ui/|from '../ui/|g" "$file"
        sed -i "" "s|from '@/lib/utils'|from '../../lib/utils'|g" "$file"
        sed -i "" "s|from '@/lib/api/|from '../../lib/api/|g" "$file"
    fi
done

# Fix auth components
for file in src/components/auth/*.tsx; do
    if [ -f "$file" ]; then
        sed -i "" "s|from '@/components/providers/auth-provider'|from '../providers/auth-provider'|g" "$file"
        sed -i "" "s|from '@/components/ui/loading'|from '../ui/loading'|g" "$file"
    fi
done

# Fix providers
sed -i "" "s|from '@/components/ui/toast'|from '../ui/toast'|g" src/components/providers/providers.tsx

echo "Import fixes complete!"