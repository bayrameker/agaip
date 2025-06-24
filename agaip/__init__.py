"""
AGAIP - Super Power Agentic AI Framework

Endüstri standartlarında, optimize, asenkron, API odaklı ve çoklu dil entegrasyonuna
uygun agentic AI framework'ü.
"""

__version__ = "2.0.0"
__author__ = "Bayram Eker"
__email__ = "eker600@gmail.com"
__description__ = "Super Power Agentic AI Framework"

from agaip.agent_manager import AgentManager

# Agent system
from agaip.agents.agent import Agent

# API imports
from agaip.api.app import create_app

# Core imports
from agaip.core.application import AgaipApplication as Application
from agaip.core.container import Container
from agaip.core.events import EventBus
from agaip.core.exceptions import AgaipException

# Plugin system
from agaip.plugins.base import BasePlugin
from agaip.plugins.loader import PluginLoader

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "Application",
    "Container",
    "EventBus",
    "AgaipException",
    "create_app",
    "BasePlugin",
    "PluginLoader",
    "Agent",
    "AgentManager",
]
