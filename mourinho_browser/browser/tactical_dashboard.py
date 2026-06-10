from typing import Dict, List

from browser.fitness_monitor import FitnessMonitor
from browser.tab_manager import TabManager
from database.database import Database


class TacticalDashboard:
    def __init__(self, fitness_monitor: FitnessMonitor, tab_manager: TabManager):
        self.fitness_monitor = fitness_monitor
        self.tab_manager = tab_manager

    def get_dashboard_data(self) -> Dict:
        system_metrics = self.fitness_monitor.get_system_metrics()
        active_tabs = [t for t in self.tab_manager.list_tabs(include_benched=False)]
        benched_tabs = [t for t in self.tab_manager.list_tabs(include_benched=True) if t["benched"] == 1]
        network_score = 100 - min(100, int(system_metrics["network_kb"]))
        fitness = self.fitness_monitor.calculate_fitness(
            cpu_score=int(100 - system_metrics["cpu_percent"]),
            ram_score=int(100 - system_metrics["ram_percent"]),
            responsiveness=100,
            network_score=network_score,
        )
        return {
            "system": system_metrics,
            "fitness_score": fitness,
            "fitness_label": self.fitness_monitor.rating_label(fitness),
            "active_tabs": len(active_tabs),
            "benched_tabs": len(benched_tabs),
            "active_tab_details": active_tabs,
            "benched_tab_details": benched_tabs,
        }

    def get_extension_usage(self) -> List[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT name, enabled, installed_at FROM extensions ORDER BY installed_at DESC")
        return [dict(row) for row in cursor.fetchall()]
