PERMISSIONS = [
    ("expense:create", "Allows creating expenses"),
    ("expense:read", "Allows viewing expenses"),
    ("expense:read:all", "Allows viewing all expenses within the tenant"),
    (
        "expense:read:approved",
        "Allows viewing approved expenses for payment processing",
    ),
    ("expense:approve", "Allows approving expenses"),
    ("expense:reject", "Allows rejecting expenses"),
    ("payment:create", "Allows creating payments"),
    ("payment:read", "Allows viewing payments"),
    ("payment:process", "Allows processing and completing payments"),
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
        "payment:process",
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
        "expense:read:approved",
        "payment:create",
        "payment:read",
        "payment:process",
    ],
    "EMPLOYEE": [
        "expense:create",
        "expense:read",
    ],
}
