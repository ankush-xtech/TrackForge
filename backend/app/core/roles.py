"""
Role hierarchy and permission service — Single Responsibility Principle.

This module is the ONLY place where role logic lives.
All role checks across the app delegate here.

Hierarchy:
    super_admin  →  system-wide god mode
    org_admin    →  organization owner (Project Manager)
    manager      →  team leader
    employee     →  regular worker

Invite rules:
    org_admin  can invite  →  manager, employee
    manager    can invite  →  employee
    employee   can invite  →  nobody
"""

from enum import IntEnum


class Role(IntEnum):
    """
    Roles ordered by power level (higher = more privileged).
    Using IntEnum lets us compare roles with simple < > operators.
    """

    EMPLOYEE = 0
    MANAGER = 1
    ORG_ADMIN = 2
    SUPER_ADMIN = 3

    @classmethod
    def from_str(cls, value: str) -> "Role":
        """Convert a DB string like 'org_admin' to the enum."""
        mapping = {
            "employee": cls.EMPLOYEE,
            "manager": cls.MANAGER,
            "org_admin": cls.ORG_ADMIN,
            "super_admin": cls.SUPER_ADMIN,
        }
        role = mapping.get(value)
        if role is None:
            raise ValueError(f"Unknown role: {value}")
        return role

    def to_str(self) -> str:
        """Convert the enum back to the DB string."""
        return {
            Role.EMPLOYEE: "employee",
            Role.MANAGER: "manager",
            Role.ORG_ADMIN: "org_admin",
            Role.SUPER_ADMIN: "super_admin",
        }[self]

    @property
    def display_name(self) -> str:
        """Human-readable label for the UI."""
        return {
            Role.EMPLOYEE: "Employee",
            Role.MANAGER: "Manager",
            Role.ORG_ADMIN: "Admin",
            Role.SUPER_ADMIN: "Super Admin",
        }[self]


# ── Invite rules ──────────────────────────────────────────────
# Which roles each role is allowed to create/invite.

_INVITE_PERMISSIONS: dict[Role, frozenset[Role]] = {
    Role.SUPER_ADMIN: frozenset({Role.ORG_ADMIN, Role.MANAGER, Role.EMPLOYEE}),
    Role.ORG_ADMIN: frozenset({Role.MANAGER, Role.EMPLOYEE}),
    Role.MANAGER: frozenset({Role.EMPLOYEE}),
    Role.EMPLOYEE: frozenset(),
}


class RoleService:
    """
    Stateless service — all methods are pure functions.
    Open/Closed: extend by adding to the enums/dicts above, not by modifying methods.
    """

    # ── Hierarchy queries ──

    @staticmethod
    def is_at_least(user_role: str, minimum_role: str) -> bool:
        """Check if user_role >= minimum_role in the hierarchy."""
        return Role.from_str(user_role) >= Role.from_str(minimum_role)

    @staticmethod
    def is_above(user_role: str, other_role: str) -> bool:
        """Check if user_role is strictly above other_role."""
        return Role.from_str(user_role) > Role.from_str(other_role)

    # ── Invite checks ──

    @staticmethod
    def can_invite(inviter_role: str, target_role: str) -> bool:
        """Can a user with inviter_role invite someone with target_role?"""
        inviter = Role.from_str(inviter_role)
        target = Role.from_str(target_role)
        return target in _INVITE_PERMISSIONS.get(inviter, frozenset())

    @staticmethod
    def invitable_roles(inviter_role: str) -> list[str]:
        """Return the list of role strings this inviter is allowed to assign."""
        inviter = Role.from_str(inviter_role)
        return [r.to_str() for r in sorted(_INVITE_PERMISSIONS.get(inviter, frozenset()))]

    # ── Feature access ──

    @staticmethod
    def can_view_team_activity(role: str) -> bool:
        return Role.from_str(role) >= Role.MANAGER

    @staticmethod
    def can_view_all_screenshots(role: str) -> bool:
        return Role.from_str(role) >= Role.MANAGER

    @staticmethod
    def can_manage_projects(role: str) -> bool:
        return Role.from_str(role) >= Role.ORG_ADMIN

    @staticmethod
    def can_manage_users(role: str) -> bool:
        """Admin can manage all users; manager can manage employees."""
        return Role.from_str(role) >= Role.MANAGER

    @staticmethod
    def can_view_reports(role: str) -> bool:
        return Role.from_str(role) >= Role.MANAGER

    @staticmethod
    def can_change_role(changer_role: str, target_current_role: str, target_new_role: str) -> bool:
        """
        Can `changer_role` change someone from `target_current_role` to `target_new_role`?
        Rules:
          - You must be strictly above BOTH the current and new role.
          - The new role must be in your invite permissions.
        """
        changer = Role.from_str(changer_role)
        current = Role.from_str(target_current_role)
        new = Role.from_str(target_new_role)
        allowed = _INVITE_PERMISSIONS.get(changer, frozenset())
        return changer > current and new in allowed


# Module-level singleton for convenience
role_service = RoleService()
