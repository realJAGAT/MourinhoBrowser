import time
from typing import Dict

try:
    import psutil
except ImportError:
    psutil = None


class FitnessMonitor:
    def __init__(self):
        self.last_network = self._read_network_bytes()

    def _read_network_bytes(self) -> int:
        if psutil is None:
            return 0
        counters = psutil.net_io_counters()
        return counters.bytes_sent + counters.bytes_recv

    def get_system_metrics(self) -> Dict[str, float]:
        cpu = psutil.cpu_percent(interval=0.1) if psutil else 0.0
        memory = psutil.virtual_memory().percent if psutil else 0.0
        network = 0.0
        if psutil:
            current = self._read_network_bytes()
            network = max(current - self.last_network, 0) / 1024.0
            self.last_network = current
        return {
            "cpu_percent": round(cpu, 1),
            "ram_percent": round(memory, 1),
            "network_kb": round(network, 1),
            "timestamp": time.time(),
        }

    def calculate_fitness(self, cpu_score: int, ram_score: int, responsiveness: int, network_score: int) -> int:
        base = round((cpu_score + ram_score + responsiveness + network_score) / 4)
        return max(0, min(100, base))

    def rating_label(self, fitness_score: int) -> str:
        if fitness_score >= 90:
            return "World Class"
        if fitness_score >= 75:
            return "Excellent"
        if fitness_score >= 60:
            return "Match Ready"
        if fitness_score >= 40:
            return "Needs Rotation"
        return "Injured"
