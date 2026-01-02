# Difference Between UserCanReadWriteMixin and UserOwnedResourceMixin

## Summary

Both mixins provide user-based permissions, but they differ in their implementation and use cases:

| Feature | UserCanReadWriteMixin | UserOwnedResourceMixin |
|---------|----------------------|------------------------|
| **Permission Check** | Direct user_id comparison | Delegates to user's permission methods |
| **Use Case** | Simple user-owned resources | Resources that inherit user's permissions |
| **user_id nullable** | Forces False (must have owner) | Can be nullable |
| **Best For** | Notes, documents, posts | Tokens, settings, profiles |

## Detailed Breakdown

### UserCanReadWriteMixin

**Implementation:**
```python
def _can_write(self) -> bool:
    return self.user_id == get_current_user_id()

def _can_read(self) -> bool:
    return self.user_id == get_current_user_id()
```

**Key Characteristics:**
- **Simple ownership check**: Compares `user_id` with current user
- **Forces non-nullable user_id**: Sets `__user_id_nullable__ = False`
- **Direct comparison**: No delegation, just checks if current user is owner
- **Use case**: Resources that belong to a user and only that user should access them

**Example:**
```python
class Note(UserCanReadWriteMixin, BasePermsModel):
    content: Mapped[str] = mapped_column(db.Text)
    # Only the owner can read/write their notes
```

### UserOwnedResourceMixin

**Implementation:**
```python
def _can_write(self) -> bool:
    return self.user._can_write()  # Delegates to user's permission

def _can_read(self) -> bool:
    return self._can_write()

def _can_create(self) -> bool:
    if self.user_id:
        user = User.get_or_404(self.user_id)
        return user._can_write()
    return self._can_write()
```

**Key Characteristics:**
- **Delegates to user**: Calls the user's `_can_write()` method
- **Inherits user permissions**: If user can be modified, their resources can too
- **More flexible**: Can handle complex user permission scenarios
- **Use case**: Resources that are extensions of the user (tokens, settings)

**Example:**
```python
class UserToken(UserOwnedResourceMixin, BasePermsModel):
    token: Mapped[str] = mapped_column(db.String(500))
    # Token permissions follow the user's permissions
```

## Admin Bypass

**Important**: Both mixins benefit from the **admin bypass** built into `BasePermsModel`:

```python
# In BasePermsModel.can_read() and can_write()
if self.is_current_user_admin():
    return True
```

This means **admins can access all resources** regardless of ownership, for both mixins.

## When to Use Each

### Use UserCanReadWriteMixin when:
- ✅ Simple ownership model (user owns resource)
- ✅ Only the owner should access the resource
- ✅ No special permission logic needed
- ✅ Examples: Notes, Documents, Posts, Comments

```python
class BlogPost(UserCanReadWriteMixin, BasePermsModel):
    title: Mapped[str] = mapped_column(db.String(200))
    content: Mapped[str] = mapped_column(db.Text)
    # User writes their posts, only they can edit them
    # Admins can edit any post (via BasePermsModel)
```

### Use UserOwnedResourceMixin when:
- ✅ Resource is an extension of the user
- ✅ Resource inherits user's permissions
- ✅ Permission logic should delegate to user
- ✅ Examples: Tokens, API Keys, User Settings, Profiles

```python
class UserApiKey(UserOwnedResourceMixin, BasePermsModel):
    key: Mapped[str] = mapped_column(db.String(64))
    # If user can be modified, their API keys can too
    # Delegates to user's permission methods
```

### Use Neither (Custom Logic) when:
- ✅ Complex permission rules
- ✅ Multi-level access (viewers, editors, owners)
- ✅ Context-dependent permissions

```python
class Article(HasUserMixin, BasePermsModel):
    published: Mapped[bool] = mapped_column(db.Boolean, default=False)
    
    def _can_read(self) -> bool:
        # Public if published
        if self.published:
            return True
        # Owner and admin can read drafts
        return self.is_current_user_owner() or self.is_current_user_admin()
    
    def _can_write(self) -> bool:
        # Only owner can edit (admin bypass via BasePermsModel)
        return self.is_current_user_owner()
```

## Common Confusion

### "Don't both allow admin access?"

**Yes!** The admin bypass is in `BasePermsModel`, not the mixins. Both mixins benefit from:

```python
# This is in BasePermsModel (both mixins inherit from it)
def can_read(self) -> bool:
    if self.is_current_user_admin():
        return True  # Admin bypass
    return self._execute_permission_check(self._can_read, "read")

def can_write(self) -> bool:
    if self.is_current_user_admin():
        return True  # Admin bypass
    return self._execute_permission_check(self._can_write, "write")
```

The difference is in **what happens for non-admins**:

- **UserCanReadWriteMixin**: Checks `user_id == current_user_id`
- **UserOwnedResourceMixin**: Delegates to `self.user._can_write()`

## Real-World Example

```python
from flask_more_smorest.perms import BasePermsModel, HasUserMixin, User

# Scenario 1: User has custom permissions
class RestrictedUser(User):
    is_suspended: Mapped[bool] = mapped_column(db.Boolean, default=False)
    
    def _can_write(self) -> bool:
        # Suspended users can't write
        return not self.is_suspended

# Option A: UserCanReadWriteMixin
class UserNote(UserCanReadWriteMixin, BasePermsModel):
    content: Mapped[str] = mapped_column(db.Text)
    # Permission: user_id == current_user_id
    # ✅ Simple ownership check
    # ❌ Doesn't respect user's suspension status

# Option B: UserOwnedResourceMixin  
class UserSettings(UserOwnedResourceMixin, BasePermsModel):
    theme: Mapped[str] = mapped_column(db.String(20))
    # Permission: self.user._can_write()
    # ✅ Respects user's suspension status
    # ✅ If user is suspended, their settings can't be modified
```

## Testing the Difference

```python
# Setup
suspended_user = RestrictedUser(email="test@example.com", is_suspended=True)
suspended_user.save()

# Test UserCanReadWriteMixin
note = UserNote(user_id=suspended_user.id, content="Test")
note.save()
# Current user is suspended_user
assert note.can_write() == True  # ❗ True because user_id matches

# Test UserOwnedResourceMixin
settings = UserSettings(user_id=suspended_user.id, theme="dark")
settings.save()
# Current user is suspended_user
assert settings.can_write() == False  # ✅ False because user._can_write() returns False
```

## Conclusion

- **UserCanReadWriteMixin**: Simple ownership (`user_id` check)
- **UserOwnedResourceMixin**: Delegated permissions (calls `user._can_write()`)
- **Both**: Benefit from admin bypass in `BasePermsModel`
- **Choice**: Depends on whether resource should inherit user's permission logic
