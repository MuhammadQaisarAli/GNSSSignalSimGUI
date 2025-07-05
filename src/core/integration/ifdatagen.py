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
from core.utils.settings import get_ifdatagen_executable_path, get_generated_output_path, get_default_path


class IFDataGenWorker(QThread):
    """Worker thread for running IFDataGen.exe."""

    progress_updated = pyqtSignal(int)  # Progress percentage
    status_updated = pyqtSignal(str)  # Status message
    finished = pyqtSignal(bool, str)  # Success, message
    output_received = pyqtSignal(str)  # Raw output from process

    def __init__(self, config_file: str, ifdatagen_path: str, working_dir: str = None, create_tag_file: bool = False):
        super().__init__()
        self.config_file = config_file
        self.ifdatagen_path = ifdatagen_path
        self.working_dir = working_dir or os.path.dirname(self.ifdatagen_path)
        self.create_tag_file = create_tag_file
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

            # Run IFDataGen.exe with config file argument
            # Convert config file path to be relative to working directory if possible
            try:
                rel_config_path = os.path.relpath(self.config_file, self.working_dir)
                if not rel_config_path.startswith('..'):
                    config_arg = rel_config_path
                else:
                    config_arg = os.path.abspath(self.config_file)
            except:
                config_arg = os.path.abspath(self.config_file)
            
            cmd = [self.ifdatagen_path, "--config", config_arg]
            if self.create_tag_file:
                cmd.append("-t")
            debug(f"Running command: {' '.join(cmd)}")
            debug(f"Working directory: {self.working_dir}")
            debug(f"Config file path: {self.config_file}")
            debug(f"Config argument: {config_arg}")
            debug(f"Config file exists: {os.path.exists(self.config_file)}")
            debug(f"Executable exists: {os.path.exists(self.ifdatagen_path)}")
            debug(f"Working dir exists: {os.path.exists(self.working_dir)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.working_dir,  # Run from the target output directory
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
        """Find IFDataGen.exe using settings system."""
        # First try to get from settings
        exe_path = get_ifdatagen_executable_path()
        if exe_path:
            info(f"Found IFDataGen.exe from settings: {exe_path}")
            return exe_path

        # Fallback to common locations
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
        self, config: GNSSSignalSimConfig, output_dir: Optional[str] = None, create_tag_file: bool = False
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
            # Use provided output directory or create one based on config
            if output_dir:
                working_dir = output_dir
            else:
                # Get output type and filename from config
                output_type = getattr(config.output, 'type', 'IF_DATA')
                output_type_str = output_type.value if hasattr(output_type, 'value') else str(output_type)
                
                if config.output.name:
                    filename = os.path.basename(config.output.name)
                    name_without_ext = os.path.splitext(filename)[0]
                    working_dir = get_generated_output_path(output_type_str, name_without_ext, create_dir=True)
                else:
                    working_dir = get_generated_output_path(output_type_str, "default_output", create_dir=True)

            # Ensure output directory exists (in case it wasn't created by Generate tab)
            working_dir = os.path.normpath(working_dir)
            os.makedirs(working_dir, exist_ok=True)
            
            # Create config file in the configs directory (not in output directory)
            configs_dir = get_default_path("config")
            os.makedirs(configs_dir, exist_ok=True)
            
            # Use single temp.json file for all generations
            config_filename = "temp.json"
            config_file = os.path.join(configs_dir, config_filename)
            # Normalize path separators for current OS
            config_file = os.path.normpath(config_file)

            # Update config to use relative paths for IFDataGen
            config_dict = config.to_dict()
            
            # Set output file as just filename (since IFDataGen will run from working_dir)
            if config.output.name:
                filename = os.path.basename(config.output.name)
                # Remove any path separators and use only filename
                filename = filename.replace('\\', '').replace('/', '')
                config_dict['output']['name'] = filename
            
            # Save configuration file
            with open(config_file, "w", encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            # Verify the file was created and is readable
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r", encoding='utf-8') as f:
                        test_load = json.load(f)
                    info(f"Config file created and verified: {config_file}")
                except Exception as e:
                    error(f"Config file created but not readable: {e}")
            else:
                error(f"Config file was not created: {config_file}")
            
            info(f"Working directory: {working_dir}")
            debug(f"Config file content preview: {json.dumps(config_dict, indent=2)[:200]}...")

            # Create and start worker thread (pass working directory for execution)
            self.worker = IFDataGenWorker(config_file, self.ifdatagen_path, working_dir, create_tag_file)

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
        if success:
            # Add information about output location
            if self.worker:
                output_dir = self.worker.working_dir
                message += f"\n\nOutput files saved to:\n{output_dir}"
                message += f"\n\nTemporary config used: temp.json"
        
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
    
    def cleanup_temp_files(self):
        """Clean up temporary config files."""
        try:
            configs_dir = get_default_path("config")
            temp_config = os.path.join(configs_dir, "temp.json")
            if os.path.exists(temp_config):
                os.remove(temp_config)
                debug(f"Cleaned up temporary config file: {temp_config}")
        except Exception as e:
            debug(f"Failed to clean up temporary config file: {e}")


# Global integration instance
ifdatagen_integration = IFDataGenIntegration()
