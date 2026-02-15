import argparse
import json
import logging
import os
import platform
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


LOG = logging.getLogger("LocalAISupervisor")


@dataclass
class ProviderConfig:
    name: str
    endpoint: str
    api_key_env: str
    model: str
    api_version: Optional[str] = None


class ProviderClient:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = os.getenv(config.api_key_env)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def chat(self, prompt: str, timeout: int = 45) -> Dict[str, Any]:
        provider = self.config.name.lower()

        if not self.enabled:
            raise RuntimeError(f"{self.config.name} is not enabled; missing {self.config.api_key_env}")

        if provider == "openai":
            return self._post_openai_style(
                url=f"{self.config.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                model=self.config.model,
                prompt=prompt,
                timeout=timeout,
            )

        if provider == "grok":
            return self._post_openai_style(
                url=f"{self.config.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                model=self.config.model,
                prompt=prompt,
                timeout=timeout,
            )

        if provider == "github":
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            return self._post_openai_style(
                url=f"{self.config.endpoint}/chat/completions",
                headers=headers,
                model=self.config.model,
                prompt=prompt,
                timeout=timeout,
            )

        if provider == "microsoft":
            if not self.config.api_version:
                raise ValueError("Microsoft provider requires api_version")
            url = (
                f"{self.config.endpoint}/openai/deployments/{self.config.model}/chat/completions"
                f"?api-version={self.config.api_version}"
            )
            response = requests.post(
                url,
                headers={"api-key": self.api_key, "Content-Type": "application/json"},
                json={"messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 600},
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        if provider == "anthropic":
            response = requests.post(
                f"{self.config.endpoint}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "max_tokens": 600,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        raise ValueError(f"Unsupported provider: {self.config.name}")

    def _post_openai_style(
        self,
        url: str,
        headers: Dict[str, str],
        model: str,
        prompt: str,
        timeout: int,
    ) -> Dict[str, Any]:
        response = requests.post(
            url,
            headers={**headers, "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 600},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()


class LocalSystemProfiler:
    @staticmethod
    def _run(cmd: List[str]) -> str:
        try:
            return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
        except Exception:
            return ""

    def collect(self) -> Dict[str, Any]:
        cpu_count = os.cpu_count() or 1
        loadavg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
        meminfo = self._read_meminfo()
        gpu_info = self._run(["bash", "-lc", "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader"]) or "none"

        profile = {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": cpu_count,
            "loadavg_1m": loadavg[0],
            "memory_total_kb": meminfo.get("MemTotal", 0),
            "memory_available_kb": meminfo.get("MemAvailable", 0),
            "gpu": gpu_info,
            "timestamp": time.time(),
        }
        return profile

    @staticmethod
    def _read_meminfo() -> Dict[str, int]:
        info: Dict[str, int] = {}
        try:
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, value = line.split(":", 1)
                info[key] = int(value.strip().split()[0])
        except Exception:
            return info
        return info


class SelfOptimizer:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                LOG.warning("State file is corrupt, recreating.")
        return {"provider_metrics": {}, "runtime_tuning": {}, "history": []}

    def save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def recommend_runtime(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        cpu = profile.get("cpu_count", 1)
        mem_gb = profile.get("memory_available_kb", 0) / 1024 / 1024

        worker_count = max(1, min(cpu, 8))
        if mem_gb < 2:
            worker_count = 1

        recommendation = {
            "worker_count": worker_count,
            "streaming_enabled": cpu >= 4,
            "parallel_tool_calls": cpu >= 8 and mem_gb >= 8,
            "max_context_tokens": 4096 if mem_gb < 8 else 8192,
        }
        self.state["runtime_tuning"] = recommendation
        return recommendation

    def record_benchmark(self, provider: str, latency_s: float, success: bool) -> None:
        metrics = self.state["provider_metrics"].setdefault(provider, [])
        metrics.append({"latency_s": latency_s, "success": success, "ts": time.time()})
        self.state["provider_metrics"][provider] = metrics[-50:]

    def choose_best_provider(self, active_providers: List[str]) -> Optional[str]:
        if not active_providers:
            return None

        provider_scores: List[Tuple[str, float]] = []
        for provider in active_providers:
            runs = self.state["provider_metrics"].get(provider, [])
            if not runs:
                provider_scores.append((provider, 0.5))
                continue
            success_ratio = statistics.mean(1.0 if run["success"] else 0.0 for run in runs)
            latency = statistics.mean(run["latency_s"] for run in runs)
            score = (success_ratio * 0.7) + (0.3 * (1 / max(latency, 0.05)))
            provider_scores.append((provider, score))

        provider_scores.sort(key=lambda s: s[1], reverse=True)
        best = provider_scores[0][0]
        self.state["history"].append({"chosen_provider": best, "timestamp": time.time()})
        self.state["history"] = self.state["history"][-100:]
        return best


class LocalAISupervisor:
    def __init__(self, config_path: Path):
        cfg = json.loads(config_path.read_text())
        self.profile = LocalSystemProfiler()
        self.optimizer = SelfOptimizer(Path(cfg.get("state_file", "state/agent_state.json")))
        self.providers: Dict[str, ProviderClient] = {}

        for item in cfg.get("providers", []):
            pconf = ProviderConfig(**item)
            client = ProviderClient(pconf)
            self.providers[pconf.name.lower()] = client

    def inspect(self) -> Dict[str, Any]:
        system_profile = self.profile.collect()
        runtime_tuning = self.optimizer.recommend_runtime(system_profile)
        self.optimizer.save()
        return {"system_profile": system_profile, "runtime_tuning": runtime_tuning}

    def benchmark(self, prompt: str = "Reply with one short sentence: 'ready'.") -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        for name, client in self.providers.items():
            if not client.enabled:
                report[name] = {"enabled": False, "reason": f"missing {client.config.api_key_env}"}
                continue

            started = time.perf_counter()
            ok = True
            error = None
            try:
                _ = client.chat(prompt, timeout=30)
            except Exception as exc:
                ok = False
                error = str(exc)
            latency = time.perf_counter() - started
            self.optimizer.record_benchmark(name, latency, ok)
            report[name] = {"enabled": True, "success": ok, "latency_s": round(latency, 3), "error": error}

        self.optimizer.save()
        return report

    def ask(self, prompt: str, preferred_provider: Optional[str] = None) -> Dict[str, Any]:
        active = [name for name, client in self.providers.items() if client.enabled]
        if not active:
            raise RuntimeError("No providers are enabled. Export API keys and retry.")

        provider = preferred_provider.lower() if preferred_provider else self.optimizer.choose_best_provider(active)
        if provider not in self.providers or not self.providers[provider].enabled:
            provider = active[0]

        started = time.perf_counter()
        try:
            response = self.providers[provider].chat(prompt)
            self.optimizer.record_benchmark(provider, time.perf_counter() - started, True)
            ok = True
        except Exception as exc:
            self.optimizer.record_benchmark(provider, time.perf_counter() - started, False)
            self.optimizer.save()
            raise RuntimeError(f"Provider {provider} failed: {exc}")

        self.optimizer.save()
        return {"provider": provider, "ok": ok, "response": response}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Ubuntu AI supervisor with multi-provider orchestration.")
    parser.add_argument("--config", default="agents/local_ai_supervisor.config.json", help="Path to JSON config file")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("inspect", help="Collect local hardware profile and runtime tuning recommendations")
    bench = sub.add_parser("benchmark", help="Benchmark enabled providers")
    bench.add_argument("--prompt", default="Reply with one word: ready.")

    ask = sub.add_parser("ask", help="Send a prompt using best available provider")
    ask.add_argument("prompt")
    ask.add_argument("--provider", default=None, help="Force a specific provider")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = build_arg_parser()
    args = parser.parse_args()

    supervisor = LocalAISupervisor(Path(args.config))

    if args.command == "inspect":
        print(json.dumps(supervisor.inspect(), indent=2))
    elif args.command == "benchmark":
        print(json.dumps(supervisor.benchmark(prompt=args.prompt), indent=2))
    elif args.command == "ask":
        print(json.dumps(supervisor.ask(prompt=args.prompt, preferred_provider=args.provider), indent=2))


if __name__ == "__main__":
    main()
