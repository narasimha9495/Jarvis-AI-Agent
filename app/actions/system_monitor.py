"""System health monitoring action module.

Monitor CPU, memory, disk, and battery to keep your machine healthy.
Uses psutil for cross-platform system metrics.
"""

import logging
from datetime import datetime
from typing import Any

from app.actions.base import BaseAction

logger = logging.getLogger(__name__)


class SystemMonitorAction(BaseAction):
    """Monitor system health — CPU, memory, disk, and battery."""

    @property
    def name(self) -> str:
        return "system_monitor"

    @property
    def description(self) -> str:
        return "Monitor system health - CPU, memory, disk, and battery status"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Route to the appropriate monitoring sub-action."""
        action = params.get("action", "")
        handlers = {
            "system_status": self._system_status,
            "cpu_alert": self._cpu_alert,
            "disk_alert": self._disk_alert,
            "top_processes": self._top_processes,
        }
        handler = handlers.get(action)
        if not handler:
            return {"success": False, "message": f"Unknown monitor action: {action}"}
        return await handler(params)

    async def _system_status(self, params: dict) -> dict[str, Any]:
        """Full system overview."""
        try:
            import psutil

            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory
            mem = psutil.virtual_memory()
            memory = {
                "total_gb": round(mem.total / (1024**3), 1),
                "used_gb": round(mem.used / (1024**3), 1),
                "percent": mem.percent,
            }

            # Disk
            disk = psutil.disk_usage("/")
            disk_info = {
                "total_gb": round(disk.total / (1024**3), 1),
                "used_gb": round(disk.used / (1024**3), 1),
                "free_gb": round(disk.free / (1024**3), 1),
                "percent": disk.percent,
            }

            # Battery
            battery = None
            try:
                bat = psutil.sensors_battery()
                if bat:
                    time_left = "Charging" if bat.power_plugged else (
                        f"{bat.secsleft // 3600}h {(bat.secsleft % 3600) // 60}m"
                        if bat.secsleft > 0 else "Unknown"
                    )
                    battery = {
                        "percent": bat.percent,
                        "plugged": bat.power_plugged,
                        "time_left": time_left,
                    }
            except Exception:
                pass

            # Boot time
            boot = datetime.fromtimestamp(psutil.boot_time())
            boot_str = boot.strftime("%Y-%m-%d %H:%M:%S")

            return {
                "success": True,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory": memory,
                "disk": disk_info,
                "battery": battery,
                "boot_time": boot_str,
                "message": (
                    f"CPU: {cpu_percent}% | "
                    f"RAM: {memory['percent']}% | "
                    f"Disk: {disk_info['percent']}%"
                ),
            }
        except ImportError:
            return {
                "success": False,
                "message": "psutil is not installed. Run: pip install psutil",
            }
        except Exception as e:
            logger.error(f"System status failed: {e}")
            return {"success": False, "message": f"Failed to get system status: {e}"}

    async def _cpu_alert(self, params: dict) -> dict[str, Any]:
        """Check if CPU usage is above a threshold."""
        try:
            import psutil

            threshold = int(params.get("threshold", 80))
            current = psutil.cpu_percent(interval=1)

            return {
                "success": True,
                "above_threshold": current > threshold,
                "current": current,
                "threshold": threshold,
                "message": (
                    f"⚠️ CPU at {current}% (above {threshold}% threshold)"
                    if current > threshold
                    else f"✅ CPU at {current}% (below {threshold}% threshold)"
                ),
            }
        except ImportError:
            return {"success": False, "message": "psutil not installed"}
        except Exception as e:
            return {"success": False, "message": f"CPU alert failed: {e}"}

    async def _disk_alert(self, params: dict) -> dict[str, Any]:
        """Check if disk usage is above a threshold."""
        try:
            import psutil

            threshold = int(params.get("threshold", 90))
            disk = psutil.disk_usage("/")
            current = disk.percent

            return {
                "success": True,
                "above_threshold": current > threshold,
                "current": current,
                "threshold": threshold,
                "free_gb": round(disk.free / (1024**3), 1),
                "message": (
                    f"⚠️ Disk at {current}% (above {threshold}% threshold)"
                    if current > threshold
                    else f"✅ Disk at {current}% ({round(disk.free / (1024**3), 1)}GB free)"
                ),
            }
        except ImportError:
            return {"success": False, "message": "psutil not installed"}
        except Exception as e:
            return {"success": False, "message": f"Disk alert failed: {e}"}

    async def _top_processes(self, params: dict) -> dict[str, Any]:
        """List top 5 processes by CPU usage."""
        try:
            import psutil

            processes = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                try:
                    info = proc.info
                    processes.append({
                        "name": info["name"],
                        "cpu_percent": info["cpu_percent"] or 0,
                        "memory_mb": round(
                            (info["memory_info"].rss / (1024**2)) if info["memory_info"] else 0,
                            1,
                        ),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU and take top 5
            processes.sort(key=lambda p: p["cpu_percent"], reverse=True)
            top_5 = processes[:5]

            return {
                "success": True,
                "processes": top_5,
                "message": f"Top processes: {', '.join(p['name'] for p in top_5)}",
            }
        except ImportError:
            return {"success": False, "message": "psutil not installed"}
        except Exception as e:
            return {"success": False, "message": f"Failed to get processes: {e}"}
