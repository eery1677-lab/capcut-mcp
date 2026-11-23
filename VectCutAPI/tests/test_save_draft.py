"""
Integration test for save_draft: drives mcp_server.py over stdio JSON-RPC.

Covers safe saving (validation, no overwrite, failure reporting) and CapCut compatibility
(draft_content.json, accurate draft_meta_info.json, no template leftovers).

Run with the VectCutAPI virtualenv:
    .venv\\Scripts\\python.exe tests\\test_save_draft.py [--keep]
or, if pytest is installed:
    .venv\\Scripts\\python.exe -m pytest tests/test_save_draft.py

Drafts are written only to a fresh temporary folder (deleted afterwards unless --keep).
The CapCut Projects folder under %LOCALAPPDATA% is snapshotted and must be unchanged.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

VECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPCUT_PROJECTS = os.path.join(os.environ.get("LOCALAPPDATA", ""), "CapCut", "User Data", "Projects")
TEMPLATE_TIMELINE_ID = "91E08AC5-22FB-47e2-9AA0-7DC300FAEA2B"
TEMPLATE_PROJECT_ID = "989869B1-B560-489C-9C6F-4B444F24BF36"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def snapshot(path):
    out = {}
    if os.path.isdir(path):
        for d, _, files in os.walk(path):
            for f in files:
                p = os.path.join(d, f)
                st = os.stat(p)
                out[p] = (st.st_size, st.st_mtime_ns)
    return out


class McpServer:
    def __init__(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=VECT)
        self.proc = subprocess.Popen([sys.executable, "mcp_server.py"], cwd=VECT, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                     encoding="utf-8", env=env)
        self._id = 0

    def request(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("mcp_server.py exited unexpectedly")
            if line.startswith("{"):
                return json.loads(line)

    def call(self, name, args):
        resp = self.request("tools/call", {"name": name, "arguments": args})
        return json.loads(resp["result"]["content"][0]["text"])

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def main(keep=False):
    results = []

    def check(label, cond, detail=""):
        results.append(bool(cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {label}" + (f"  -> {detail}" if detail and not cond else ""))

    def check_capcut_files(label, folder, name, duration_us, text):
        content_p = os.path.join(folder, "draft_content.json")
        check(f"{label}: draft_content.json exists", os.path.isfile(content_p))
        c = load_json(content_p)
        i = load_json(os.path.join(folder, "draft_info.json"))
        m = load_json(os.path.join(folder, "draft_meta_info.json"))
        check(f"{label}: draft_content.json == draft_info.json", c == i)
        check(f"{label}: timeline has text, canvas, duration",
              c["canvas_config"]["width"] == 1080 and c["canvas_config"]["height"] == 1920
              and c["duration"] == duration_us
              and json.loads(c["materials"]["texts"][0]["content"])["text"] == text
              and any(t["type"] == "text" and t["segments"][0]["target_timerange"]["duration"] == duration_us
                      for t in c["tracks"]))
        check(f"{label}: unique timeline id", c["id"] != TEMPLATE_TIMELINE_ID, c["id"])
        fold = os.path.realpath(folder).replace("\\", "/")
        ok = (m["draft_id"] != TEMPLATE_PROJECT_ID and m["draft_name"] == name and m["draft_fold_path"] == fold
              and m["draft_root_path"] == os.path.dirname(fold) and m["tm_duration"] == duration_us
              and m["cloud_draft_sync"] is False and m["cloud_draft_cover"] is False
              and m["tm_draft_create"] > 1.7e15)
        check(f"{label}: draft_meta_info.json correct", ok,
              {k: m.get(k) for k in ("draft_id", "draft_name", "draft_fold_path", "draft_root_path", "tm_duration")})
        blob = ""
        for dp, _, fs in os.walk(folder):
            for f in fs:
                with open(os.path.join(dp, f), encoding="utf-8", errors="ignore") as fh:
                    blob += fh.read()
        check(f"{label}: no template leftovers (Mac paths, 0707, template ids, .bak)",
              not os.path.exists(os.path.join(folder, "draft_info.json.bak"))
              and "sunguannan" not in blob and "/Movies/" not in blob and '"0707"' not in blob
              and TEMPLATE_PROJECT_ID not in blob and TEMPLATE_TIMELINE_ID not in blob)
        return m["draft_id"], c["id"]

    capcut_before = snapshot(CAPCUT_PROJECTS)
    root = os.path.realpath(tempfile.mkdtemp(prefix="capcut_save_draft_test_"))
    fake_project = os.path.join(root, "existing_project")
    os.makedirs(fake_project)
    with open(os.path.join(fake_project, "draft_info.json"), "w") as f:
        f.write("{}")

    server = McpServer()
    working_copies = []
    try:
        # Tool schema
        tools = {t["name"]: t for t in server.request("tools/list")["result"]["tools"]}
        check("all 11 tools listed", len(tools) == 11, sorted(tools))
        sd = tools["save_draft"]["inputSchema"]
        check("schema exposes draft_folder, draft_id required",
              "draft_folder" in sd["properties"] and sd.get("required") == ["draft_id"])
        check("add_text font_size default matches impl (8.0)",
              tools["add_text"]["inputSchema"]["properties"]["font_size"]["default"] == 8.0)

        # 1. Save to a folder, explicit font size
        d = server.call("create_draft", {"width": 1080, "height": 1920})["result"]["draft_id"]
        working_copies.append(os.path.join(VECT, d))
        server.call("add_text", {"draft_id": d, "text": "Hello World", "start": 0, "end": 3, "font_size": 24})
        r = server.call("save_draft", {"draft_id": d, "draft_folder": root})
        dest = os.path.join(root, d)
        check("save to temp folder succeeds",
              r["success"] and os.path.normcase(r["result"]["draft_path"]) == os.path.normcase(dest), r)
        info = load_json(os.path.join(dest, "draft_info.json"))
        size = json.loads(info["materials"]["texts"][0]["content"])["styles"][0]["size"]
        check("explicit font_size 24 saved as 24", size == 24, f"size={size}")
        ids1 = check_capcut_files("folder", dest, d, 3_000_000, "Hello World")
        check("save result reports project_id", r["result"].get("project_id") == ids1[0])
        check("working copy cleaned up",
              not os.path.exists(os.path.join(VECT, d)) and r["result"]["working_path"] is None)
        check("no leftover staging folders", not [n for n in os.listdir(root) if ".saving-" in n])

        # 2. Saving again never overwrites
        h_before = file_hash(os.path.join(dest, "draft_info.json"))
        r = server.call("save_draft", {"draft_id": d, "draft_folder": root})
        check("re-save refuses to overwrite", not r["success"] and "refusing to overwrite" in r.get("error", ""),
              r.get("error"))
        check("existing draft unchanged", file_hash(os.path.join(dest, "draft_info.json")) == h_before)

        # 3. Validation failures
        for label, args, needle in [
            ("relative path rejected", {"draft_id": d, "draft_folder": os.path.join("relative", "path")}, "absolute"),
            ("missing folder rejected", {"draft_id": d, "draft_folder": os.path.join(root, "nope")}, "does not exist"),
            ("existing project folder rejected", {"draft_id": d, "draft_folder": fake_project}, "existing draft project"),
            ("VectCutAPI dir rejected", {"draft_id": d, "draft_folder": VECT}, "working directory"),
            ("path-traversal draft_id rejected", {"draft_id": os.path.join("..", "evil"), "draft_folder": root},
             "Invalid draft_id"),
            ("unknown draft_id fails", {"draft_id": "dfd_cat_does_not_exist", "draft_folder": root},
             "does not exist in cache"),
            ("missing draft_id fails", {}, "draft_id is required"),
        ]:
            r = server.call("save_draft", args)
            check(label, not r["success"] and needle in r.get("error", ""), r.get("error"))
        check("fake project untouched", os.listdir(fake_project) == ["draft_info.json"])

        # 4. No draft_folder: stays in the working directory; default font size
        d2 = server.call("create_draft", {})["result"]["draft_id"]
        wp = os.path.join(VECT, d2)
        working_copies.append(wp)
        server.call("add_text", {"draft_id": d2, "text": "Default size", "start": 0, "end": 3})
        r = server.call("save_draft", {"draft_id": d2})
        check("save without draft_folder reports working path",
              r["success"] and os.path.normcase(r["result"]["draft_path"]) == os.path.normcase(wp)
              and os.path.isfile(os.path.join(wp, "draft_info.json")), r)
        info = load_json(os.path.join(wp, "draft_info.json"))
        size = json.loads(info["materials"]["texts"][0]["content"])["styles"][0]["size"]
        check("omitted font_size uses 8.0", size == 8.0, f"size={size}")
        ids2 = check_capcut_files("no-folder", wp, d2, 3_000_000, "Default size")
        check("ids differ between drafts", ids1[0] != ids2[0] and ids1[1] != ids2[1])

        # 5. The 5-second draft verified manually in CapCut 9.8
        d3 = server.call("create_draft", {"width": 1080, "height": 1920})["result"]["draft_id"]
        working_copies.append(os.path.join(VECT, d3))
        server.call("add_text", {"draft_id": d3, "text": "CapCut MCP Automation Working", "start": 0, "end": 5})
        r = server.call("save_draft", {"draft_id": d3, "draft_folder": root})
        check("5 s draft saves", r["success"], r.get("error"))
        check_capcut_files("5s", os.path.join(root, d3), d3, 5_000_000, "CapCut MCP Automation Working")
    finally:
        server.close()
        for wc in working_copies:
            shutil.rmtree(wc, ignore_errors=True)

    check("CapCut Projects folder unchanged", snapshot(CAPCUT_PROJECTS) == capcut_before)

    if keep:
        print(f"\nTest drafts kept in {root}")
    else:
        shutil.rmtree(root, ignore_errors=True)
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


def test_save_draft():
    """pytest entry point."""
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main(keep="--keep" in sys.argv))
