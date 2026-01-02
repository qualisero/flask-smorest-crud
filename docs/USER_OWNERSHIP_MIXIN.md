# UserOwnershipMixin: Unified Permission Mixin

## Overview

`UserOwnershipMixin` is a unified mixin for user-owned resources with configurable permission delegation modes.

## Two Modes

### 1. Simple Ownership Mode (Default)

**Configuration**: `__delegate_to_user__ = False` (default)

**Use for**: Simple user-owned resources (notes, posts, comments, documents)

**Example**:
```python
from flask_more_smorest.perms import BasePermsModel, UserOwnershipMixin

class Note(UserOwnershipMixin, BasePermsModel):
    # Uses default: __delegate_to_user__ = False
    content: Mapped[str] = mapped_column(db.Text)
    # Permission: user_id == current_user_id
```

### 2. Delegated Permissions Mode

**Configuration**: `__delegate_to_user__ = True`

**Use for**: Resources that extend the user (tokens, settings, API keys)

**Example**:
```python
from flask_more_smorest.perms import BasePermsModel, UserOwnershipMixin

class UserToken(UserOwnershipMixin, BasePermsModel):
    __delegate_to_user__ = True
    token: Mapped[str] = mapped_column(db.String(500))
    # Permission: delegates to self.user._can_write()
```

## Configuration Options

- **`__delegate_to_user__`**: Set to `True` for delegated permissions, `False` for simple ownership (default: `False`)
- **`__user_id_nullable__`**: Set to `True` to allow nullable user_id (default: `False`)

## Benefits

- **Single Import**: One mixin to learn and use
- **Clear Configuration**: Explicit `__delegate_to_user__` flag
- **Flexible**: Works for both simple and complex use cases
- **Admin Bypass**: Both modes benefit from admin bypass in BasePermsModel

Choose the mode based on whether your resource is **owned by** the user (simple) or **extends** the user (delegated).

