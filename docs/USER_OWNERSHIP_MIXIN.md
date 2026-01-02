# UserOwnershipMixin: Unified Permission Mixin

## Overview

`UserOwnershipMixin` is a unified mixin for user-owned resources with configurable permission delegation modes. It replaces the previous `UserCanReadWriteMixin` and `UserOwnedResourceMixin` mixins with a single, more flexible implementation.

## Two Modes

### 1. Simple Ownership Mode (Default)

**Configuration**: `__delegate_to_user__ = False` (default)

**Use for**: Simple user-owned resources (notes, posts, comments, documents)

### 2. Delegated Permissions Mode

**Configuration**: `__delegate_to_user__ = True`

**Use for**: Resources that extend the user (tokens, settings, API keys)

## Benefits

- **Single Import**: One mixin to learn and use
- **Clear Configuration**: Explicit `__delegate_to_user__` flag
- **Flexible**: Works for both simple and complex use cases
- **Admin Bypass**: Both modes benefit from admin bypass in BasePermsModel

Choose the mode based on whether your resource is **owned by** the user (simple) or **extends** the user (delegated).
