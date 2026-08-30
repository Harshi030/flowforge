PERMISSIONS = [
    ("expense:create", "Allows creating expenses"),
    ("expense:read", "Allows viewing expenses"),
    ("expense:read:all", "Allows viewing all expenses within the tenant"),
    ("expense:approve", "Allows approving expenses"),
    ("expense:reject", "Allows rejecting expenses"),

    ("payment:create", "Allows creating payments"),
    ("payment:read", "Allows viewing payments"),

    ("user:create", "Allows creating users"),
    ("user:manage", "Allows managing users, including updating and deactivating them"),

    ("role:manage", "Allows managing roles and their permissions"),
    ("audit:read", "Allows viewing audit logs"),
]

ROLE_PERMISSIONS = {
    "ADMIN": [
        "expense:create",
        "expense:read",
        "expense:read:all",
        "expense:approve",
        "expense:reject",
        "payment:create",
        "payment:read",
        "user:create",
        "user:manage",
        "role:manage",
        "audit:read",
    ],

    "MANAGER": [
        "expense:create",
        "expense:read",
        "expense:read:all",
        "expense:approve",
        "expense:reject",
    ],

    "FINANCE": [
        "expense:read",
        "expense:read:all",
        "payment:create",
        "payment:read",
    ],

    "EMPLOYEE": [
        "expense:create",
        "expense:read",
    ],
}