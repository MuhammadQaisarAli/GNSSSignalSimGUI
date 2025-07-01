"""
Workflow Manager for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module manages the workflow state and tab enabling/disabling based on
configuration validation status, following the Config File Generation Steps.

Based on Config File Generation Steps.md workflow requirements.
"""

from enum import Enum
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from ..utils.logger import debug, info


class WorkflowStep(Enum):
    """Workflow steps in SignalSim configuration."""
    BASIC_INFO = "basic_info"
    EPHEMERIS_LOADING = "ephemeris_loading"
    TIME_VALIDATION = "time_validation"
    TRAJECTORY_CONFIG = "trajectory_config"
    SIGNAL_SELECTION = "signal_selection"
    POWER_CONFIG = "power_config"
    OUTPUT_SETTINGS = "output_settings"


class ValidationStatus(Enum):
    """Validation status for workflow steps."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class StepStatus:
    """Status information for a workflow step."""
    step: WorkflowStep
    status: ValidationStatus
    message: str = ""
    details: str = ""
    can_proceed: bool = False
    completion_percentage: int = 0


class WorkflowManager(QObject):
    """Manages workflow state and tab enabling logic."""
    
    # Signals for UI updates
    step_status_changed = pyqtSignal(WorkflowStep, ValidationStatus, str)
    workflow_progress_changed = pyqtSignal(int)  # Overall progress percentage
    tab_state_changed = pyqtSignal(str, bool)  # tab_name, enabled
    
    def __init__(self):
        super().__init__()
        self.step_statuses: Dict[WorkflowStep, StepStatus] = {}
        self.validation_callbacks: Dict[WorkflowStep, Callable] = {}
        self.tab_mapping: Dict[WorkflowStep, str] = {
            WorkflowStep.BASIC_INFO: "Basic",
            WorkflowStep.EPHEMERIS_LOADING: "Ephemeris & Time",
            # TIME_VALIDATION is handled within the Ephemeris & Time tab, no separate mapping
            WorkflowStep.TRAJECTORY_CONFIG: "Trajectory",
            WorkflowStep.SIGNAL_SELECTION: "Signal Selection",
            WorkflowStep.POWER_CONFIG: "Signal Power",
            WorkflowStep.OUTPUT_SETTINGS: "Output Settings",
        }
        
        # Initialize step statuses
        self._initialize_steps()
        
        info("WorkflowManager initialized")

    def _initialize_steps(self):
        """Initialize all workflow steps with default status."""
        for step in WorkflowStep:
            self.step_statuses[step] = StepStatus(
                step=step,
                status=ValidationStatus.NOT_STARTED,
                message="Not started",
                can_proceed=False
            )
        
        # Basic info is always available
        self.step_statuses[WorkflowStep.BASIC_INFO].status = ValidationStatus.VALID
        self.step_statuses[WorkflowStep.BASIC_INFO].can_proceed = True
        self.step_statuses[WorkflowStep.BASIC_INFO].completion_percentage = 100
        
        # Ephemeris loading is always available
        self.step_statuses[WorkflowStep.EPHEMERIS_LOADING].status = ValidationStatus.VALID
        self.step_statuses[WorkflowStep.EPHEMERIS_LOADING].can_proceed = True

    def register_validation_callback(self, step: WorkflowStep, callback: Callable):
        """Register a validation callback for a workflow step."""
        self.validation_callbacks[step] = callback
        debug(f"Registered validation callback for {step.value}")

    def update_step_status(self, step: WorkflowStep, status: ValidationStatus, 
                          message: str = "", details: str = "", 
                          completion_percentage: int = 0):
        """Update the status of a workflow step."""
        if step not in self.step_statuses:
            return
        
        step_status = self.step_statuses[step]
        step_status.status = status
        step_status.message = message
        step_status.details = details
        step_status.completion_percentage = completion_percentage
        
        # Determine if this step allows proceeding
        step_status.can_proceed = self._can_step_proceed(step, status)
        
        # Update dependent steps
        self._update_dependent_steps(step)
        
        # Emit signals
        self.step_status_changed.emit(step, status, message)
        self._update_tab_states()
        self._update_overall_progress()
        
        debug(f"Updated {step.value}: {status.value} - {message}")

    def _can_step_proceed(self, step: WorkflowStep, status: ValidationStatus) -> bool:
        """Determine if a step allows proceeding to next steps."""
        if step == WorkflowStep.BASIC_INFO:
            return True  # Always can proceed from basic info
        elif step == WorkflowStep.EPHEMERIS_LOADING:
            return status == ValidationStatus.VALID
        elif step == WorkflowStep.TIME_VALIDATION:
            return status == ValidationStatus.VALID
        else:
            return status == ValidationStatus.VALID

    def _update_dependent_steps(self, updated_step: WorkflowStep):
        """Update dependent steps based on the updated step."""
        if updated_step == WorkflowStep.EPHEMERIS_LOADING:
            # If ephemeris loading changes, update time validation
            if self.step_statuses[updated_step].status == ValidationStatus.VALID:
                # Trigger time validation
                self._trigger_validation(WorkflowStep.TIME_VALIDATION)
            else:
                # Reset time validation and all subsequent steps
                self._reset_subsequent_steps(WorkflowStep.TIME_VALIDATION)
        
        elif updated_step == WorkflowStep.TIME_VALIDATION:
            if self.step_statuses[updated_step].status != ValidationStatus.VALID:
                # Reset all subsequent steps
                self._reset_subsequent_steps(WorkflowStep.TRAJECTORY_CONFIG)

    def _reset_subsequent_steps(self, from_step: WorkflowStep):
        """Reset all steps from the given step onwards."""
        step_order = list(WorkflowStep)
        from_index = step_order.index(from_step)
        
        for step in step_order[from_index:]:
            if step != from_step:  # Don't reset the from_step itself
                self.step_statuses[step].status = ValidationStatus.NOT_STARTED
                self.step_statuses[step].message = "Waiting for prerequisites"
                self.step_statuses[step].can_proceed = False
                self.step_statuses[step].completion_percentage = 0

    def _trigger_validation(self, step: WorkflowStep):
        """Trigger validation for a specific step."""
        if step in self.validation_callbacks:
            try:
                self.validation_callbacks[step]()
            except Exception as e:
                debug(f"Error in validation callback for {step.value}: {e}")
                self.update_step_status(step, ValidationStatus.ERROR, 
                                      f"Validation error: {str(e)}")

    def _update_tab_states(self):
        """Update tab enabled/disabled states based on workflow."""
        for step, tab_name in self.tab_mapping.items():
            enabled = self._is_tab_enabled(step)
            self.tab_state_changed.emit(tab_name, enabled)
        
        # Handle TIME_VALIDATION separately since it shares a tab with EPHEMERIS_LOADING
        # but we don't want to emit duplicate signals for the same tab

    def _is_tab_enabled(self, step: WorkflowStep) -> bool:
        """Determine if a tab should be enabled based on workflow state."""
        # For now, let's enable all tabs to fix the navigation issue
        # We can implement progressive enabling later if needed
        return True
        
        # Original logic (commented out for now):
        # if step in [WorkflowStep.BASIC_INFO, WorkflowStep.EPHEMERIS_LOADING]:
        #     return True  # Always enabled
        # 
        # # Check prerequisites
        # step_order = list(WorkflowStep)
        # step_index = step_order.index(step)
        # 
        # # Check all previous steps
        # for i in range(step_index):
        #     prev_step = step_order[i]
        #     if not self.step_statuses[prev_step].can_proceed:
        #         return False
        # 
        # return True

    def _update_overall_progress(self):
        """Calculate and emit overall workflow progress."""
        total_steps = len(WorkflowStep)
        completed_steps = 0
        
        for step_status in self.step_statuses.values():
            if step_status.status == ValidationStatus.VALID:
                completed_steps += 1
            elif step_status.status == ValidationStatus.IN_PROGRESS:
                completed_steps += 0.5
        
        progress_percentage = int((completed_steps / total_steps) * 100)
        self.workflow_progress_changed.emit(progress_percentage)

    def get_step_status(self, step: WorkflowStep) -> StepStatus:
        """Get the current status of a workflow step."""
        return self.step_statuses.get(step, StepStatus(step, ValidationStatus.NOT_STARTED))

    def get_overall_progress(self) -> int:
        """Get overall workflow progress percentage."""
        total_steps = len(WorkflowStep)
        completed_steps = sum(1 for status in self.step_statuses.values() 
                            if status.status == ValidationStatus.VALID)
        return int((completed_steps / total_steps) * 100)

    def get_next_required_step(self) -> Optional[WorkflowStep]:
        """Get the next step that requires attention."""
        for step in WorkflowStep:
            status = self.step_statuses[step]
            if status.status in [ValidationStatus.NOT_STARTED, ValidationStatus.INVALID, ValidationStatus.ERROR]:
                return step
        return None

    def is_workflow_complete(self) -> bool:
        """Check if the entire workflow is complete."""
        return all(status.status == ValidationStatus.VALID 
                  for status in self.step_statuses.values())

    def get_workflow_summary(self) -> Dict[str, any]:
        """Get a summary of the current workflow state."""
        return {
            'overall_progress': self.get_overall_progress(),
            'is_complete': self.is_workflow_complete(),
            'next_step': self.get_next_required_step(),
            'step_statuses': {step.value: {
                'status': status.status.value,
                'message': status.message,
                'can_proceed': status.can_proceed,
                'completion': status.completion_percentage
            } for step, status in self.step_statuses.items()}
        }

    def validate_all_steps(self):
        """Trigger validation for all steps that have callbacks."""
        for step in WorkflowStep:
            if step in self.validation_callbacks:
                self._trigger_validation(step)

    def reset_workflow(self):
        """Reset the entire workflow to initial state."""
        self._initialize_steps()
        self._update_tab_states()
        self._update_overall_progress()
        info("Workflow reset to initial state")


# Global workflow manager instance
workflow_manager = WorkflowManager()


def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager instance."""
    return workflow_manager


def update_step_status(step: WorkflowStep, status: ValidationStatus, 
                      message: str = "", details: str = "", 
                      completion_percentage: int = 0):
    """Convenience function to update step status."""
    workflow_manager.update_step_status(step, status, message, details, completion_percentage)


def register_validation_callback(step: WorkflowStep, callback: Callable):
    """Convenience function to register validation callback."""
    workflow_manager.register_validation_callback(step, callback)