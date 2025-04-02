"""
Behavior Tree implementation for USV mission planning.

This module provides a simple behavior tree implementation that can be
used for complex autonomous decision making.
"""

from enum import Enum
from typing import Callable, List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class BehaviorStatus(Enum):
    """Status values returned by behavior tree nodes."""
    SUCCESS = "SUCCESS"       # The node has completed successfully
    FAILURE = "FAILURE"       # The node has failed
    RUNNING = "RUNNING"       # The node is still running
    INVALID = "INVALID"       # The node is in an invalid state

class BehaviorNode:
    """
    Base class for all behavior tree nodes.
    
    Attributes:
        name: Name of the node for debugging
        status: Current status of the node
    """
    
    def __init__(self, name: str):
        """
        Initialize a behavior node.
        
        Args:
            name: Name of the node for identification
        """
        self.name = name
        self.status = BehaviorStatus.INVALID
    
    def tick(self, blackboard: Dict[str, Any]) -> BehaviorStatus:
        """
        Execute the node's logic and return a status.
        
        Args:
            blackboard: Shared data dictionary for nodes to use
            
        Returns:
            Status of the node after execution
        """
        # To be implemented by subclasses
        return BehaviorStatus.INVALID

class ActionNode(BehaviorNode):
    """
    Node that executes a specific action function.
    
    Attributes:
        action_func: Function to execute when ticked
    """
    
    def __init__(self, name: str, action_func: Callable[[Dict[str, Any]], BehaviorStatus]):
        """
        Initialize an action node.
        
        Args:
            name: Name of the node
            action_func: Function that implements the action logic
        """
        super().__init__(name)
        self.action_func = action_func
    
    def tick(self, blackboard: Dict[str, Any]) -> BehaviorStatus:
        """
        Execute the action function.
        
        Args:
            blackboard: Shared data dictionary
            
        Returns:
            Status returned by the action function
        """
        self.status = self.action_func(blackboard)
        return self.status

class ConditionNode(BehaviorNode):
    """
    Node that checks a condition.
    
    Attributes:
        condition_func: Function that evaluates a condition
    """
    
    def __init__(self, name: str, condition_func: Callable[[Dict[str, Any]], bool]):
        """
        Initialize a condition node.
        
        Args:
            name: Name of the node
            condition_func: Function that evaluates the condition
        """
        super().__init__(name)
        self.condition_func = condition_func
    
    def tick(self, blackboard: Dict[str, Any]) -> BehaviorStatus:
        """
        Evaluate the condition.
        
        Args:
            blackboard: Shared data dictionary
            
        Returns:
            SUCCESS if condition is true, FAILURE otherwise
        """
        if self.condition_func(blackboard):
            self.status = BehaviorStatus.SUCCESS
        else:
            self.status = BehaviorStatus.FAILURE
        
        return self.status

class SequenceNode(BehaviorNode):
    """
    Node that executes children in sequence until one fails.
    
    Attributes:
        children: List of child nodes to execute
        current_child_idx: Index of the child currently being executed
    """
    
    def __init__(self, name: str, children: List[BehaviorNode] = None):
        """
        Initialize a sequence node.
        
        Args:
            name: Name of the node
            children: List of child nodes to execute in sequence
        """
        super().__init__(name)
        self.children = children or []
        self.current_child_idx = 0
    
    def tick(self, blackboard: Dict[str, Any]) -> BehaviorStatus:
        """
        Execute children in sequence until one fails.
        
        Args:
            blackboard: Shared data dictionary
            
        Returns:
            FAILURE if any child fails, SUCCESS if all succeed, 
            RUNNING if still executing children
        """
        if not self.children:
            logger.warning(f"Sequence node '{self.name}' has no children")
            self.status = BehaviorStatus.FAILURE
            return self.status
        
        # Start or resume execution from current child
        while self.current_child_idx < len(self.children):
            # Tick current child
            child = self.children[self.current_child_idx]
            child_status = child.tick(blackboard)
            
            # Process result
            if child_status == BehaviorStatus.RUNNING:
                # Child is still running, return RUNNING
                self.status = BehaviorStatus.RUNNING
                return self.status
            
            elif child_status == BehaviorStatus.FAILURE:
                # Child failed, reset and return FAILURE
                self.current_child_idx = 0
                self.status = BehaviorStatus.FAILURE
                return self.status
            
            else:  # SUCCESS
                # Move to next child
                self.current_child_idx += 1
        
        # All children succeeded
        self.current_child_idx = 0
        self.status = BehaviorStatus.SUCCESS
        return self.status

class SelectorNode(BehaviorNode):
    """
    Node that executes children in sequence until one succeeds.
    
    Attributes:
        children: List of child nodes to try
        current_child_idx: Index of the child currently being executed
    """
    
    def __init__(self, name: str, children: List[BehaviorNode] = None):
        """
        Initialize a selector node.
        
        Args:
            name: Name of the node
            children: List of child nodes to try in sequence
        """
        super().__init__(name)
        self.children = children or []
        self.current_child_idx = 0
    
    def tick(self, blackboard: Dict[str, Any]) -> BehaviorStatus:
        """
        Execute children in sequence until one succeeds.
        
        Args:
            blackboard: Shared data dictionary
            
        Returns:
            SUCCESS if any child succeeds, FAILURE if all fail, 
            RUNNING if still executing children
        """
        if not self.children:
            logger.warning(f"Selector node '{self.name}' has no children")
            self.status = BehaviorStatus.FAILURE
            return self.status
        
        # Start or resume execution from current child
        while self.current_child_idx < len(self.children):
            # Tick current child
            child = self.children[self.current_child_idx]
            child_status = child.tick(blackboard)
            
            # Process result
            if child_status == BehaviorStatus.RUNNING:
                # Child is still running, return RUNNING
                self.status = BehaviorStatus.RUNNING
                return self.status
            
            elif child_status == BehaviorStatus.SUCCESS:
                # Child succeeded, reset and return SUCCESS
                self.current_child_idx = 0
                self.status = BehaviorStatus.SUCCESS
                return self.status
            
            else:  # FAILURE
                # Move to next child
                self.current_child_idx += 1
        
        # All children failed
        self.current_child_idx = 0
        self.status = BehaviorStatus.FAILURE
        return self.status

class ParallelNode(BehaviorNode):
    """
    Node that executes all children simultaneously.
    
    Attributes:
        children: List of child nodes to execute in parallel
        success_threshold: Minimum number of successful children required for success
    """
    
    def __init__(self, name: str, children: List[BehaviorNode] = None, success_threshold: int = None):
        """
        Initialize a parallel node.
        
        Args:
            name: Name of the node
            children: List of child nodes to execute in parallel
            success_threshold: Minimum number of successful children required for success
                               (defaults to all children)
        """
        super().__init__(name)
        self.children = children or []
        self.success_threshold = success_threshold if success_threshold is not None else len(self.children)
    
    def tick(self, blackboard: Dict[str, Any]) -> BehaviorStatus:
        """
        Execute all children in parallel.
        
        Args:
            blackboard: Shared data dictionary
            
        Returns:
            SUCCESS if enough children succeed, FAILURE if too many fail,
            RUNNING otherwise
        """
        if not self.children:
            logger.warning(f"Parallel node '{self.name}' has no children")
            self.status = BehaviorStatus.FAILURE
            return self.status
        
        # Execute all children
        success_count = 0
        running_count = 0
        
        for child in self.children:
            child_status = child.tick(blackboard)
            
            if child_status == BehaviorStatus.SUCCESS:
                success_count += 1
            elif child_status == BehaviorStatus.RUNNING:
                running_count += 1
        
        # Determine node status
        if success_count >= self.success_threshold:
            self.status = BehaviorStatus.SUCCESS
        elif running_count > 0:
            self.status = BehaviorStatus.RUNNING
        else:
            self.status = BehaviorStatus.FAILURE
        
        return self.status

class BehaviorTree:
    """
    A complete behavior tree.
    
    Attributes:
        root: Root node of the behavior tree
        blackboard: Shared data dictionary for nodes to use
    """
    
    def __init__(self, root: BehaviorNode):
        """
        Initialize the behavior tree.
        
        Args:
            root: Root node of the behavior tree
        """
        self.root = root
        self.blackboard = {}
        logger.info(f"Created behavior tree with root node '{root.name}'")
    
    def update(self, blackboard_updates: Dict[str, Any] = None) -> BehaviorStatus:
        """
        Update the behavior tree for one tick.
        
        Args:
            blackboard_updates: Updates to apply to the blackboard
            
        Returns:
            Status of the root node after execution
        """
        # Update blackboard if provided
        if blackboard_updates:
            self.blackboard.update(blackboard_updates)
        
        # Execute the root node
        status = self.root.tick(self.blackboard)
        return status
    
    def reset(self) -> None:
        """Reset the tree state for a fresh execution."""
        # Implement a recursive reset if needed
        # This is a simple implementation
        self.blackboard = {}
