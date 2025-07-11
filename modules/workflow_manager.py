import time
from typing import List, Dict, Any, Optional

class WorkflowManager:
    def __init__(self, controller):
        """Initialize workflow manager with reference to controller"""
        self.controller = controller
        self.workflows = {}
        
    def create_workflow(self, name: str, commands: List[str]) -> bool:
        """Create a new automation workflow with a sequence of commands"""
        if name in self.workflows:
            print(f"Workflow '{name}' already exists. Use update_workflow to modify.")
            return False
            
        self.workflows[name] = {
            'commands': commands,
            'created': time.strftime("%Y-%m-%d %H:%M:%S"),
            'last_run': None
        }
        
        self.controller.workflows = self.workflows  # Update controller's workflows
        print(f"Created workflow '{name}' with {len(commands)} commands")
        return True
        
    def update_workflow(self, name: str, commands: List[str]) -> bool:
        """Update an existing workflow"""
        if name not in self.workflows:
            print(f"Workflow '{name}' does not exist")
            return False
            
        self.workflows[name]['commands'] = commands
        self.workflows[name]['last_modified'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        self.controller.workflows = self.workflows  # Update controller's workflows
        print(f"Updated workflow '{name}'")
        return True
        
    def delete_workflow(self, name: str) -> bool:
        """Delete a workflow"""
        if name in self.workflows:
            del self.workflows[name]
            self.controller.workflows = self.workflows  # Update controller's workflows
            print(f"Deleted workflow '{name}'")
            return True
        else:
            print(f"Workflow '{name}' not found")
            return False
            
    def run_workflow(self, name: str) -> bool:
        """Run a saved workflow by name"""
        if name not in self.workflows:
            print(f"Workflow '{name}' not found")
            return False
            
        workflow = self.workflows[name]
        commands = workflow['commands']
        
        print(f"Running workflow '{name}' with {len(commands)} commands")
        
        # Update last run time
        self.workflows[name]['last_run'] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.controller.workflows = self.workflows  # Update controller's workflows
        
        try:
            self.controller.execute_command_sequence(commands)
            print(f"Workflow '{name}' completed successfully")
            return True
        except Exception as e:
            print(f"Error running workflow '{name}': {str(e)}")
            return False
            
    def get_workflow_list(self) -> List[str]:
        """Get a list of available workflow names"""
        return sorted(list(self.workflows.keys()))
        
    def get_workflow_details(self, name: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific workflow"""
        return self.workflows.get(name)
        
    def import_workflows(self, workflows_data: Dict[str, Any]) -> int:
        """Import workflows from external data source"""
        count = 0
        for name, workflow_data in workflows_data.items():
            if 'commands' in workflow_data and isinstance(workflow_data['commands'], list):
                self.workflows[name] = workflow_data
                count += 1
                
        self.controller.workflows = self.workflows  # Update controller's workflows
        return count 