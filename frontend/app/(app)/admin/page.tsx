"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity, BadgeCheck, Loader2, Mail, Plus, Search, Shield, ShieldOff,
  Trash2, UserCog, UserRound, X,
} from "lucide-react";
import { adminCreateUser, adminDeleteUser, adminListUsers, adminUpdateUser, getAllActivity, type ActivityRow, type AdminUser } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, Dialog, Input, Select, useToast } from "@/components/ui/primitives";
import { timeAgo } from "@/lib/utils";
import { useRouter } from "next/navigation";

const ROLES = ["viewer", "field", "analyst", "admin"] as const;
type Role = typeof ROLES[number];

const ROLE_BADGE: Record<Role, "muted" | "info" | "purple" | "critical"> = {
  viewer: "muted",
  field: "info",
  analyst: "purple",
  admin: "critical",
};

const ROLE_LABEL: Record<Role, string> = {
  viewer: "Viewer",
  field: "Field Officer",
  analyst: "Analyst",
  admin: "Admin",
};

export default function AdminPage() {
  const { user } = useAuth();
  const router = useRouter();
  const { push } = useToast();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null);
  const [editTarget, setEditTarget] = useState<AdminUser | null>(null);

  // Create form
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "viewer" });
  const [saving, setSaving] = useState(false);

  // All-users activity log (admin-only scope)
  const [activity, setActivity] = useState<ActivityRow[]>([]);
  const [activityFilter, setActivityFilter] = useState("all");
  const [activityLoading, setActivityLoading] = useState(true);

  const loadActivity = useCallback((email: string | null) => {
    setActivityLoading(true);
    getAllActivity({ user: email ?? undefined, limit: 100 })
      .then((r) => setActivity(r.items))
      .catch((e: Error) => push({ title: "Activity log unavailable", message: e.message, tone: "error" }))
      .finally(() => setActivityLoading(false));
  }, [push]);

  // Redirect non-admins
  useEffect(() => {
    if (user && user.role !== "admin") router.replace("/");
  }, [user, router]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminListUsers();
      setUsers(data);
    } catch (e) {
      push({ title: "Failed to load users", message: e instanceof Error ? e.message : "Unknown error", tone: "error" });
    } finally {
      setLoading(false);
    }
  }, [push]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { loadActivity(activityFilter === "all" ? null : activityFilter); }, [activityFilter, loadActivity]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminCreateUser(form);
      push({ title: "User created", message: `${form.email} has been created as ${form.role}.`, tone: "success" });
      setCreateOpen(false);
      setForm({ name: "", email: "", password: "", role: "viewer" });
      load();
    } catch (err) {
      push({ title: "Create failed", message: err instanceof Error ? err.message : "Error", tone: "error" });
    } finally {
      setSaving(false);
    }
  };

  const handleRoleChange = async (u: AdminUser, role: string) => {
    try {
      await adminUpdateUser(u.id, { role });
      setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, role } : x)));
      push({ title: "Role updated", message: `${u.email} is now ${role}.`, tone: "success" });
    } catch (err) {
      push({ title: "Update failed", message: err instanceof Error ? err.message : "Error", tone: "error" });
    }
  };

  const handleToggleActive = async (u: AdminUser) => {
    const is_active = !u.is_active;
    try {
      await adminUpdateUser(u.id, { is_active });
      setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active } : x)));
      push({ title: is_active ? "User activated" : "User deactivated", message: u.email, tone: "info" });
    } catch (err) {
      push({ title: "Update failed", message: err instanceof Error ? err.message : "Error", tone: "error" });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setSaving(true);
    try {
      await adminDeleteUser(deleteTarget.id);
      setUsers((prev) => prev.filter((x) => x.id !== deleteTarget.id));
      push({ title: "User deleted", message: `${deleteTarget.email} removed.`, tone: "info" });
      setDeleteTarget(null);
    } catch (err) {
      push({ title: "Delete failed", message: err instanceof Error ? err.message : "Error", tone: "error" });
    } finally {
      setSaving(false);
    }
  };

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.role.toLowerCase().includes(search.toLowerCase())
  );

  if (!user || user.role !== "admin") return null;

  const initials = (name: string) =>
    name.split(/\s+/).map((p) => p[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-primary flex items-center gap-2">
            <UserCog className="h-5 w-5 text-accent" /> Admin Panel
          </h1>
          <p className="text-xs text-muted">Manage users, roles, and access control</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" /> Create User
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {ROLES.map((r) => (
          <Card key={r}>
            <CardBody className="flex items-center gap-3 py-3">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-lg"
                style={{ background: r === "admin" ? "rgba(220,38,38,0.15)" : r === "analyst" ? "rgba(124,58,237,0.15)" : r === "field" ? "rgba(37,99,235,0.15)" : "rgba(100,116,139,0.15)" }}
              >
                <Shield className="h-4 w-4" style={{ color: r === "admin" ? "#dc2626" : r === "analyst" ? "#7c3aed" : r === "field" ? "#2563eb" : "#64748b" }} />
              </div>
              <div>
                <p className="text-xl font-bold text-primary">{users.filter((u) => u.role === r).length}</p>
                <p className="text-[10px] uppercase tracking-wider text-muted">{ROLE_LABEL[r]}s</p>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Search + table */}
      <Card>
        <CardHeader>
          <CardTitle>All Users ({filtered.length})</CardTitle>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name, email, role..."
              className="h-8 w-52 pl-8 text-xs"
            />
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-base-border/50 bg-base-panel/50">
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted">User</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted">Role</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted">Joined</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-10 text-center text-xs text-muted">No users found.</td>
                    </tr>
                  )}
                  {filtered.map((u) => (
                    <tr key={u.id} className="border-b border-base-border/30 transition-colors hover:bg-base-raised/30">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <span
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
                            style={{ background: u.id === user.id ? "linear-gradient(135deg,#0284c7,#7c3aed)" : "rgba(100,116,139,0.4)" }}
                          >
                            {initials(u.name)}
                          </span>
                          <div>
                            <p className="text-xs font-medium text-primary">
                              {u.name}
                              {u.id === user.id && <span className="ml-1.5 text-[9px] text-accent">(you)</span>}
                            </p>
                            <p className="flex items-center gap-1 text-[10px] text-muted">
                              <Mail className="h-2.5 w-2.5" /> {u.email}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u, e.target.value)}
                          className="h-7 w-32 text-xs"
                          disabled={u.id === user.id}
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>{ROLE_LABEL[r]}</option>
                          ))}
                        </Select>
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={u.is_active !== false ? "low" : "muted"}>
                          {u.is_active !== false ? (
                            <><BadgeCheck className="h-3 w-3" /> Active</>
                          ) : (
                            <><ShieldOff className="h-3 w-3" /> Inactive</>
                          )}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1.5">
                          {u.id !== user.id && (
                            <>
                              <button
                                onClick={() => handleToggleActive(u)}
                                title={u.is_active !== false ? "Deactivate" : "Activate"}
                                className="rounded-lg p-1.5 text-muted transition-colors hover:bg-base-raised hover:text-primary"
                              >
                                {u.is_active !== false ? <ShieldOff className="h-3.5 w-3.5" /> : <BadgeCheck className="h-3.5 w-3.5" />}
                              </button>
                              <button
                                onClick={() => setDeleteTarget(u)}
                                title="Delete user"
                                className="rounded-lg p-1.5 text-muted transition-colors hover:bg-critical/10 hover:text-critical"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* All-users activity log (admin all-in-one view) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-accent" /> All Activity ({activity.length})
          </CardTitle>
          <div className="flex items-center gap-2">
            <Select value={activityFilter} onChange={(e) => setActivityFilter(e.target.value)} className="h-8 w-56 text-xs">
              <option value="all">All users</option>
              {users.map((u) => (
                <option key={u.id} value={u.email}>{u.name} ({u.email})</option>
              ))}
            </Select>
            <Button variant="ghost" size="sm" onClick={() => loadActivity(activityFilter === "all" ? null : activityFilter)} disabled={activityLoading}>
              {activityLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Activity className="h-3.5 w-3.5" />}
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {activity.length === 0 ? (
            <p className="py-10 text-center text-xs text-muted">{activityLoading ? "Loading activity..." : "No activity recorded."}</p>
          ) : (
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 border-b border-base-border/70 bg-base-panel text-muted/70">
                  <tr>
                    <th className="px-4 py-2.5 font-medium">Time</th>
                    <th className="px-4 py-2.5 font-medium">User</th>
                    <th className="px-4 py-2.5 font-medium">Action</th>
                    <th className="px-4 py-2.5 font-medium">Entity</th>
                  </tr>
                </thead>
                <tbody>
                  {activity.map((a) => (
                    <tr key={a.id} className="border-b border-base-border/40">
                      <td className="px-4 py-2 text-muted">{a.created_at ? timeAgo(a.created_at) : "—"}</td>
                      <td className="px-4 py-2 text-secondary">{a.user}</td>
                      <td className="px-4 py-2"><span className="font-mono text-sky-400">{a.action}</span></td>
                      <td className="px-4 py-2 text-muted">{a.entity}{a.entity_id ? ` · ${a.entity_id}` : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Create user dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="Create New User">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted">Full Name</label>
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required placeholder="John Doe" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted">Email</label>
            <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required placeholder="john@example.com" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted">Password</label>
            <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required placeholder="min. 6 characters" minLength={6} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted">Role</label>
            <Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </Select>
            <p className="mt-1.5 text-[10px] text-muted/60">
              Viewer → view only · Field → update alerts · Analyst → analyze/ingest · Admin → full access
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserRound className="h-4 w-4" />}
              Create User
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Delete confirm dialog */}
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete User">
        <div className="space-y-4">
          <p className="text-sm text-secondary">
            Are you sure you want to permanently delete <span className="font-semibold text-primary">{deleteTarget?.name}</span>?
          </p>
          <p className="text-xs text-muted">Email: {deleteTarget?.email}</p>
          <p className="rounded-lg border border-critical/30 bg-critical/10 px-3 py-2 text-xs text-critical">
            This action cannot be undone. All data associated with this user will be removed.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Delete Permanently
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
