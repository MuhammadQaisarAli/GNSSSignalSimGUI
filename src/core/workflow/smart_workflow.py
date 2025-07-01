"""
Smart Workflow Manager for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides intelligent workflow guidance without blocking user navigation.
It offers helpful hints, progress tracking, and validation feedback while keeping
all functionality accessible.

Based on Config File Generation Steps.md workflow requirements.
"""

from enum import Enum
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from ..utils.logger import debug, info


class WorkflowStep(Enum):
    """Workflow steps in GNSSSignalSim configuration."""
    BASIC_INFO = "basic_info"
    EPHEMERIS_LOADING = "ephemeris_loading"
    TIME_VALIDATION = "time_validation"
    TRAJECTORY_CONFIG = "trajectory_config"
    SIGNAL_SELECTION = "signal_selection"
    POWER_CONFIG = "power_config"
    OUTPUT_SETTINGS = "output_settings"


class ValidationLevel(Enum):
    """Validation levels for user feedback."""
    SUCCESS = "success"      # Everything is good
    WARNING = "warning"      # Potential issues, but can proceed
    ERROR = "error"         # Issues that should be addressed
    INFO = "info"           # Helpful information
    INCOMPLETE = "incomplete" # Step not yet completed


@dataclass
class StepFeedback:
    """Feedback information for a workflow step."""
    step: WorkflowStep
    level: ValidationLevel
    title: str
    message: str
    suggestion: str = ""
    completion_percentage: int = 0
    can_proceed: bool = True  # Always True - we don't block navigation


class SmartWorkflowManager(QObject):
    """Smart workflow manager that guides without blocking."""
    
    # Signals for UI updates
    step_feedback_changed = pyqtSignal(WorkflowStep, ValidationLevel, str, str)
    overall_progress_changed = pyqtSignal(int)
    workflow_summary_changed = pyqtSignal(str)  # Summary message for status bar
    
    def __init__(self):
        super().__init__()
        self.step_feedback: Dict[WorkflowStep, StepFeedback] = {}
        self.validation_callbacks: Dict[WorkflowStep, Callable] = {}
        
        # Throttling for validation
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._perform_validation)
        self.validation_pending = False
        
        # Initialize step feedback
        self._initialize_feedback()
        
        info("SmartWorkflowManager initialized")

    def _initialize_feedback(self):
        """Initialize all workflow steps with default feedback."""
        step_info = {
            WorkflowStep.BASIC_INFO: ("Basic Information", "Configure project metadata"),
            WorkflowStep.EPHEMERIS_LOADING: ("Ephemeris Files", "Load satellite ephemeris data"),
            WorkflowStep.TIME_VALIDATION: ("Time Configuration", "Set simulation time within ephemeris range"),
            WorkflowStep.TRAJECTORY_CONFIG: ("Trajectory Setup", "Define receiver movement path"),
            WorkflowStep.SIGNAL_SELECTION: ("Signal Selection", "Choose GNSS signals to simulate"),
            WorkflowStep.POWER_CONFIG: ("Power Settings", "Configure signal power levels"),
            WorkflowStep.OUTPUT_SETTINGS: ("Output Configuration", "Set output file and format"),
        }
        
        for step, (title, message) in step_info.items():
            self.step_feedback[step] = StepFeedback(
                step=step,
                level=ValidationLevel.INCOMPLETE,
                title=title,
                message=message,
                suggestion="Click on the corresponding tab to configure this step.",
                completion_percentage=0,
                can_proceed=True
            )

    def register_validation_callback(self, step: WorkflowStep, callback: Callable):
        """Register a validation callback for a workflow step."""
        self.validation_callbacks[step] = callback
        debug(f"Registered validation callback for {step.value}")

    def request_validation(self, delay_ms: int = 500):
        """Request validation with throttling to prevent excessive calls."""
        self.validation_pending = True
        self.validation_timer.start(delay_ms)

    def _perform_validation(self):
        """Perform validation for all steps."""
        if not self.validation_pending:
            return
            
        self.validation_pending = False
        
        for step in WorkflowStep:
            if step in self.validation_callbacks:
                try:
                    self.validation_callbacks[step]()
                except Exception as e:
                    debug(f"Error in validation callback for {step.value}: {e}")
                    self.update_step_feedback(
                        step, 
                        ValidationLevel.ERROR,
                        "Validation Error",
                        f"Error checking {step.value}: {str(e)}",
                        "Please check the configuration and try again."
                    )

    def update_step_feedback(self, step: WorkflowStep, level: ValidationLevel, 
                           title: str, message: str, suggestion: str = "",
                           completion_percentage: int = 0):
        """Update feedback for a workflow step."""
        if step not in self.step_feedback:
            return
        
        feedback = self.step_feedback[step]
        feedback.level = level
        feedback.title = title
        feedback.message = message
        feedback.suggestion = suggestion
        feedback.completion_percentage = completion_percentage
        
        # Emit signals for UI updates
        self.step_feedback_changed.emit(step, level, title, message)
        self._update_overall_progress()
        self._update_workflow_summary()
        
        debug(f"Updated feedback for {step.value}: {level.value} - {title}")

    def _update_overall_progress(self):
        """Calculate and emit overall workflow progress."""
        total_steps = len(WorkflowStep)
        total_completion = 0
        
        for feedback in self.step_feedback.values():
            if feedback.level == ValidationLevel.SUCCESS:
                total_completion += 100
            elif feedback.level in [ValidationLevel.WARNING, ValidationLevel.INFO]:
                total_completion += 80  # Mostly complete
            else:
                total_completion += feedback.completion_percentage
        
        progress_percentage = int(total_completion / total_steps)
        self.overall_progress_changed.emit(progress_percentage)

    def _update_workflow_summary(self):
        """Generate and emit workflow summary for status bar."""
        # Count step statuses
        success_count = sum(1 for f in self.step_feedback.values() if f.level == ValidationLevel.SUCCESS)
        error_count = sum(1 for f in self.step_feedback.values() if f.level == ValidationLevel.ERROR)
        warning_count = sum(1 for f in self.step_feedback.values() if f.level == ValidationLevel.WARNING)
        
        total_steps = len(WorkflowStep)
        
        if success_count == total_steps:
            summary = "All workflow steps complete! Ready to generate signals."
        elif error_count > 0:
            next_error_step = self._get_next_step_with_level(ValidationLevel.ERROR)
            if next_error_step:
                step_name = next_error_step.value.replace('_', ' ').title()
                summary = f"Issues in {step_name}. Check the {step_name} tab."
            else:
                summary = f"{error_count} step(s) need attention."
        elif warning_count > 0:
            summary = f"{warning_count} step(s) have warnings. Configuration is usable."
        else:
            next_incomplete = self._get_next_step_with_level(ValidationLevel.INCOMPLETE)
            if next_incomplete:
                step_name = next_incomplete.value.replace('_', ' ').title()
                summary = f"Next: Configure {step_name}"
            else:
                summary = f"{success_count}/{total_steps} steps complete"
        
        self.workflow_summary_changed.emit(summary)

    def _get_next_step_with_level(self, level: ValidationLevel) -> Optional[WorkflowStep]:
        """Get the next step with the specified validation level."""
        for step in WorkflowStep:
            if self.step_feedback[step].level == level:
                return step
        return None

    def get_step_feedback(self, step: WorkflowStep) -> StepFeedback:
        """Get current feedback for a workflow step."""
        return self.step_feedback.get(step, StepFeedback(
            step, ValidationLevel.INCOMPLETE, "Unknown", "No feedback available"
        ))

    def get_overall_progress(self) -> int:
        """Get overall workflow progress percentage."""
        total_steps = len(WorkflowStep)
        total_completion = sum(f.completion_percentage for f in self.step_feedback.values())
        return int(total_completion / total_steps)

    def get_workflow_status(self) -> Dict[str, any]:
        """Get comprehensive workflow status."""
        return {
            'overall_progress': self.get_overall_progress(),
            'step_feedback': {step.value: {
                'level': feedback.level.value,
                'title': feedback.title,
                'message': feedback.message,
                'suggestion': feedback.suggestion,
                'completion': feedback.completion_percentage
            } for step, feedback in self.step_feedback.items()},
            'summary': self._generate_summary()
        }

    def _generate_summary(self) -> str:
        """Generate a comprehensive workflow summary."""
        success_steps = [s for s, f in self.step_feedback.items() if f.level == ValidationLevel.SUCCESS]
        error_steps = [s for s, f in self.step_feedback.items() if f.level == ValidationLevel.ERROR]
        warning_steps = [s for s, f in self.step_feedback.items() if f.level == ValidationLevel.WARNING]
        
        summary_parts = []
        
        if success_steps:
            summary_parts.append(f"Completed: {len(success_steps)} steps")
        
        if error_steps:
            summary_parts.append(f"Issues: {len(error_steps)} steps")
        
        if warning_steps:
            summary_parts.append(f"Warnings: {len(warning_steps)} steps")
        
        return " | ".join(summary_parts) if summary_parts else "Ready to configure"

    def get_next_recommended_step(self) -> Optional[WorkflowStep]:
        """Get the next recommended step for the user."""
        # Priority: Errors first, then incomplete, then warnings
        for level in [ValidationLevel.ERROR, ValidationLevel.INCOMPLETE, ValidationLevel.WARNING]:
            step = self._get_next_step_with_level(level)
            if step:
                return step
        return None

    def validate_all_steps(self):
        """Trigger validation for all steps with throttling."""
        self.request_validation(100)  # Short delay for immediate validation

    def get_step_icon(self, step: WorkflowStep) -> str:
        """Get an icon/emoji for the step based on its status."""
        feedback = self.step_feedback.get(step)
        if not feedback:
            return "?"
        
        icon_map = {
            ValidationLevel.SUCCESS: "✓",
            ValidationLevel.WARNING: "!",
            ValidationLevel.ERROR: "✗",
            ValidationLevel.INFO: "i",
            ValidationLevel.INCOMPLETE: "○"
        }
        
        return icon_map.get(feedback.level, "?")


# Global smart workflow manager instance
smart_workflow_manager = SmartWorkflowManager()


def get_smart_workflow_manager() -> SmartWorkflowManager:
    """Get the global smart workflow manager instance."""
    return smart_workflow_manager


def update_step_feedback(step: WorkflowStep, level: ValidationLevel, 
                        title: str, message: str, suggestion: str = "",
                        completion_percentage: int = 0):
    """Convenience function to update step feedback."""
    smart_workflow_manager.update_step_feedback(
        step, level, title, message, suggestion, completion_percentage
    )


def register_smart_validation_callback(step: WorkflowStep, callback: Callable):
    """Convenience function to register validation callback."""
    smart_workflow_manager.register_validation_callback(step, callback)