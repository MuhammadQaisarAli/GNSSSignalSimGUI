"""
IFDataGen Integration for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module handles the integration with IFDataGen.exe for signal generation.
"""

import os
import subprocess
import tempfile
import json
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from core.config.models import GNSSSignalSimConfig
from core.utils.logger import info, debug, error


class IFDataGenWorker(QThread):
    """Worker thread for running IFDataGen.exe."""

    progress_updated = pyqtSignal(int)  # Progress percentage
    status_updated = pyqtSignal(str)  # Status message
    finished = pyqtSignal(bool, str)  # Success, message
    output_received = pyqtSignal(str)  # Raw output from process

    def __init__(self, config_file: str, ifdatagen_path: str):
        super().__init__()
        self.config_file = config_file
        self.ifdatagen_path = ifdatagen_path
        self.process = None
        self._stop_requested = False

    def run(self):
        """Run IFDataGen.exe with the configuration file."""
        try:
            self.status_updated.emit("Starting IFDataGen...")
            self.progress_updated.emit(0)

            # Check if IFDataGen.exe exists
            if not os.path.exists(self.ifdatagen_path):
                self.finished.emit(
                    False, f"IFDataGen.exe not found at: {self.ifdatagen_path}"
                )
                return

            # Check if config file exists
            if not os.path.exists(self.config_file):
                self.finished.emit(
                    False, f"Configuration file not found: {self.config_file}"
                )
                return

            self.status_updated.emit("Executing IFDataGen...")
            self.progress_updated.emit(10)

            # Run IFDataGen.exe
            cmd = [self.ifdatagen_path, self.config_file]
            debug(f"Running command: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.path.dirname(self.ifdatagen_path),
            )

            # Read output line by line
            output_lines = []
            while True:
                if self._stop_requested:
                    self.process.terminate()
                    self.finished.emit(False, "Operation cancelled by user")
                    return

                output = self.process.stdout.readline()
                if output == "" and self.process.poll() is not None:
                    break

                if output:
                    line = output.strip()
                    output_lines.append(line)
                    self.output_received.emit(line)

                    # Try to extract progress information
                    self.parse_progress(line)

            # Wait for process to complete
            return_code = self.process.wait()

            if return_code == 0:
                self.progress_updated.emit(100)
                self.status_updated.emit("Signal generation completed successfully")
                self.finished.emit(True, "Signal generation completed successfully")
                info("IFDataGen completed successfully")
            else:
                error_msg = f"IFDataGen failed with return code {return_code}"
                if output_lines:
                    error_msg += (
                        f"\nOutput: {' '.join(output_lines[-5:])}"  # Last 5 lines
                    )
                self.finished.emit(False, error_msg)
                error(f"IFDataGen failed: {error_msg}")

        except Exception as e:
            error_msg = f"Error running IFDataGen: {str(e)}"
            self.finished.emit(False, error_msg)
            error(error_msg)

    def parse_progress(self, line: str):
        """Parse progress information from IFDataGen output."""
        # This is a simple progress parser - you may need to adjust based on actual IFDataGen output
        line_lower = line.lower()

        if "starting" in line_lower or "initializing" in line_lower:
            self.progress_updated.emit(20)
            self.status_updated.emit("Initializing...")
        elif "processing" in line_lower or "generating" in line_lower:
            self.progress_updated.emit(50)
            self.status_updated.emit("Generating signals...")
        elif "writing" in line_lower or "saving" in line_lower:
            self.progress_updated.emit(80)
            self.status_updated.emit("Writing output file...")
        elif "completed" in line_lower or "finished" in line_lower:
            self.progress_updated.emit(95)
            self.status_updated.emit("Finalizing...")

    def stop(self):
        """Request to stop the process."""
        self._stop_requested = True
        if self.process:
            self.process.terminate()


class IFDataGenIntegration(QObject):
    """Integration class for IFDataGen.exe."""

    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_finished = pyqtSignal(bool, str)
    output_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.ifdatagen_path = self.find_ifdatagen_executable()

    def find_ifdatagen_executable(self) -> Optional[str]:
        """Find IFDataGen.exe in common locations."""
        # Common locations to search for IFDataGen.exe
        search_paths = [
            "IFDataGen.exe",  # Current directory
            "bin/IFDataGen.exe",
            "tools/IFDataGen.exe",
            "../IFDataGen.exe",
            "C:/Program Files/SignalSim/IFDataGen.exe",
            "C:/Program Files (x86)/SignalSim/IFDataGen.exe",
        ]

        for path in search_paths:
            if os.path.exists(path):
                info(f"Found IFDataGen.exe at: {path}")
                return os.path.abspath(path)

        debug("IFDataGen.exe not found in common locations")
        return None

    def set_ifdatagen_path(self, path: str):
        """Set the path to IFDataGen.exe."""
        self.ifdatagen_path = path
        info(f"IFDataGen path set to: {path}")

    def is_available(self) -> bool:
        """Check if IFDataGen.exe is available."""
        return self.ifdatagen_path is not None and os.path.exists(self.ifdatagen_path)

    def generate_signals(
        self, config: GNSSSignalSimConfig, output_dir: Optional[str] = None
    ) -> bool:
        """Generate signals using IFDataGen.exe."""
        if not self.is_available():
            error("IFDataGen.exe is not available")
            self.generation_finished.emit(
                False, "IFDataGen.exe not found. Please set the correct path."
            )
            return False

        if self.worker and self.worker.isRunning():
            error("IFDataGen is already running")
            self.generation_finished.emit(
                False, "Signal generation is already in progress"
            )
            return False

        try:
            # Create temporary config file
            temp_dir = output_dir or tempfile.gettempdir()
            config_file = os.path.join(temp_dir, "temp_config.json")

            # Save configuration to temporary file
            config_dict = config.to_dict()
            with open(config_file, "w") as f:
                json.dump(config_dict, f, indent=2)

            info(f"Temporary config file created: {config_file}")

            # Create and start worker thread
            self.worker = IFDataGenWorker(config_file, self.ifdatagen_path)

            # Connect signals
            self.worker.progress_updated.connect(self.progress_updated)
            self.worker.status_updated.connect(self.status_updated)
            self.worker.finished.connect(self.on_generation_finished)
            self.worker.output_received.connect(self.output_received)

            # Start generation
            self.worker.start()
            info("Signal generation started")
            return True

        except Exception as e:
            error_msg = f"Error starting signal generation: {str(e)}"
            error(error_msg)
            self.generation_finished.emit(False, error_msg)
            return False

    def on_generation_finished(self, success: bool, message: str):
        """Handle generation completion."""
        # Clean up temporary files if needed
        if self.worker:
            temp_config = self.worker.config_file
            if os.path.exists(temp_config) and "temp_config.json" in temp_config:
                try:
                    os.remove(temp_config)
                    debug(f"Cleaned up temporary config file: {temp_config}")
                except Exception as e:
                    debug(f"Failed to clean up temporary file: {e}")

        self.generation_finished.emit(success, message)

    def stop_generation(self):
        """Stop the current signal generation."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(5000)  # Wait up to 5 seconds
            info("Signal generation stopped")

    def get_status(self) -> str:
        """Get current generation status."""
        if self.worker and self.worker.isRunning():
            return "Running"
        return "Idle"


# Global integration instance
ifdatagen_integration = IFDataGenIntegration()
