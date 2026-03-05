#!/usr/bin/env python3
import json
import re
import socket
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

PROFILE_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
DEFAULT_SETTINGS_PATH = Path.home() / ".config" / "aifirst" / "aifirst-ai.json"


def send_request(socket_path: str, payload: dict[str, Any]) -> dict[str, Any]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(socket_path)
        sock.sendall(json.dumps(payload).encode("utf-8"))
        chunks: list[bytes] = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
    raw = b"".join(chunks)
    if not raw:
        raise RuntimeError("No response from assistantd")
    return json.loads(raw.decode("utf-8"))


def default_settings() -> dict[str, Any]:
    return {
        "assistant_permissions": "read_only",
        "default_profile": "local-ollama",
        "profiles": {
            "local-ollama": {
                "provider": "ollama",
                "model": "llama3.2",
                "ollama_base_url": "http://127.0.0.1:11434",
            }
        },
        "timeout_sec": 60,
        "system_prompt": (
            "You are a Linux assistant for an AI-first Fedora distribution. "
            "Prioritize safe, reproducible commands and explain briefly."
        ),
    }


class AssistantGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("tAI Assistant")
        self.geometry("940x680")
        self.settings_path_var = tk.StringVar(value=str(DEFAULT_SETTINGS_PATH))
        self.socket_path_var = tk.StringVar(value="/run/assistantd.sock")
        self.data: dict[str, Any] = default_settings()
        self._build_ui()
        self.load_settings()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(root)
        top.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(top, text="Socket Path").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.socket_path_var, width=45).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Label(top, text="Settings Path").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.settings_path_var, width=45).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(top, text="Reload Settings", command=self.load_settings).pack(side=tk.LEFT)

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.chat_tab = ttk.Frame(notebook)
        self.actions_tab = ttk.Frame(notebook)
        self.settings_tab = ttk.Frame(notebook)
        notebook.add(self.chat_tab, text="Chat")
        notebook.add(self.actions_tab, text="System Actions")
        notebook.add(self.settings_tab, text="Settings")

        self._build_chat_tab()
        self._build_actions_tab()
        self._build_settings_tab()

    def _build_chat_tab(self) -> None:
        frame = self.chat_tab
        top = ttk.Frame(frame, padding=8)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Mode").pack(side=tk.LEFT)
        self.chat_mode = tk.StringVar(value="ask")
        ttk.Combobox(top, textvariable=self.chat_mode, values=["ask", "summarize"], state="readonly", width=14).pack(
            side=tk.LEFT, padx=(6, 16)
        )
        ttk.Label(top, text="Profile").pack(side=tk.LEFT)
        self.chat_profile = tk.StringVar(value="")
        self.chat_profile_combo = ttk.Combobox(top, textvariable=self.chat_profile, values=[], width=30)
        self.chat_profile_combo.pack(side=tk.LEFT, padx=(6, 8))
        ttk.Button(top, text="Send", command=self.send_ai_query).pack(side=tk.LEFT)

        ttk.Label(frame, text="Prompt").pack(anchor=tk.W, padx=8, pady=(4, 0))
        self.chat_prompt = tk.Text(frame, height=10)
        self.chat_prompt.pack(fill=tk.X, padx=8, pady=(0, 8))

        ttk.Label(frame, text="Response").pack(anchor=tk.W, padx=8, pady=(4, 0))
        self.chat_output = tk.Text(frame, height=16)
        self.chat_output.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _build_actions_tab(self) -> None:
        frame = self.actions_tab
        actions = ttk.Frame(frame, padding=8)
        actions.pack(fill=tk.X)

        ttk.Button(actions, text="Disk Usage", command=lambda: self.run_action("disk_usage_summary")).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(actions, text="Network Summary", command=lambda: self.run_action("network_summary")).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(actions, text="List Upgrades", command=lambda: self.run_action("list_upgrades")).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(actions, text="Check Updates", command=lambda: self.run_action("system_update_check")).pack(
            side=tk.LEFT, padx=4
        )

        pkg = ttk.Frame(frame, padding=8)
        pkg.pack(fill=tk.X)
        ttk.Label(pkg, text="Package").pack(side=tk.LEFT)
        self.package_var = tk.StringVar(value="")
        ttk.Entry(pkg, textvariable=self.package_var, width=30).pack(side=tk.LEFT, padx=(6, 8))
        ttk.Button(pkg, text="Install", command=self.install_package).pack(side=tk.LEFT, padx=4)
        ttk.Button(pkg, text="Remove", command=self.remove_package).pack(side=tk.LEFT, padx=4)

        ttk.Label(frame, text="Output").pack(anchor=tk.W, padx=8, pady=(4, 0))
        self.action_output = tk.Text(frame, height=24)
        self.action_output.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _build_settings_tab(self) -> None:
        frame = self.settings_tab
        wrapper = ttk.Frame(frame, padding=8)
        wrapper.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(wrapper)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="Profiles").pack(anchor=tk.W)
        self.profile_list = tk.Listbox(left, width=30, height=18)
        self.profile_list.pack(fill=tk.Y, pady=(4, 8))
        self.profile_list.bind("<<ListboxSelect>>", self.on_profile_select)
        ttk.Button(left, text="Set Default", command=self.set_default_profile).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Delete", command=self.delete_profile).pack(fill=tk.X, pady=2)

        right = ttk.Frame(wrapper)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))
        form = ttk.Frame(right)
        form.pack(fill=tk.X)

        self.profile_name = tk.StringVar(value="")
        self.profile_provider = tk.StringVar(value="ollama")
        self.profile_model = tk.StringVar(value="llama3.2")
        self.profile_base_url = tk.StringVar(value="")
        self.profile_api_key_env = tk.StringVar(value="")
        self.permissions_mode = tk.StringVar(value="read_only")

        self._row(form, 0, "Name", self.profile_name)
        self._row(form, 1, "Provider", self.profile_provider, values=["ollama", "openai_compatible"], combo=True)
        self._row(form, 2, "Model", self.profile_model)
        self._row(form, 3, "Base URL", self.profile_base_url)
        self._row(form, 4, "API Key Env", self.profile_api_key_env)

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X, pady=(8, 8))
        ttk.Button(btns, text="Add/Update Profile", command=self.add_or_update_profile).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=4)

        perms = ttk.LabelFrame(right, text="Assistant Permissions", padding=8)
        perms.pack(fill=tk.X, pady=(4, 8))
        ttk.Radiobutton(perms, text="Read Only", variable=self.permissions_mode, value="read_only").pack(
            anchor=tk.W
        )
        ttk.Radiobutton(perms, text="Full Access", variable=self.permissions_mode, value="full_access").pack(
            anchor=tk.W
        )
        ttk.Label(
            perms,
            text="Read Only blocks privileged actions. Full Access allows them (with explicit approval).",
            wraplength=520,
        ).pack(anchor=tk.W, pady=(6, 0))

    @staticmethod
    def _row(parent: ttk.Frame, row: int, label: str, var: tk.StringVar, values: list[str] | None = None, combo: bool = False) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=3)
        if combo:
            widget: Any = ttk.Combobox(parent, textvariable=var, values=values or [], state="readonly", width=40)
        else:
            widget = ttk.Entry(parent, textvariable=var, width=42)
        widget.grid(row=row, column=1, sticky=tk.W, pady=3, padx=(8, 0))

    def _append_output(self, widget: tk.Text, text: str) -> None:
        widget.insert(tk.END, text + "\n")
        widget.see(tk.END)

    def load_settings(self) -> None:
        path = Path(self.settings_path_var.get())
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.data = data
            except Exception as exc:
                messagebox.showerror("Settings Error", f"Failed loading settings:\n{exc}")
                return
        else:
            self.data = default_settings()
        if str(self.data.get("assistant_permissions", "")).strip() not in {"read_only", "full_access"}:
            self.data["assistant_permissions"] = "read_only"
        self.permissions_mode.set(self.data.get("assistant_permissions", "read_only"))
        self.refresh_profiles()

    def save_settings(self) -> None:
        self.data["assistant_permissions"] = self.permissions_mode.get()
        path = Path(self.settings_path_var.get())
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, sort_keys=True)
            f.write("\n")
        messagebox.showinfo("Saved", f"Saved settings to {path}")

    def refresh_profiles(self) -> None:
        profiles = self.data.get("profiles", {})
        default_profile = str(self.data.get("default_profile", "")).strip()
        self.profile_list.delete(0, tk.END)
        names = sorted(profiles.keys())
        for name in names:
            marker = "*" if name == default_profile else " "
            provider = str(profiles[name].get("provider", "unknown"))
            model = str(profiles[name].get("model", "unknown"))
            self.profile_list.insert(tk.END, f"{marker} {name} ({provider}, model={model})")
        combo_values = names
        self.chat_profile_combo.configure(values=combo_values)
        if default_profile:
            self.chat_profile.set(default_profile)

    def _selected_profile_name(self) -> str:
        sel = self.profile_list.curselection()
        if not sel:
            return ""
        text = self.profile_list.get(sel[0]).strip()
        text = text[2:] if text and text[0] in {"*", " "} and len(text) > 2 else text
        return text.split(" (", 1)[0]

    def on_profile_select(self, _event: Any) -> None:
        name = self._selected_profile_name()
        if not name:
            return
        profiles = self.data.get("profiles", {})
        profile = profiles.get(name, {})
        self.profile_name.set(name)
        self.profile_provider.set(str(profile.get("provider", "ollama")))
        self.profile_model.set(str(profile.get("model", "")))
        self.profile_base_url.set(
            str(
                profile.get(
                    "ollama_base_url" if self.profile_provider.get() == "ollama" else "openai_base_url",
                    "",
                )
            )
        )
        self.profile_api_key_env.set(str(profile.get("openai_api_key_env", "")))

    def add_or_update_profile(self) -> None:
        name = self.profile_name.get().strip()
        provider = self.profile_provider.get().strip()
        model = self.profile_model.get().strip()
        base_url = self.profile_base_url.get().strip()
        api_key_env = self.profile_api_key_env.get().strip()
        if not PROFILE_RE.match(name):
            messagebox.showerror("Invalid Name", "Profile name can only include letters, numbers, dot, dash, underscore.")
            return
        if provider not in {"ollama", "openai_compatible"}:
            messagebox.showerror("Invalid Provider", "Provider must be ollama or openai_compatible.")
            return
        if not model:
            messagebox.showerror("Missing Model", "Model is required.")
            return
        profiles = self.data.setdefault("profiles", {})
        entry: dict[str, Any] = {"provider": provider, "model": model}
        if provider == "ollama":
            entry["ollama_base_url"] = base_url or "http://127.0.0.1:11434"
        else:
            entry["openai_base_url"] = base_url or "https://api.openai.com/v1"
            if api_key_env:
                entry["openai_api_key_env"] = api_key_env
        profiles[name] = entry
        if not self.data.get("default_profile"):
            self.data["default_profile"] = name
        self.refresh_profiles()

    def delete_profile(self) -> None:
        name = self._selected_profile_name()
        if not name:
            return
        profiles = self.data.setdefault("profiles", {})
        if name in profiles:
            del profiles[name]
            if self.data.get("default_profile") == name:
                self.data["default_profile"] = next(iter(sorted(profiles.keys())), "")
        self.refresh_profiles()

    def set_default_profile(self) -> None:
        name = self._selected_profile_name()
        if not name:
            return
        self.data["default_profile"] = name
        self.chat_profile.set(name)
        self.refresh_profiles()

    def send_ai_query(self) -> None:
        prompt = self.chat_prompt.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Missing Prompt", "Enter a prompt first.")
            return
        payload = {
            "action": "ai_query",
            "params": {
                "mode": self.chat_mode.get(),
                "prompt": prompt,
            },
            "approve": False,
            "dry_run": False,
        }
        profile = self.chat_profile.get().strip()
        if profile:
            payload["params"]["profile"] = profile
        try:
            response = send_request(self.socket_path_var.get().strip(), payload)
        except Exception as exc:
            messagebox.showerror("Request Failed", str(exc))
            return
        if response.get("ok"):
            out = str(response.get("stdout", "")).strip() or "(no output)"
            self._append_output(self.chat_output, out)
        else:
            self._append_output(self.chat_output, f"error: {response.get('error', 'unknown error')}")

    def run_action(self, action: str, params: dict[str, Any] | None = None, approve: bool = False) -> None:
        payload = {"action": action, "params": params or {}, "approve": approve, "dry_run": False}
        try:
            response = send_request(self.socket_path_var.get().strip(), payload)
        except Exception as exc:
            messagebox.showerror("Request Failed", str(exc))
            return
        if response.get("ok"):
            stdout = str(response.get("stdout", "")).strip()
            stderr = str(response.get("stderr", "")).strip()
            command = str(response.get("command_str", ""))
            self._append_output(self.action_output, f"$ {command}")
            if stdout:
                self._append_output(self.action_output, stdout)
            if stderr:
                self._append_output(self.action_output, f"stderr: {stderr}")
        else:
            self._append_output(self.action_output, f"error: {response.get('error', 'unknown error')}")

    def install_package(self) -> None:
        pkg = self.package_var.get().strip()
        if not pkg:
            messagebox.showerror("Missing Package", "Enter a package name.")
            return
        if not messagebox.askyesno("Confirm Install", f"Install package '{pkg}'?"):
            return
        self.run_action("install_package", {"package": pkg}, approve=True)

    def remove_package(self) -> None:
        pkg = self.package_var.get().strip()
        if not pkg:
            messagebox.showerror("Missing Package", "Enter a package name.")
            return
        if not messagebox.askyesno("Confirm Remove", f"Remove package '{pkg}'?"):
            return
        self.run_action("remove_package", {"package": pkg}, approve=True)


def main() -> int:
    app = AssistantGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
