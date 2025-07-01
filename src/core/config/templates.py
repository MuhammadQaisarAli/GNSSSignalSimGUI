"""
Template Manager for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module handles pre-defined configuration templates and custom template management.
"""

import os
import json
from typing import Dict, List, Optional
from core.config.models import (
    GNSSSignalSimConfig,
    get_default_system_select,
    SystemSelect,
    ConstellationType,
)
from core.utils.logger import info, error


class TemplateManager:
    """Manages configuration templates for SignalSim."""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.ensure_templates_dir()
        self.built_in_templates = self._create_built_in_templates()

    def ensure_templates_dir(self):
        """Ensure templates directory exists."""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            info(f"Created templates directory: {self.templates_dir}")

    def _create_built_in_templates(self) -> Dict[str, GNSSSignalSimConfig]:
        """Create built-in configuration templates."""
        templates = {}

        # Urban Navigation Template
        urban_config = GNSSSignalSimConfig()
        urban_config.description = "Urban Navigation Scenario"
        urban_config.comment = "Multi-constellation configuration for urban navigation with typical signal conditions"
        urban_config.trajectory.name = "Urban Vehicle"
        urban_config.trajectory.init_position.latitude = 37.7749
        urban_config.trajectory.init_position.longitude = -122.4194
        urban_config.trajectory.init_position.altitude = 50.0
        urban_config.trajectory.init_velocity.speed = 15.0  # 15 m/s (54 km/h)
        urban_config.trajectory.init_velocity.course = 45.0
        urban_config.output.config.elevation_mask = 10.0  # Higher mask for urban
        urban_config.power.noise_floor = -170.0  # Urban noise
        urban_config.output.system_select = [
            SystemSelect(ConstellationType.GPS, "L1CA", True),
            SystemSelect(ConstellationType.GPS, "L5", True),
            SystemSelect(ConstellationType.GALILEO, "E1", True),
            SystemSelect(ConstellationType.GALILEO, "E5a", True),
            SystemSelect(ConstellationType.BDS, "B1C", True),
            SystemSelect(ConstellationType.BDS, "B2a", True),
        ]
        templates["Urban Navigation"] = urban_config

        # Rural/Open Sky Template
        rural_config = GNSSSignalSimConfig()
        rural_config.description = "Rural Open Sky Scenario"
        rural_config.comment = (
            "High-precision configuration for rural/open sky environments"
        )
        rural_config.trajectory.name = "Rural Vehicle"
        rural_config.trajectory.init_position.latitude = 40.7128
        rural_config.trajectory.init_position.longitude = -74.0060
        rural_config.trajectory.init_position.altitude = 100.0
        rural_config.trajectory.init_velocity.speed = 25.0  # 25 m/s (90 km/h)
        rural_config.trajectory.init_velocity.course = 0.0
        rural_config.output.config.elevation_mask = 5.0  # Lower mask for open sky
        rural_config.power.noise_floor = -174.0  # Ideal noise floor
        rural_config.output.system_select = get_default_system_select()
        # Enable all major signals for rural
        for system_select in rural_config.output.system_select:
            if system_select.signal in ["L1CA", "L5", "E1", "E5a", "B1C", "B2a", "G1"]:
                system_select.enable = True
        templates["Rural Open Sky"] = rural_config

        # Aviation Template
        aviation_config = GNSSSignalSimConfig()
        aviation_config.description = "Aviation Scenario"
        aviation_config.comment = (
            "High-altitude aviation configuration with SBAS signals"
        )
        aviation_config.trajectory.name = "Aircraft"
        aviation_config.trajectory.init_position.latitude = 51.4700
        aviation_config.trajectory.init_position.longitude = -0.4543
        aviation_config.trajectory.init_position.altitude = 10000.0  # 10km altitude
        aviation_config.trajectory.init_velocity.speed = 250.0  # 250 m/s (900 km/h)
        aviation_config.trajectory.init_velocity.course = 90.0
        aviation_config.output.config.elevation_mask = (
            0.0  # No elevation mask for aviation
        )
        aviation_config.power.noise_floor = -174.0
        aviation_config.power.elevation_adjust = True  # Enable elevation adjustment
        aviation_config.output.system_select = [
            SystemSelect(ConstellationType.GPS, "L1CA", True),
            SystemSelect(ConstellationType.GPS, "L1C", True),
            SystemSelect(ConstellationType.GPS, "L5", True),
            SystemSelect(ConstellationType.GALILEO, "E1", True),
            SystemSelect(ConstellationType.GALILEO, "E5a", True),
        ]
        templates["Aviation"] = aviation_config

        # Maritime Template
        maritime_config = GNSSSignalSimConfig()
        maritime_config.description = "Maritime Navigation Scenario"
        maritime_config.comment = (
            "Marine navigation configuration with moderate dynamics"
        )
        maritime_config.trajectory.name = "Vessel"
        maritime_config.trajectory.init_position.latitude = 35.6762
        maritime_config.trajectory.init_position.longitude = 139.6503
        maritime_config.trajectory.init_position.altitude = 0.0  # Sea level
        maritime_config.trajectory.init_velocity.speed = 10.0  # 10 m/s (36 km/h)
        maritime_config.trajectory.init_velocity.course = 180.0
        maritime_config.output.config.elevation_mask = 5.0
        maritime_config.power.noise_floor = -172.0  # Marine environment noise
        maritime_config.output.system_select = [
            SystemSelect(ConstellationType.GPS, "L1CA", True),
            SystemSelect(ConstellationType.GPS, "L2C", True),
            SystemSelect(ConstellationType.GLONASS, "G1", True),
            SystemSelect(ConstellationType.BDS, "B1I", True),
            SystemSelect(ConstellationType.GALILEO, "E1", True),
        ]
        templates["Maritime"] = maritime_config

        # Testing Template
        testing_config = GNSSSignalSimConfig()
        testing_config.description = "Testing and Validation Scenario"
        testing_config.comment = (
            "Minimal configuration for testing and validation purposes"
        )
        testing_config.trajectory.name = "Test Scenario"
        testing_config.trajectory.init_position.latitude = 0.0
        testing_config.trajectory.init_position.longitude = 0.0
        testing_config.trajectory.init_position.altitude = 0.0
        testing_config.trajectory.init_velocity.speed = 0.0
        testing_config.trajectory.init_velocity.course = 0.0
        testing_config.output.config.elevation_mask = 5.0
        testing_config.power.noise_floor = -174.0
        testing_config.output.system_select = [
            SystemSelect(ConstellationType.GPS, "L1CA", True),
        ]
        templates["Testing"] = testing_config

        return templates

    def get_template_names(self) -> List[str]:
        """Get list of available template names."""
        built_in_names = list(self.built_in_templates.keys())
        custom_names = self.get_custom_template_names()
        return built_in_names + custom_names

    def get_custom_template_names(self) -> List[str]:
        """Get list of custom template names."""
        custom_names = []
        try:
            for filename in os.listdir(self.templates_dir):
                if filename.endswith(".json"):
                    template_name = filename[:-5]  # Remove .json extension
                    custom_names.append(template_name)
        except OSError as e:
            error(f"Error reading templates directory: {e}")
        return custom_names

    def get_template(self, name: str) -> Optional[GNSSSignalSimConfig]:
        """Get a template by name."""
        # Check built-in templates first
        if name in self.built_in_templates:
            return self.built_in_templates[name]

        # Check custom templates
        template_path = os.path.join(self.templates_dir, f"{name}.json")
        if os.path.exists(template_path):
            try:
                with open(template_path, "r") as f:
                    data = json.load(f)
                return GNSSSignalSimConfig.from_dict(data)
            except Exception as e:
                error(f"Error loading template '{name}': {e}")
                return None

        return None

    def save_template(self, name: str, config: GNSSSignalSimConfig) -> bool:
        """Save a configuration as a custom template."""
        try:
            template_path = os.path.join(self.templates_dir, f"{name}.json")
            config_dict = config.to_dict()

            with open(template_path, "w") as f:
                json.dump(config_dict, f, indent=2)

            info(f"Template '{name}' saved successfully")
            return True
        except Exception as e:
            error(f"Error saving template '{name}': {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """Delete a custom template."""
        # Don't allow deletion of built-in templates
        if name in self.built_in_templates:
            error(f"Cannot delete built-in template '{name}'")
            return False

        template_path = os.path.join(self.templates_dir, f"{name}.json")
        try:
            if os.path.exists(template_path):
                os.remove(template_path)
                info(f"Template '{name}' deleted successfully")
                return True
            else:
                error(f"Template '{name}' not found")
                return False
        except Exception as e:
            error(f"Error deleting template '{name}': {e}")
            return False

    def is_built_in_template(self, name: str) -> bool:
        """Check if a template is a built-in template."""
        return name in self.built_in_templates

    def get_template_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get template information (description, comment, etc.)."""
        template = self.get_template(name)
        if template:
            return {
                "name": name,
                "description": template.description,
                "comment": template.comment,
                "type": "Built-in" if self.is_built_in_template(name) else "Custom",
            }
        return None


# Global template manager instance
template_manager = TemplateManager()
