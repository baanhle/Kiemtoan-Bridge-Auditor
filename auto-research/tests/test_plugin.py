"""Kiểm thử tự động cho plugin auto-research (offline, chạy được trên Windows và Linux).

  python -m unittest discover -s tests -v
Mạng được giả lập bằng AUTO_RESEARCH_HTTP_FIXTURES (xem scripts/common.py).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
S = PLUGIN / "scripts"

REAL_DOI = "10.1016/j.example.2023.001"
CROSSREF_OK = {"message": {"title": ["Energy absorption of gyroid TPMS lattices"],
                           "issued": {"date-parts": [[2023, 5]]},
                           "author": [{"given": "An", "family": "Nguyen"}, {"given": "B", "family": "Tran"}]}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        prof = (PLUGIN / "templates/profile.yaml").read_text(encoding="utf-8")
        prof = prof.replace("download_delay_seconds: 20", "download_delay_seconds: 0").replace("max_fulltext: 30", "max_fulltext: 5")
        (self.root / "profile.yaml").write_text(prof, encoding="utf-8")
        self.fx = self.root / "fixtures.json"
        self.fx.write_text(json.dumps({f"https://api.crossref.org/works/{REAL_DOI}": json.dumps(CROSSREF_OK)}), encoding="utf-8")
        self.env = dict(os.environ, AUTO_RESEARCH_ROOT=str(self.root), AUTO_RESEARCH_PROFILE=str(self.root / "profile.yaml"),
                        AUTO_RESEARCH_HTTP_FIXTURES=str(self.fx), PYTHONIOENCODING="utf-8")
        self.env.pop("AUTO_RESEARCH_RUN", None)
        out = self.py("state.py", "init", "--topic", "TPMS lattice test")
        self.run_dir = Path(out.stdout.strip().splitlines()[-1])

    def tearDown(self):
        self.tmp.cleanup()

    def py(self, script, *args, stdin=None, check=True):
        p = subprocess.run([sys.executable, str(S / script), *args], cwd=str(self.root), env=self.env,
                           input=stdin, capture_output=True, text=True, encoding="utf-8")
        if check and p.returncode not in (0,):
            raise AssertionError(f"{script} {args} → {p.returncode}\n{p.stdout}\n{p.stderr}")
        return p

    def state(self):
        return json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))

    def stop_hook(self):
        payload = json.dumps({"hook_event_name": "Stop", "cwd": str(self.run_dir), "stop_hook_active": False})
        p = self.py("run_gates.py", "--hook", "stop", stdin=payload)
        return json.loads(p.stdout) if p.stdout.strip() else None

    def done_until(self, n):
        for i in range(1, n + 1):
            self.py("state.py", "--run", str(self.run_dir), "done", str(i))

    def build_complete_run(self):
        rd = self.run_dir
        (rd / "brief.md").write_text(textwrap.dedent("""\
            # Brief — test
            Selected: G2
            Candidate index: 0

            ## Bằng chứng tính mới
            - query: gyroid concrete impact | db: openalex | date: 2026-11-02 | hits: 3
            - query: tpms ipc concrete | db: crossref | date: 2026-11-02 | hits: 0
            - query: lattice reinforced concrete drop | db: arxiv | date: 2026-11-02 | hits: 1
            """), encoding="utf-8")
        (rd / "gaps/novelty.md").write_text("### G1\nVerdict: published\n\n### G2\nVerdict: novel\n", encoding="utf-8")
        (rd / "results/summary.csv").write_text("case,sea\nA,12.34\nB,15.6\n", encoding="utf-8")
        (rd / "analysis/run_all.py").write_text(textwrap.dedent("""\
            import csv, pathlib
            out = pathlib.Path('analysis'); (out/'tables').mkdir(parents=True, exist_ok=True); (out/'figures').mkdir(exist_ok=True)
            rows = list(csv.DictReader(open('results/summary.csv', encoding='utf-8')))
            with open(out/'tables/sea.csv', 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f); w.writerow(['case','sea'])
                for r in rows: w.writerow([r['case'], round(float(r['sea']), 2)])
            (out/'figures/sea.png').write_bytes(b'PNG')
            (out/'figures/sea.data.csv').write_text('case,sea\\nA,12.34\\nB,15.6\\n', encoding='utf-8')
            """), encoding="utf-8")
        subprocess.run([sys.executable, "analysis/run_all.py"], cwd=str(rd), check=True)
        m = rd / "manuscript"
        (m / "references.bib").write_text(textwrap.dedent(f"""\
            @article{{nguyen2023,
              author = {{Nguyen, An and Tran, B}},
              title = {{Energy absorption of gyroid {{TPMS}} lattices}},
              journal = {{Test J}},
              year = {{2023}},
              doi = {{{REAL_DOI}}}
            }}
            """), encoding="utf-8")
        (m / "manuscript.md").write_text(textwrap.dedent("""\
            # Title

            ## 1 Introduction
            Gyroid lattices absorb energy well [@nguyen2023], reaching 12.34 J/g in 2023 tests.

            ## 2 Results
            Case B reached 15.6 J/g (@fig:sea, @tbl:sea).

            ![Specific energy absorption](../analysis/figures/sea.png){#fig:sea}

            : SEA by case {#tbl:sea}

            # References
            """), encoding="utf-8")
        (m / "numbers.csv").write_text(
            "value,unit,context,source_type,source,locator\n"
            "12.34,J/g,intro,result,analysis/tables/sea.csv,row A\n"
            "15.6,J/g,results,result,analysis/tables/sea.csv,row B\n", encoding="utf-8")
        for f in ("SUMMARY.md",):
            (rd / f).write_text("# Summary\n", encoding="utf-8")


class TestState(Base):
    def test_init_creates_layout(self):
        self.assertTrue((self.run_dir / "state.json").is_file())
        self.assertTrue((self.run_dir / "DECISIONS.md").is_file())
        self.assertEqual(self.py("state.py", "--run", str(self.run_dir), "next").stdout.strip(), "1")

    def test_from_resets_later_stages_and_keeps_files(self):
        self.done_until(9)
        (self.run_dir / "brief.md").write_text("keep", encoding="utf-8")
        self.py("state.py", "--run", str(self.run_dir), "from", "novelty")
        st = self.state()
        self.assertEqual(st["stages"]["5"]["status"], "done")
        self.assertEqual(st["stages"]["6"]["status"], "pending")
        self.assertEqual(st["stages"]["9"]["status"], "pending")
        self.assertEqual(self.py("state.py", "--run", str(self.run_dir), "next").stdout.strip(), "6")
        self.assertEqual((self.run_dir / "brief.md").read_text(encoding="utf-8"), "keep")
        self.assertIn("--from", (self.run_dir / "DECISIONS.md").read_text(encoding="utf-8"))

    def test_fallback_three_candidates_then_stop(self):
        self.done_until(8)
        self.assertEqual(self.py("state.py", "--run", str(self.run_dir), "fallback", "--reason", "không hội tụ").stdout.strip(), "7")
        self.assertEqual(self.state()["candidate_index"], 1)
        self.assertEqual(self.state()["stages"]["7"]["status"], "pending")
        self.py("state.py", "--run", str(self.run_dir), "fallback", "--reason", "thiếu dữ liệu")
        self.assertEqual(self.py("state.py", "--run", str(self.run_dir), "fallback", "--reason", "vượt tài nguyên").stdout.strip(), "STOP")
        self.assertEqual(self.state()["status"], "stopped")
        # dừng mà chưa có báo cáo tình trạng ⇒ bị chặn
        self.assertEqual(self.stop_hook()["decision"], "block")
        (self.run_dir / "STATUS_REPORT.md").write_text("x", encoding="utf-8")
        self.assertIsNone(self.stop_hook())


class TestDownload(Base):
    def setUp(self):
        super().setUp()
        (self.run_dir / "literature/shortlist.csv").write_text(
            "doi,title,year\n10.1/a,Paper A,2024\n10.1/b,Paper B,2023\n10.1/c,Paper C,2022\n", encoding="utf-8")

    def test_session_expired_marks_abstract_only_and_continues(self):
        self.py("download.py", "oa", "--run", str(self.run_dir))
        todo = json.loads(self.py("download.py", "pending", "--run", str(self.run_dir)).stdout)["todo"]
        self.assertEqual(len(todo), 3)
        # bài đầu tải thành công qua Chrome
        (self.run_dir / todo[0]["file"]).write_bytes(b"%PDF-1.4 test")
        self.py("download.py", "mark", "--run", str(self.run_dir), "--doi", todo[0]["doi"], "--status", "full",
                "--source", "openathens", "--file", todo[0]["file"])
        # phiên OpenAthens hết hạn
        out = json.loads(self.py("download.py", "expire", "--run", str(self.run_dir), "--reason", "sim").stdout)
        self.assertEqual(out["marked_abstract_only"], 2)
        idx = (self.run_dir / "papers/index.csv").read_text(encoding="utf-8")
        self.assertEqual(idx.count("abstract-only"), 2)
        # pipeline chạy tiếp: giai đoạn 3 đánh dấu xong, sang 4
        self.py("state.py", "--run", str(self.run_dir), "done", "3")
        # lần chạy sau tải bù: bài abstract-only vẫn nằm trong danh sách cần tải
        todo2 = json.loads(self.py("download.py", "pending", "--run", str(self.run_dir)).stdout)["todo"]
        self.assertEqual({t["doi"] for t in todo2}, {"10.1/b", "10.1/c"})

    def test_mark_rejects_non_pdf(self):
        self.py("download.py", "oa", "--run", str(self.run_dir))
        (self.run_dir / "papers/x.pdf").write_text("<html>login</html>", encoding="utf-8")
        p = self.py("download.py", "mark", "--run", str(self.run_dir), "--doi", "10.1/a", "--status", "full",
                    "--file", "papers/x.pdf", check=False)
        self.assertNotEqual(p.returncode, 0)


class TestGates(Base):
    def setUp(self):
        super().setUp()
        self.build_complete_run()
        self.done_until(12)

    def test_all_gates_pass_on_clean_run(self):
        p = self.py("run_gates.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue((self.run_dir / "VERIFICATION.md").is_file())

    def test_stop_hook_asks_for_handoff_then_allows(self):
        r = self.stop_hook()
        self.assertEqual(r["decision"], "block")
        self.assertIn("13", r["reason"])
        self.py("state.py", "--run", str(self.run_dir), "done", "13")
        self.assertIsNone(self.stop_hook())

    def test_fake_doi_is_blocked(self):
        bib = self.run_dir / "manuscript/references.bib"
        bib.write_text(bib.read_text(encoding="utf-8") + textwrap.dedent("""\
            @article{fake2024,
              author = {Doe, John},
              title = {A study that does not exist},
              year = {2024},
              doi = {10.9999/fake.2024.123}
            }
            """), encoding="utf-8")
        ms = self.run_dir / "manuscript/manuscript.md"
        ms.write_text(ms.read_text(encoding="utf-8").replace("[@nguyen2023]", "[@nguyen2023; @fake2024]"), encoding="utf-8")
        p = self.py("verify_citations.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("10.9999/fake.2024.123", p.stdout)
        r = self.stop_hook()
        self.assertEqual(r["decision"], "block")
        self.assertIn("fake2024", r["reason"])
        # hook PostToolUse cũng báo ngay khi sửa references.bib
        payload = json.dumps({"cwd": str(self.run_dir), "tool_name": "Edit", "tool_input": {"file_path": str(bib)}})
        e = self.py("run_gates.py", "--hook", "edit", stdin=payload, check=False)
        self.assertEqual(e.returncode, 2)
        # --prune loại trích dẫn và ghi báo cáo
        self.py("verify_citations.py", "--run", str(self.run_dir), "--prune", check=False)
        self.assertNotIn("fake2024", bib.read_text(encoding="utf-8"))
        self.assertIn("fake2024", (self.run_dir / "manuscript/rejected_citations.csv").read_text(encoding="utf-8"))

    def test_wrong_metadata_is_blocked(self):
        bib = self.run_dir / "manuscript/references.bib"
        bib.write_text(bib.read_text(encoding="utf-8").replace("year = {2023}", "year = {2019}"), encoding="utf-8")
        p = self.py("verify_citations.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("năm lệch", p.stdout)

    def test_unsourced_number_is_blocked(self):
        ms = self.run_dir / "manuscript/manuscript.md"
        ms.write_text(ms.read_text(encoding="utf-8").replace("Case B reached", "Peak force was 87.5 kN. Case B reached"),
                      encoding="utf-8")
        p = self.py("verify_numbers.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("87.5", p.stdout)
        r = self.stop_hook()
        self.assertEqual(r["decision"], "block")
        self.assertIn("87.5", r["reason"])

    def test_number_row_pointing_to_wrong_value_is_blocked(self):
        nc = self.run_dir / "manuscript/numbers.csv"
        nc.write_text(nc.read_text(encoding="utf-8").replace("15.6,J/g", "15.9,J/g"), encoding="utf-8")
        ms = self.run_dir / "manuscript/manuscript.md"
        ms.write_text(ms.read_text(encoding="utf-8").replace("15.6 J/g", "15.9 J/g"), encoding="utf-8")
        p = self.py("verify_numbers.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 1)

    def test_reproducibility_detects_drift(self):
        t = self.run_dir / "analysis/tables/sea.csv"
        t.write_text(t.read_text(encoding="utf-8").replace("15.6", "15.7"), encoding="utf-8")
        p = self.py("rerun_analysis.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 1)

    def test_consistency_detects_missing_label(self):
        ms = self.run_dir / "manuscript/manuscript.md"
        ms.write_text(ms.read_text(encoding="utf-8").replace("(@fig:sea, @tbl:sea)", "(@fig:sea, @tbl:sea, @fig:missing)"),
                      encoding="utf-8")
        p = self.py("check_consistency.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("fig:missing", p.stdout)

    def test_novelty_gate_requires_evidence(self):
        (self.run_dir / "gaps/novelty.md").write_text("### G2\nVerdict: published\n", encoding="utf-8")
        p = self.py("check_novelty.py", "--run", str(self.run_dir), check=False)
        self.assertEqual(p.returncode, 1)


class TestStopHookPipeline(Base):
    def test_blocks_mid_pipeline_and_allows_after_until(self):
        self.done_until(2)
        r = self.stop_hook()
        self.assertEqual(r["decision"], "block")
        self.assertIn("giai đoạn 3", r["reason"])
        # chạy thử giới hạn 1–7
        self.py("state.py", "--run", str(self.run_dir), "from", "3", "--until", "7")
        self.done_until(7)
        self.assertIsNone(self.stop_hook())

    def test_hook_finds_run_from_research_root(self):
        # Claude Code mở tại D:/Research (= self.root): hook phải tìm thấy lần chạy qua auto-research/ACTIVE_RUN
        payload = json.dumps({"cwd": str(self.root)})
        p = self.py("run_gates.py", "--hook", "stop", stdin=payload)
        self.assertEqual(json.loads(p.stdout)["decision"], "block")

    def test_no_active_run_is_noop(self):
        payload = json.dumps({"cwd": tempfile.gettempdir()})
        env = dict(self.env); env["AUTO_RESEARCH_ROOT"] = str(self.root / "nowhere")
        p = subprocess.run([sys.executable, str(S / "run_gates.py"), "--hook", "stop"], input=payload,
                           capture_output=True, text=True, env=env, cwd=tempfile.gettempdir())
        self.assertEqual(p.returncode, 0); self.assertEqual(p.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
