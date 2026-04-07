/**
 * Role hierarchy and permission utilities — frontend mirror of backend RoleService.
 * Single source of truth for all role checks in the UI.
 *
 * Hierarchy (higher number = more power):
 *   employee (0) → manager (1) → org_admin (2) → super_admin (3)
 */

export const ROLES = {
  employee: 0,
  manager: 1,
  org_admin: 2,
  super_admin: 3,
} as const;

export type RoleKey = keyof typeof ROLES;

export const ROLE_LABELS: Record<RoleKey, string> = {
  employee: "Employee",
  manager: "Manager",
  org_admin: "Admin",
  super_admin: "Super Admin",
};

export const ROLE_COLORS: Record<RoleKey, string> = {
  employee: "bg-slate-100 text-slate-700",
  manager: "bg-blue-100 text-blue-700",
  org_admin: "bg-purple-100 text-purple-700",
  super_admin: "bg-red-100 text-red-700",
};

/** Check if userRole >= minimumRole in the hierarchy */
export function isAtLeast(userRole: string, minimumRole: RoleKey): boolean {
  return (ROLES[userRole as RoleKey] ?? -1) >= ROLES[minimumRole];
}

/** Check if userRole is strictly above otherRole */
export function isAbove(userRole: string, otherRole: string): boolean {
  return (ROLES[userRole as RoleKey] ?? -1) > (ROLES[otherRole as RoleKey] ?? -1);
}

/** Sidebar items each role can see */
export function canViewNav(userRole: string, navKey: string): boolean {
  const role = userRole as RoleKey;
  const power = ROLES[role] ?? 0;

  switch (navKey) {
    // Everyone sees these
    case "dashboard":
    case "time-tracking":
    case "settings":
      return true;

    // Manager+ sees these
    case "reports":
    case "activity":
    case "screenshots":
      return power >= ROLES.manager;

    // Manager+ sees Team (they can add employees)
    case "team":
      return power >= ROLES.manager;

    // Admin+ sees Projects
    case "projects":
      return power >= ROLES.org_admin;

    default:
      return true;
  }
}

/** Roles this user can assign when inviting */
export function invitableRoles(userRole: string): RoleKey[] {
  switch (userRole) {
    case "super_admin":
      return ["org_admin", "manager", "employee"];
    case "org_admin":
      return ["manager", "employee"];
    case "manager":
      return ["employee"];
    default:
      return [];
  }
}

/** Can this user invite anyone at all? */
export function canInvite(userRole: string): boolean {
  return invitableRoles(userRole).length > 0;
}
