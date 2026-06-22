import shlex
from pathlib import Path


class ResumeGenerationScriptWriter:
    def write(
        self,
        output_path: Path,
        project_root: Path,
        report_dir: Path,
        vacancy_url: str,
    ) -> Path:
        command = (
            f"{shlex.quote(str(project_root / 'run.sh'))} generate "
            f"--report-dir {shlex.quote(str(report_dir))} "
            f"--vacancy-url {shlex.quote(vacancy_url)}"
        )
        script = "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "",
                command,
                "",
            ]
        )

        output_path.write_text(script, encoding="utf-8")
        output_path.chmod(0o755)
        return output_path
