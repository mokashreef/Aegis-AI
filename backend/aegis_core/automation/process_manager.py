"""
Aegis AI - Windows Process Manager.
Provides reliable, safe process enumeration, application launching, and process termination.
"""

import os
import subprocess
from typing import Any, Dict, List, Optional
import psutil
from aegis_core.utils.logger import logger


class ProcessManager:
    """Manages Windows desktop applications and processes."""

    @staticmethod
    def list_processes(filter_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists active running processes with memory and CPU usage."""
        results = []
        for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
            try:
                pinfo = proc.info
                name = pinfo.get("name", "")
                if filter_name and filter_name.lower() not in name.lower():
                    continue

                mem_mb = round(pinfo["memory_info"].rss / (1024 * 1024), 1) if pinfo.get("memory_info") else 0.0
                results.append({
                    "pid": pinfo["pid"],
                    "name": name,
                    "memory_mb": mem_mb,
                    "cpu_percent": pinfo.get("cpu_percent", 0.0),
                })
                if len(results) >= limit:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return sorted(results, key=lambda x: x["memory_mb"], reverse=True)

    @staticmethod
    def launch_app(app_name_or_path: str, arguments: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launches a desktop executable or document safely."""
        args = arguments or []
        command = [app_name_or_path] + args

        logger.info("Launching desktop application: %s", command)
        try:
            # On Windows, use shell invocation or standard popen
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
            )
            return {
                "launched": True,
                "target": app_name_or_path,
                "pid": proc.pid,
            }
        except Exception as exc:
            logger.error("Failed to launch application '%s': %s", app_name_or_path, exc)
            return {
                "launched": False,
                "target": app_name_or_path,
                "error": str(exc),
            }

    @staticmethod
    def terminate_process(pid: Optional[int] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """Safely terminates an application process by PID or name."""
        terminated = []
        errors = []

        if pid is not None:
            try:
                proc = psutil.Process(pid)
                proc_name = proc.name()
                proc.terminate()
                proc.wait(timeout=3.0)
                terminated.append({"pid": pid, "name": proc_name})
            except Exception as exc:
                errors.append({"pid": pid, "error": str(exc)})

        elif name is not None:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if proc.info["name"] and proc.info["name"].lower() == name.lower():
                        p = psutil.Process(proc.info["pid"])
                        p.terminate()
                        terminated.append({"pid": proc.info["pid"], "name": name})
                except Exception as exc:
                    errors.append({"pid": proc.info["pid"], "error": str(exc)})

        return {
            "success": len(terminated) > 0,
            "terminated": terminated,
            "errors": errors,
        }
